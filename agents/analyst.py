"""
Agent 1: Der Analyst

Analysiert GA4-Daten (Top-Seiten, Engagement) und GSC-Daten (Keywords, Impressions, CTR).
Identifiziert:
  - Welche Themen performen gut (viele Views, hohes Engagement)
  - Welche Keywords viele Impressions aber niedrige CTR haben (Content-Lücken)
  - Welche Seiten auf Position 4–15 ranken ("Fast-Ranker") → Update-Kandidaten
  - Welche Themen dauerhaft relevant sind (90-Tage-Vergleich vs. 7-Tage)
"""

import json
from openai import OpenAI
from config import OPENAI_MODEL


def run(
    client: OpenAI,
    ga4_pages: list[dict],
    gsc_queries: list[dict],
    gsc_pages: list[dict] | None = None,
    ga4_pages_long: list[dict] | None = None,
    gsc_queries_long: list[dict] | None = None,
    trends_data: list[dict] | None = None,
    token_callback=None,
) -> str:
    """
    Analyse GA4 and GSC data and return a structured text summary of findings.

    Args:
        gsc_pages:        Page-level GSC data (position per page).
        ga4_pages_long:   GA4 top pages over 90 days for evergreen detection.
        gsc_queries_long: GSC top queries over 90 days for evergreen detection.
        trends_data:      Google Trends trending keywords for Switzerland.
    """

    ga4_text = _format_ga4(ga4_pages)
    gsc_text = _format_gsc(gsc_queries)
    gsc_pages_text = _format_gsc_pages(gsc_pages or [])
    long_period_text = _format_long_period(ga4_pages_long or [], gsc_queries_long or [])
    trends_text = _format_trends(trends_data or [])

    prompt = f"""Du bist ein datengetriebener Content-Analyst für ein deutschsprachiges Wirtschaftsmedium.

Analysiere die folgenden Daten aus Google Analytics 4 (GA4) und Google Search Console (GSC).

**GA4 – Top-Seiten nach Seitenaufrufen (letzte 7 Tage):**
{ga4_text}

**GSC – Top-Suchanfragen nach Impressionen (letzte 7 Tage):**
{gsc_text}

**GSC – Seitenränge nach Position (letzte 7 Tage):**
{gsc_pages_text}

**Langzeit-Vergleich (letzte 90 Tage):**
{long_period_text}

**Google Trends – Trendende Suchen in der Schweiz (heute):**
{trends_text}

Deine Aufgabe:
1. Identifiziere 3-5 Themenfelder, die aktuell sehr gut performen (hohe Views + gutes Engagement).
2. Identifiziere 3-5 Content-Lücken: Keywords mit vielen Impressionen, aber niedriger CTR (< 3%) oder noch kein passendes Dokument.
3. Identifiziere "Fast-Ranker": Seiten auf Position 4–15, die mit einem Content-Update auf Platz 1–3 klettern könnten.
4. Erkenne Evergreen-Themen (konstant gut über 90 Tage) vs. Kurzfrist-Trends (nur letzte 7 Tage stark).
5. Erkenne übergreifende Trends oder Muster in den Suchanfragen.
6. Gleiche trendende Google-Keywords mit den GSC-Daten ab: Wo gibt es Momentum-Themen, bei denen wir bereits ranken oder eine Content-Lücke besteht?
7. Fasse deine Erkenntnisse klar und strukturiert zusammen – diese werden direkt an den nächsten Agenten weitergegeben.

Antworte auf Deutsch. Strukturiere deine Antwort mit klaren Abschnitten."""

    if token_callback:
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            stream=True,
        )
        full_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_text += delta
            token_callback(full_text)
        return full_text
    else:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content


def _format_ga4(pages: list[dict]) -> str:
    if not pages:
        return "Keine GA4-Daten verfügbar."
    lines = ["Titel | Aufrufe | Engagement-Rate"]
    lines.append("------|---------|----------------")
    for p in pages[:15]:
        lines.append(f"{p['page_title'][:80]} | {p['page_views']} | {p['engagement_rate']}%")
    return "\n".join(lines)


def _format_gsc(queries: list[dict]) -> str:
    if not queries:
        return "Keine GSC-Daten verfügbar."
    lines = ["Suchanfrage | Impressionen | Klicks | CTR | Position"]
    lines.append("-----------|--------------|--------|-----|----------")
    for q in queries[:20]:
        lines.append(
            f"{q['query'][:60]} | {q['impressions']} | {q['clicks']} | {q['ctr']}% | {q['position']}"
        )
    return "\n".join(lines)


def _format_gsc_pages(pages: list[dict]) -> str:
    if not pages:
        return "Keine seitenspezifischen GSC-Daten verfügbar."
    lines = ["URL | Impressionen | Klicks | CTR | Position | Status"]
    lines.append("----|--------------|--------|-----|----------|-------")
    for p in pages[:20]:
        pos = p["position"]
        status = "Fast-Ranker ⚡" if 4 <= pos <= 15 else ("Top 3 ✅" if pos < 4 else "Weit hinten")
        lines.append(
            f"{p['page'][:70]} | {p['impressions']} | {p['clicks']} | {p['ctr']}% | {pos} | {status}"
        )
    return "\n".join(lines)


def _format_trends(trends: list[dict]) -> str:
    if not trends:
        return "Keine Google-Trends-Daten verfügbar."
    lines = ["Trend-Index (0–100) | Keyword", "--------------------|--------"]
    for t in trends:
        lines.append(f"{t['value']:<20}| {t['keyword']}")
    return "\n".join(lines)


def _format_long_period(ga4_long: list[dict], gsc_long: list[dict]) -> str:
    if not ga4_long and not gsc_long:
        return "Keine Langzeit-Daten verfügbar."
    parts = []
    if ga4_long:
        lines = ["Top-Seiten (90 Tage) | Aufrufe"]
        lines.append("---------------------|--------")
        for p in ga4_long[:10]:
            lines.append(f"{p['page_title'][:60]} | {p['page_views']}")
        parts.append("\n".join(lines))
    if gsc_long:
        lines = ["Top-Suchanfragen (90 Tage) | Impressionen | Position"]
        lines.append("--------------------------|--------------|----------")
        for q in gsc_long[:10]:
            lines.append(f"{q['query'][:50]} | {q['impressions']} | {q['position']}")
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
