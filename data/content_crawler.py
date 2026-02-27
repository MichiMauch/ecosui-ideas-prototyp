"""
Website Content Crawler.

Fetches and summarises the top-performing pages so that the Strategist agent
can avoid duplicates and suggest fresh angles on already-covered topics.

Uses only stdlib (html.parser) + requests (already in requirements.txt) –
no extra dependencies needed.
"""

import re
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

# Simple in-memory cache: url → result dict
_CACHE: dict[str, dict] = {}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ContentIdeaBot/1.0; +https://github.com)"
    ),
    "Accept-Language": "de,en;q=0.9",
}

_REQUEST_TIMEOUT = 8  # seconds per page


class _TextExtractor(HTMLParser):
    """Strips HTML tags and collects visible text."""

    SKIP_TAGS = {"script", "style", "nav", "footer", "header", "aside", "noscript"}

    def __init__(self):
        super().__init__()
        self._skip = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self.chunks.append(text)


def _extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(parser.chunks)


def _extract_title(html: str) -> str:
    """Extract <title> or first <h1>."""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return ""


def _extract_date(html: str) -> str:
    """Best-effort extraction of a publication date."""
    patterns = [
        r'<meta[^>]+(?:article:published_time|datePublished)[^>]+content=["\']([^"\']+)["\']',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"published"\s*:\s*"([^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            return m.group(1)[:10]  # return YYYY-MM-DD
    return ""


def _summarise(text: str, max_sentences: int = 4) -> str:
    """Return the first `max_sentences` sentences of the text."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:max_sentences])


def crawl_page(url: str) -> dict:
    """
    Fetch a single URL and return a summary dict.

    Returns:
        {url, title, summary, word_count, estimated_date}
    """
    if url in _CACHE:
        return _CACHE[url]

    result = {
        "url": url,
        "title": "",
        "summary": "",
        "word_count": 0,
        "estimated_date": "",
        "error": None,
    }

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text

        result["title"] = _extract_title(html)
        result["estimated_date"] = _extract_date(html)
        text = _extract_text(html)
        result["word_count"] = len(text.split())
        result["summary"] = _summarise(text)

    except Exception as exc:
        result["error"] = str(exc)

    _CACHE[url] = result
    return result


def crawl_top_pages(
    ga4_pages: list[dict],
    base_url: str,
    limit: int = 10,
) -> list[dict]:
    """
    Crawl the top `limit` pages from GA4 results.

    Args:
        ga4_pages:  List of dicts with keys page_path, page_title, page_views.
        base_url:   Root URL of the website, e.g. "https://example.com".
        limit:      Maximum number of pages to crawl.

    Returns:
        List of crawl result dicts (see crawl_page()).
    """
    if not base_url:
        return []

    # Normalise base_url
    parsed = urlparse(base_url)
    root = f"{parsed.scheme}://{parsed.netloc}"

    results = []
    for page in ga4_pages[:limit]:
        path = page.get("page_path", "")
        if not path or path in ("/", ""):
            continue
        url = urljoin(root, path)
        data = crawl_page(url)
        # Enrich with GA4 metadata
        data["page_views"] = page.get("page_views", 0)
        data["engagement_rate"] = page.get("engagement_rate", 0)
        results.append(data)
        time.sleep(0.3)  # polite crawl delay

    return results


def format_crawl_summaries(crawled: list[dict]) -> str:
    """
    Format crawled pages into a concise text block for agent prompts.
    """
    if not crawled:
        return "Keine bestehenden Seiten gecrawlt."

    lines = []
    for page in crawled:
        if page.get("error"):
            continue
        title = page.get("title") or page.get("url", "")
        url = page.get("url", "")
        summary = page.get("summary", "")
        word_count = page.get("word_count", 0)
        date = page.get("estimated_date", "")
        views = page.get("page_views", 0)

        date_str = f" · {date}" if date else ""
        lines.append(
            f"- **{title}** ({url}){date_str} — {word_count} Wörter, {views} Aufrufe\n"
            f"  Zusammenfassung: {summary[:200]}"
        )

    if not lines:
        return "Keine gecrawlten Seiten verfügbar."

    return "\n\n".join(lines)
