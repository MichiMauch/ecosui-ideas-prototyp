"""
Pipeline orchestrator.

Runs all 4 agents in sequence, fetching data sources in parallel first.
Returns the final list of content ideas.

New in this version:
  - Crawls top GA4 pages to give the Strategist existing-content context
  - Fetches GSC page-level positions (Fast-Ranker detection)
  - Fetches 90-day GA4 + GSC data alongside the 7-day data
  - Persists generated ideas to data/ideas_history.json
"""

import concurrent.futures
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

import agents.analyst as analyst_agent
import agents.trend_scout as trend_scout_agent
import agents.strategist as strategist_agent
import agents.editor as editor_agent
from data.google_analytics import fetch_top_pages
from data.rss_reader import fetch_rss_articles
from data.search_console import fetch_top_queries, fetch_top_pages_by_position
from data.content_crawler import crawl_top_pages, format_crawl_summaries
from data.google_trends import fetch_trending_topics
from config import ANALYTICS_DAYS_BACK, ANALYTICS_DAYS_LONG, CRAWL_TOP_PAGES, TRENDS_GEO, TRENDS_LIMIT
import seo_potential as seo_potential_module

load_dotenv()

_HISTORY_FILE = Path(__file__).parent / "data" / "ideas_history.json"


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
    # New: page-level GSC positions
    gsc_pages: list[dict] = field(default_factory=list)
    # New: 90-day data
    ga4_pages_long: list[dict] = field(default_factory=list)
    gsc_queries_long: list[dict] = field(default_factory=list)
    # New: crawled existing content
    crawled_pages: list[dict] = field(default_factory=list)
    # New: Google Trends data
    trends_data: list[dict] = field(default_factory=list)
    # New: SEO traffic potential
    seo_potential: dict = field(default_factory=dict)
    fetched_at: datetime | None = None


def _save_ideas_history(ideas: list[dict]) -> None:
    """Append the generated ideas to the local JSON history file."""
    try:
        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history: list[dict] = []
        if _HISTORY_FILE.exists():
            try:
                history = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                history = []
        entry = {
            "generated_at": datetime.now().isoformat(),
            "ideas": ideas,
        }
        history.append(entry)
        # Keep last 30 runs
        history = history[-30:]
        _HISTORY_FILE.write_text(
            json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception:
        pass  # History is non-critical


def load_ideas_history() -> list[dict]:
    """Load persisted idea runs. Returns list of {generated_at, ideas} dicts."""
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


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

    has_credentials = (
        os.path.exists(credentials_file)
        or bool(os.getenv("GOOGLE_CREDENTIALS_JSON"))
        or credentials_file.strip().startswith("{")
    )

    # --- Step 1: Fetch all data sources in parallel ---
    status("Daten werden geladen (GA4, Search Console, RSS)...")

    ga4_pages: list[dict] = []
    gsc_queries: list[dict] = []
    rss_articles: list[dict] = []
    gsc_pages: list[dict] = []
    ga4_pages_long: list[dict] = []
    gsc_queries_long: list[dict] = []
    trends_data: list[dict] = []

    def fetch_ga4():
        if not property_id or not has_credentials:
            return []
        return fetch_top_pages(property_id, credentials_file, days_back=ANALYTICS_DAYS_BACK)

    def fetch_ga4_long():
        if not property_id or not has_credentials:
            return []
        return fetch_top_pages(property_id, credentials_file, days_back=ANALYTICS_DAYS_LONG)

    def fetch_gsc():
        if not site_url or not has_credentials:
            return []
        return fetch_top_queries(site_url, credentials_file, days_back=ANALYTICS_DAYS_BACK)

    def fetch_gsc_long():
        if not site_url or not has_credentials:
            return []
        return fetch_top_queries(site_url, credentials_file, days_back=ANALYTICS_DAYS_LONG)

    def fetch_gsc_pages():
        if not site_url or not has_credentials:
            return []
        return fetch_top_pages_by_position(
            site_url, credentials_file, days_back=ANALYTICS_DAYS_BACK, limit=25
        )

    def fetch_rss():
        return fetch_rss_articles()

    def fetch_trends():
        return fetch_trending_topics(geo=TRENDS_GEO, limit=TRENDS_LIMIT)

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        future_ga4 = executor.submit(fetch_ga4)
        future_ga4_long = executor.submit(fetch_ga4_long)
        future_gsc = executor.submit(fetch_gsc)
        future_gsc_long = executor.submit(fetch_gsc_long)
        future_gsc_pages = executor.submit(fetch_gsc_pages)
        future_rss = executor.submit(fetch_rss)
        future_trends = executor.submit(fetch_trends)

        deadline = time.monotonic() + 45  # extended timeout for 7 fetches
        fetch_map = [
            (future_ga4, "GA4"),
            (future_ga4_long, "GA4-90T"),
            (future_gsc, "GSC"),
            (future_gsc_long, "GSC-90T"),
            (future_gsc_pages, "GSC-Pages"),
            (future_rss, "RSS"),
            (future_trends, "Trends"),
        ]
        for future, label in fetch_map:
            remaining = max(0.1, deadline - time.monotonic())
            try:
                data = future.result(timeout=remaining)
                if label == "GA4":
                    ga4_pages = data
                elif label == "GA4-90T":
                    ga4_pages_long = data
                elif label == "GSC":
                    gsc_queries = data
                elif label == "GSC-90T":
                    gsc_queries_long = data
                elif label == "GSC-Pages":
                    gsc_pages = data
                elif label == "RSS":
                    rss_articles = data
                else:
                    trends_data = data
            except Exception as e:
                result.errors.append(f"{label}-Fehler: {e}")

    result.ga4_pages = ga4_pages
    result.gsc_queries = gsc_queries
    result.rss_articles = rss_articles
    result.gsc_pages = gsc_pages
    result.ga4_pages_long = ga4_pages_long
    result.gsc_queries_long = gsc_queries_long
    result.trends_data = trends_data
    result.fetched_at = datetime.now()

    # --- Calculate SEO traffic potential ---
    try:
        result.seo_potential = seo_potential_module.calculate_seo_potential(
            gsc_pages, gsc_queries
        )
    except Exception as e:
        result.errors.append(f"SEO-Potenzial-Fehler: {e}")

    # --- Step 2: Crawl top pages for existing-content context ---
    status("Bestehende Top-Seiten werden analysiert (Website-Crawler)...")
    crawled_pages: list[dict] = []
    if ga4_pages and site_url:
        try:
            crawled_pages = crawl_top_pages(
                ga4_pages, base_url=site_url, limit=CRAWL_TOP_PAGES
            )
        except Exception as e:
            result.errors.append(f"Crawler-Fehler: {e}")
    result.crawled_pages = crawled_pages

    # --- Step 3: Agent 1 – Analyst ---
    status("Agent 1/4: Analyst wertet GA4 & Search Console aus...")
    try:
        result.analyst_output = analyst_agent.run(
            client, ga4_pages, gsc_queries,
            gsc_pages=gsc_pages,
            ga4_pages_long=ga4_pages_long,
            gsc_queries_long=gsc_queries_long,
            trends_data=trends_data,
            token_callback=make_token_cb("analyst"),
        )
    except Exception as e:
        result.errors.append(f"Analyst-Agent Fehler: {e}")
        result.analyst_output = "Keine Analyse verfügbar."

    # --- Step 4: Agent 2 – Trend Scout ---
    status("Agent 2/4: Trend-Scout analysiert RSS-Feeds...")
    try:
        result.trend_scout_output = trend_scout_agent.run(
            client, rss_articles,
            token_callback=make_token_cb("trend_scout"),
        )
    except Exception as e:
        result.errors.append(f"Trend-Scout-Agent Fehler: {e}")
        result.trend_scout_output = "Keine Trend-Analyse verfügbar."

    # --- Step 5: Agent 3 – Strategist ---
    status("Agent 3/4: Stratege kombiniert Erkenntnisse zu Ideen...")
    try:
        crawl_summaries = format_crawl_summaries(crawled_pages)
        result.strategist_output = strategist_agent.run(
            client, result.analyst_output, result.trend_scout_output,
            crawl_summaries=crawl_summaries,
            token_callback=make_token_cb("strategist"),
        )
    except Exception as e:
        result.errors.append(f"Strategen-Agent Fehler: {e}")
        result.strategist_output = "Keine Strategie verfügbar."

    # --- Step 6: Agent 4 – Editor ---
    status("Agent 4/4: Redakteur verfeinert Titel & Begründungen...")
    try:
        result.ideas = editor_agent.run(client, result.strategist_output, rss_articles)
    except Exception as e:
        result.errors.append(f"Redakteur-Agent Fehler: {e}")

    # --- Step 7: Persist ideas to history ---
    if result.ideas:
        _save_ideas_history(result.ideas)

    status("Fertig!")
    return result
