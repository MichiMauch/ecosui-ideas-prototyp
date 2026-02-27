"""
Researcher Agent

Extracts concrete facts, statistics, and sources from available data
(RSS articles + GSC queries) to support article writing.
No external API calls — works only with the data already fetched.
"""

import json

from openai import OpenAI

from config import OPENAI_MODEL_PRO as OPENAI_MODEL


def run(
    client: OpenAI,
    idea: dict,
    rss_articles: list[dict],
    gsc_queries: list[dict],
) -> str:
    """
    Analyse available data and extract research notes for the given idea.

    Returns a structured string with:
    - Kernthesen (key arguments)
    - Belege aus RSS (evidence from news)
    - Search-Insights (from GSC queries)
    - Mögliche Zitate / Quellenhinweise
    """

    # Format RSS articles relevant to the idea
    rss_text = ""
    if rss_articles:
        rss_lines = []
        for a in rss_articles[:40]:
            pub = a.get("published", "")
            pub_str = pub.strftime("%d.%m.%Y") if hasattr(pub, "strftime") else str(pub or "")
            rss_lines.append(
                f"- [{a.get('source', '')}] {a.get('title', '')} ({pub_str})\n"
                f"  {a.get('summary', '')[:300]}"
            )
        rss_text = "\n".join(rss_lines)
    else:
        rss_text = "Keine RSS-Artikel verfügbar."

    # Format GSC queries
    gsc_text = ""
    if gsc_queries:
        gsc_lines = []
        for q in gsc_queries[:25]:
            gsc_lines.append(
                f"- \"{q.get('query', '')}\" — "
                f"{q.get('impressions', 0)} Impressionen, "
                f"{q.get('clicks', 0)} Klicks, "
                f"CTR {q.get('ctr', 0):.1f}%, "
                f"Pos. {q.get('position', 0):.1f}"
            )
        gsc_text = "\n".join(gsc_lines)
    else:
        gsc_text = "Keine GSC-Daten verfügbar."

    idea_title = idea.get("title", "")
    idea_why = idea.get("why_now", "")
    idea_category = idea.get("category", "")

    system_prompt = (
        "Du bist ein präziser Rechercheur für einen Wirtschafts-Newsroom. "
        "Deine Aufgabe ist es, aus den vorhandenen Daten (RSS-Artikel, Suchanfragen) "
        "konkrete Fakten, Belege und Quellen für einen Artikel herauszuarbeiten. "
        "Keine Erfindungen, keine externen Suchen — nur was in den Daten steht. "
        "Antworte auf Deutsch."
    )

    user_prompt = f"""Artikel-Idee: {idea_title}
Kategorie: {idea_category}
Hintergrund: {idea_why}

Verfügbare RSS-Artikel:
{rss_text}

Suchanfragen der Leser (Google Search Console):
{gsc_text}

Erstelle strukturierte Research-Notes mit folgenden Abschnitten:

## Kernthesen
(2-4 zentrale Aussagen, die der Artikel belegen soll)

## Belege & Datenpunkte
(Konkrete Zahlen, Fakten, Zitate als Bullet-Liste — mit Quellenangabe [Medienname])
- Fakt: ... [Quelle]
- Zahl: ... [Quelle]
- Zitat: "..." [Quelle]

## Leserfragen (aus Search Console)
(Nur als inhaltliche Fragen formuliert — KEINE Metriken im Artikel verwenden)
- Frage 1?
- Frage 2?

## SEO-Kontext [NUR FÜR JOURNALIST_NOTES — niemals in Artikelabschnitte]
(Rohdaten: Suchvolumen, CTR, Positionen — gehören in journalist_notes, nicht in den Artikel)
- "keyword" — X Impressionen, Y Klicks, CTR Z%, Pos. P

## Empfohlene Artikel-Struktur
(Vorschlag: 4-6 Abschnitte mit je 1-Satz-Beschreibung was dort stehen soll)
1. Einleitung / Kontext
2. ...
3. Fazit

## Relevante Quellen
(Liste der verwendeten Artikel mit Titel und Medium)

Halte die Notes präzise und faktenbasiert."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content or ""
