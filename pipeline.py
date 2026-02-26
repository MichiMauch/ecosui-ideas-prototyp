"""
Pipeline orchestrator.

Runs all 4 agents in sequence, fetching data sources in parallel first.
Returns the final list of content ideas.
"""

import concurrent.futures
import os
import time
from dataclasses import dataclass, field
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

import agents.analyst as analyst_agent
import agents.trend_scout as trend_scout_agent
import agents.strategist as strategist_agent
import agents.editor as editor_agent
from data.google_analytics import fetch_top_pages
from data.rss_reader import fetch_rss_articles
from data.search_console import fetch_top_queries
from config import ANALYTICS_DAYS_BACK

load_dotenv()


@dataclass
class PipelineResult:
    ideas: list[dict] = field(default_factory=list)
    analyst_output: str = ""
    trend_scout_output: str = ""
    strategist_output: str = ""
    errors: list[str] = field(default_factory=list)
    # Raw source data — forwarded to content_pipeline
    ga4_pages: list[dict] = field(default_factory=list)
    gsc_queries: list[dict] = field(default_factory=list)
    rss_articles: list[dict] = field(default_factory=list)
    fetched_at: datetime | None = None


def run(status_callback=None, token_callback=None) -> PipelineResult:
    """
    Execute the full multi-agent content idea pipeline.

    status_callback(step: str) is called before each major step
    so the UI can show progress.

    token_callback(phase: str, accumulated_text: str) is called on each
    streaming token for text-generating agents.
    """

    def status(msg: str):
        if status_callback:
            status_callback(msg)

    def make_token_cb(phase: str):
        if token_callback:
            return lambda text: token_callback(phase, text)
        return None

    result = PipelineResult()

    # --- Config from env ---
    api_key = os.getenv("OPENAI_API_KEY")
    property_id = os.getenv("GA4_PROPERTY_ID")
    site_url = os.getenv("GSC_SITE_URL")
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    if not api_key:
        result.errors.append("OPENAI_API_KEY fehlt in der .env-Datei.")
        return result

    client = OpenAI(api_key=api_key)

    # --- Step 1: Fetch all data sources in parallel ---
    status("Daten werden geladen (GA4, Search Console, RSS)...")

    ga4_pages = []
    gsc_queries = []
    rss_articles = []

    has_credentials = (
        os.path.exists(credentials_file)
        or bool(os.getenv("GOOGLE_CREDENTIALS_JSON"))
        or credentials_file.strip().startswith("{")
    )

    def fetch_ga4():
        if not property_id or not has_credentials:
            return []
        return fetch_top_pages(property_id, credentials_file, days_back=ANALYTICS_DAYS_BACK)

    def fetch_gsc():
        if not site_url or not has_credentials:
            return []
        return fetch_top_queries(site_url, credentials_file, days_back=ANALYTICS_DAYS_BACK)

    def fetch_rss():
        return fetch_rss_articles()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_ga4 = executor.submit(fetch_ga4)
        future_gsc = executor.submit(fetch_gsc)
        future_rss = executor.submit(fetch_rss)

        deadline = time.monotonic() + 30
        for future, label, target_list in [
            (future_ga4, "GA4", "ga4"),
            (future_gsc, "GSC", "gsc"),
            (future_rss, "RSS", "rss"),
        ]:
            remaining = max(0.1, deadline - time.monotonic())
            try:
                data = future.result(timeout=remaining)
                if label == "GA4":
                    ga4_pages = data
                elif label == "GSC":
                    gsc_queries = data
                else:
                    rss_articles = data
            except Exception as e:
                result.errors.append(f"{label}-Fehler: {e}")

    result.ga4_pages = ga4_pages
    result.gsc_queries = gsc_queries
    result.rss_articles = rss_articles
    result.fetched_at = datetime.now()

    # --- Step 2: Agent 1 – Analyst ---
    status("Agent 1/4: Analyst wertet GA4 & Search Console aus...")
    try:
        result.analyst_output = analyst_agent.run(
            client, ga4_pages, gsc_queries,
            token_callback=make_token_cb("analyst"),
        )
    except Exception as e:
        result.errors.append(f"Analyst-Agent Fehler: {e}")
        result.analyst_output = "Keine Analyse verfügbar."

    # --- Step 3: Agent 2 – Trend Scout ---
    status("Agent 2/4: Trend-Scout analysiert RSS-Feeds...")
    try:
        result.trend_scout_output = trend_scout_agent.run(
            client, rss_articles,
            token_callback=make_token_cb("trend_scout"),
        )
    except Exception as e:
        result.errors.append(f"Trend-Scout-Agent Fehler: {e}")
        result.trend_scout_output = "Keine Trend-Analyse verfügbar."

    # --- Step 4: Agent 3 – Strategist ---
    status("Agent 3/4: Stratege kombiniert Erkenntnisse zu Ideen...")
    try:
        result.strategist_output = strategist_agent.run(
            client, result.analyst_output, result.trend_scout_output,
            token_callback=make_token_cb("strategist"),
        )
    except Exception as e:
        result.errors.append(f"Strategen-Agent Fehler: {e}")
        result.strategist_output = "Keine Strategie verfügbar."

    # --- Step 5: Agent 4 – Editor ---
    status("Agent 4/4: Redakteur verfeinert Titel & Begründungen...")
    try:
        result.ideas = editor_agent.run(client, result.strategist_output, rss_articles)
    except Exception as e:
        result.errors.append(f"Redakteur-Agent Fehler: {e}")

    status("Fertig!")
    return result
