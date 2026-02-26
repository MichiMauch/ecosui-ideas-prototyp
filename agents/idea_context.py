"""
Kontext-Agent: Sucht relevante Signale (RSS, GA4, GSC) zur User-Idee.

Gibt einen strukturierten Markdown-Text zurück, der beschreibt, welche
vorhandenen Daten zur eingereichten Idee passen.
"""

from openai import OpenAI
from config import OPENAI_MODEL


def run(
    client: OpenAI,
    idea_title: str,
    idea_desc: str,
    rss_articles: list[dict],
    ga4_pages: list[dict],
    gsc_queries: list[dict],
) -> str:
    """
    Sucht relevante Datenpunkte aus RSS, GA4 und GSC zur eingereichten Idee.

    Returns:
        Strukturierter Markdown-Text mit relevanten Signalen.
    """
    rss_text = _format_rss(rss_articles)
    ga4_text = _format_ga4(ga4_pages)
    gsc_text = _format_gsc(gsc_queries)

    desc_section = f"\n**Beschreibung:** {idea_desc.strip()}" if idea_desc.strip() else ""

    prompt = f"""Du bist ein Daten-Rechercheur für ein deutschsprachiges Wirtschaftsmedium.

Ein Redakteur hat folgende Artikel-Idee eingereicht:

**Ideen-Titel:** {idea_title}{desc_section}

Deine Aufgabe: Durchsuche die folgenden Datenpunkte und identifiziere, welche davon zur Idee passen.

---

**RSS-Artikel (aktuelle Nachrichten):**
{rss_text}

---

**GA4 – Top-Seiten (letzte 7 Tage):**
{ga4_text}

---

**GSC – Top-Suchanfragen (letzte 7 Tage):**
{gsc_text}

---

Erstelle einen strukturierten Bericht mit diesen Abschnitten:

## Relevante RSS-Artikel
Liste max. 5 passende Artikel auf (Quelle, Titel, kurze Relevanz-Erklärung).
Falls keine RSS-Artikel relevant sind, schreibe "Kein direkter Nachrichtenanlass gefunden."

## GA4-Signale
Welche bestehenden Seiten/Themen performen gut und überschneiden sich mit der Idee?
Falls keine Überschneidung, schreibe "Kein direktes GA4-Signal."

## GSC-Signale
Welche Suchanfragen deuten auf Leser-Interesse an diesem Thema hin?
Falls keine Überschneidung, schreibe "Kein direktes GSC-Signal."

## Fazit
2-3 Sätze: Wie gut ist die Datenlage für diese Idee?

Antworte auf Deutsch. Sei präzise und faktenbasiert."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def _format_rss(articles: list[dict]) -> str:
    if not articles:
        return "Keine RSS-Daten verfügbar."
    lines = []
    for a in articles[:40]:
        pub = a.get("published", "")
        pub_str = pub.strftime("%d.%m.%Y") if hasattr(pub, "strftime") else str(pub)[:10]
        title = a.get("title", "")[:100]
        source = a.get("source", "")
        summary = a.get("summary", "")[:200]
        lines.append(f"[{source}] {title} ({pub_str})\n  {summary}")
    return "\n\n".join(lines)


def _format_ga4(pages: list[dict]) -> str:
    if not pages:
        return "Keine GA4-Daten verfügbar."
    lines = ["Titel | Aufrufe | Engagement-Rate", "------|---------|----------------"]
    for p in pages[:15]:
        lines.append(
            f"{p['page_title'][:80]} | {p['page_views']} | {p['engagement_rate']}%"
        )
    return "\n".join(lines)


def _format_gsc(queries: list[dict]) -> str:
    if not queries:
        return "Keine GSC-Daten verfügbar."
    lines = [
        "Suchanfrage | Impressionen | Klicks | CTR | Position",
        "-----------|--------------|--------|-----|----------",
    ]
    for q in queries[:20]:
        lines.append(
            f"{q['query'][:60]} | {q['impressions']} | {q['clicks']} | {q['ctr']}% | {q['position']}"
        )
    return "\n".join(lines)
