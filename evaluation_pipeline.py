"""
Evaluation pipeline orchestrator.

Runs the 2-agent evaluation flow for a user-submitted idea:
  1. idea_context  → Finds relevant RSS/GA4/GSC signals
  2. idea_evaluator → Returns verdict, score, pros/cons, recommendation

Data strategy:
  - If rss_articles/ga4_pages/gsc_queries are passed (from a prior pipeline run),
    they are used directly (no extra API call).
  - If rss_articles is None, fresh RSS data is fetched.
  - GA4/GSC are left empty when not provided (no credentials required).
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from openai import OpenAI

import agents.idea_context as idea_context_agent
import agents.idea_evaluator as idea_evaluator_agent
from data.rss_reader import fetch_rss_articles, fetch_google_news_articles

load_dotenv()


@dataclass
class EvaluationResult:
    verdict: str = ""               # "Empfohlen" | "Mit Vorbehalt" | "Nicht empfohlen"
    score: int = 0                  # 0–100
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    recommendation: str = ""
    context_notes: str = ""         # Raw text from idea_context agent (for show_details)
    errors: list[str] = field(default_factory=list)


def run(
    idea_title: str,
    idea_desc: str = "",
    rss_articles: list[dict] | None = None,
    ga4_pages: list[dict] | None = None,
    gsc_queries: list[dict] | None = None,
    status_callback=None,
) -> EvaluationResult:
    """
    Evaluate a user-submitted article idea.

    Args:
        idea_title:      The idea title entered by the user.
        idea_desc:       Optional description / context from the user.
        rss_articles:    Pre-fetched RSS articles. If None, fetched fresh.
        ga4_pages:       Pre-fetched GA4 pages. If None, left empty.
        gsc_queries:     Pre-fetched GSC queries. If None, left empty.
        status_callback: Called with a status string at each step.

    Returns:
        EvaluationResult with verdict, score, pros, cons, recommendation,
        context_notes (raw agent output), and any errors.
    """

    def status(msg: str):
        if status_callback:
            status_callback(msg)

    result = EvaluationResult()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        result.errors.append("OPENAI_API_KEY fehlt in der .env-Datei.")
        return result

    client = OpenAI(api_key=api_key)

    # --- Step 1: Fetch RSS if not provided ---
    if rss_articles is None:
        status("RSS-Feeds werden geladen...")
        try:
            rss_articles = fetch_rss_articles()
        except Exception as e:
            result.errors.append(f"RSS-Fehler: {e}")
            rss_articles = []

    ga4_pages = ga4_pages or []
    gsc_queries = gsc_queries or []

    # --- Step 1b: Google News dynamisch nach Ideen-Titel durchsuchen ---
    status("Google News wird durchsucht...")
    try:
        gn_articles = fetch_google_news_articles(idea_title)
        existing_urls = {a["url"] for a in rss_articles}
        for a in gn_articles:
            if a["url"] not in existing_urls:
                rss_articles.append(a)
                existing_urls.add(a["url"])
    except Exception as e:
        result.errors.append(f"Google News Fehler: {e}")

    # --- Step 2: Agent 1 – Kontext-Agent ---
    status("Kontext-Agent sucht relevante Signale...")
    try:
        result.context_notes = idea_context_agent.run(
            client=client,
            idea_title=idea_title,
            idea_desc=idea_desc,
            rss_articles=rss_articles,
            ga4_pages=ga4_pages,
            gsc_queries=gsc_queries,
        )
    except Exception as e:
        result.errors.append(f"Kontext-Agent Fehler: {e}")
        result.context_notes = "Keine Kontextdaten verfügbar."

    # --- Step 3: Agent 2 – Bewertungs-Agent ---
    status("Idee wird bewertet...")
    try:
        evaluation = idea_evaluator_agent.run(
            client=client,
            idea_title=idea_title,
            idea_desc=idea_desc,
            context=result.context_notes,
        )
        result.verdict = evaluation.get("verdict", "")
        result.score = evaluation.get("score", 0)
        result.pros = evaluation.get("pros", [])
        result.cons = evaluation.get("cons", [])
        result.recommendation = evaluation.get("recommendation", "")
    except Exception as e:
        result.errors.append(f"Bewertungs-Agent Fehler: {e}")

    return result
