"""
Agent 1: Der Analyst

Analysiert GA4-Daten (Top-Seiten, Engagement) und GSC-Daten (Keywords, Impressions, CTR).
Identifiziert:
  - Welche Themen performen gut (viele Views, hohes Engagement)
  - Welche Keywords viele Impressions aber niedrige CTR haben (Content-Lücken)
  - Welche Themenfelder besonders relevant sind
"""

import json
from openai import OpenAI
from config import OPENAI_MODEL


def run(
    client: OpenAI,
    ga4_pages: list[dict],
    gsc_queries: list[dict],
    token_callback=None,
) -> str:
    """
    Analyse GA4 and GSC data and return a structured text summary of findings.
    """

    ga4_text = _format_ga4(ga4_pages)
    gsc_text = _format_gsc(gsc_queries)

    prompt = f"""Du bist ein datengetriebener Content-Analyst für ein deutschsprachiges Wirtschaftsmedium.

Analysiere die folgenden Daten aus Google Analytics 4 (GA4) und Google Search Console (GSC) der letzten 7 Tage.

**GA4 – Top-Seiten nach Seitenaufrufen:**
{ga4_text}

**GSC – Top-Suchanfragen nach Impressionen:**
{gsc_text}

Deine Aufgabe:
1. Identifiziere 3-5 Themenfelder, die aktuell sehr gut performen (hohe Views + gutes Engagement).
2. Identifiziere 3-5 Content-Lücken: Keywords mit vielen Impressionen, aber niedriger CTR (< 3%) oder noch kein passendes Dokument.
3. Erkenne übergreifende Trends oder Muster in den Suchanfragen.
4. Fasse deine Erkenntnisse klar und strukturiert zusammen – diese werden direkt an den nächsten Agenten weitergegeben.

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
