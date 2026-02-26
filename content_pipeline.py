"""
Content Pipeline Orchestrator

Turns a single content idea into a fully written, fact-checked and evaluated
article using a 4-agent chain:

    Researcher → Writer → Fact-Checker → Evaluator
                   ▲           │              │
                   └───────────┘       score < 80?
                   (max 2 loops)             │ no
                                             ▼
                                       ContentResult
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI

import agents.researcher as researcher_agent
import agents.writer as writer_agent
import agents.fact_checker as fact_checker_agent
import agents.evaluator as evaluator_agent
import agents.social_writer as social_writer_agent
from config import (
    BRAND_VOICE,
    FORBIDDEN_PHRASES,
    ARTICLE_TARGET_WORDS,
    MAX_REVISION_LOOPS,
)

load_dotenv()


@dataclass
class ContentResult:
    article: dict = field(default_factory=dict)
    evaluation: dict = field(default_factory=dict)
    research_notes: str = ""
    revision_count: int = 0
    social_snippets: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def run(
    idea: dict,
    rss_articles: list[dict],
    gsc_queries: list[dict],
    status_callback=None,
    target_words: int | None = None,
) -> ContentResult:
    """
    Execute the full article-creation pipeline for a single idea.

    Args:
        idea:            Idea dict with keys: title, why_now, category
        rss_articles:    Raw RSS articles from the data pipeline
        gsc_queries:     Raw GSC queries from the data pipeline
        status_callback: Optional callable(msg: str) for progress updates
        target_words:    Target word count (overrides config default)

    Returns:
        ContentResult with finished article, evaluation scores, and metadata
    """

    def status(msg: str):
        if status_callback:
            status_callback(msg)

    result = ContentResult()
    words = target_words or ARTICLE_TARGET_WORDS

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        result.errors.append("OPENAI_API_KEY fehlt in der .env-Datei.")
        return result

    client = OpenAI(api_key=api_key)

    # ── Step 1: Researcher ────────────────────────────────────────────────────
    status("Researcher: Fakten und Quellen werden analysiert...")
    try:
        result.research_notes = researcher_agent.run(
            client, idea, rss_articles, gsc_queries
        )
    except Exception as e:
        result.errors.append(f"Researcher-Fehler: {e}")
        result.research_notes = "Keine Research-Notes verfügbar."

    # ── Revision Loop: Writer → Fact-Checker → Evaluator ─────────────────────
    revision_feedback: str | None = None
    max_passes = MAX_REVISION_LOOPS + 1  # initial draft + up to 2 revisions

    for pass_num in range(max_passes):
        loop_label = f"Durchlauf {pass_num + 1}/{max_passes}"

        # Writer
        if pass_num == 0:
            status(f"Writer: Artikel wird verfasst ({loop_label})...")
        else:
            status(f"Writer: Artikel wird überarbeitet ({loop_label})...")
        try:
            article = writer_agent.run(
                client,
                idea,
                result.research_notes,
                BRAND_VOICE,
                FORBIDDEN_PHRASES,
                target_words=words,
                revision_feedback=revision_feedback,
            )
        except Exception as e:
            result.errors.append(f"Writer-Fehler ({loop_label}): {e}")
            break

        # Fact-Checker
        status(f"Fact-Checker: Behauptungen werden geprüft ({loop_label})...")
        try:
            article = fact_checker_agent.run(client, article, result.research_notes)
        except Exception as e:
            result.errors.append(f"Fact-Checker-Fehler ({loop_label}): {e}")
            # Continue with unchecked article rather than aborting

        # Evaluator
        status(f"Evaluator: Artikel wird bewertet ({loop_label})...")
        try:
            evaluation = evaluator_agent.run(client, article, idea)
        except Exception as e:
            result.errors.append(f"Evaluator-Fehler ({loop_label}): {e}")
            evaluation = {
                "scores": {},
                "overall": 0,
                "passed": False,
                "feedback": "",
            }

        result.article = article
        result.evaluation = evaluation
        result.revision_count = pass_num

        if evaluation.get("passed", False):
            break

        # Not passed and more loops available → feed back into Writer
        revision_feedback = evaluation.get("feedback", "")
        if not revision_feedback:
            # No actionable feedback — stop looping
            break

    # ── Social Media Snippets ─────────────────────────────────────────────────
    if result.evaluation.get("passed", False) and result.article:
        status("Social Media Snippets werden erstellt...")
        try:
            result.social_snippets = social_writer_agent.run(
                client, result.article, idea.get("title", "")
            )
        except Exception as e:
            result.errors.append(f"Social-Writer-Fehler: {e}")

    status("Fertig!")
    return result
