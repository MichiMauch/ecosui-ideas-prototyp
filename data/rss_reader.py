"""
RSS feed reader.

Fetches recent articles from configured news feeds.
Uses certifi to fix SSL certificate issues on macOS.
"""

import ssl
import urllib.request
import certifi
import feedparser
from datetime import datetime, timezone
from config import RSS_FEEDS, RSS_MAX_ITEMS_PER_FEED


def _fetch_feed_raw(url: str) -> bytes:
    """Fetch feed URL using certifi SSL context."""
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 feedparser"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return resp.read()


def fetch_rss_articles(feeds: list[dict] | None = None, max_per_feed: int = RSS_MAX_ITEMS_PER_FEED) -> list[dict]:
    """
    Fetch recent articles from all configured RSS feeds.

    Returns a list of dicts with keys:
        source, title, summary, published, url
    """
    if feeds is None:
        feeds = RSS_FEEDS

    articles = []

    for feed_config in feeds:
        try:
            raw = _fetch_feed_raw(feed_config["url"])
            feed = feedparser.parse(raw)
            for entry in feed.entries[:max_per_feed]:
                published = _parse_date(entry)
                articles.append(
                    {
                        "source": feed_config["name"],
                        "title": entry.get("title", "").strip(),
                        "summary": _clean_summary(entry.get("summary", "")),
                        "published": published,
                        "url": entry.get("link", ""),
                    }
                )
        except Exception as e:
            # Log but don't inject error messages as articles into the LLM prompt
            print(f"[rss_reader] Feed '{feed_config['name']}' konnte nicht geladen werden: {e}")

    # Sort by publication date, newest first
    articles.sort(
        key=lambda a: a["published"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return articles


def _parse_date(entry) -> datetime | None:
    """Try to parse the publication date from an RSS entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def _clean_summary(text: str) -> str:
    """Strip HTML tags from a summary string."""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()[:500]
