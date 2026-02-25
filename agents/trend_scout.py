"""
Agent 2: Der Trend-Scout

Verarbeitet aktuelle RSS-Feed-Artikel von Wirtschaftsmedien.
Filtert und priorisiert die relevantesten News-Themen (Top 10).
"""

from openai import OpenAI
from config import OPENAI_MODEL


def run(client: OpenAI, articles: list[dict], token_callback=None) -> str:
    """
    Filter and summarize RSS articles, returning the 10 most relevant topics.
    """

    articles_text = _format_articles(articles)

    prompt = f"""Du bist ein erfahrener Wirtschaftsjournalist und Trend-Scout.

Hier sind aktuelle Artikel aus deutschsprachigen Wirtschaftsmedien (Handelsblatt, FAZ, NZZ):

{articles_text}

Deine Aufgabe:
1. Filtere die wichtigsten 10 Themen heraus – fokussiere auf aktuelle, relevante Wirtschaftsthemen.
2. Gruppiere ähnliche Themen (z.B. mehrere EZB-Artikel = ein Thema "EZB-Zinsentscheid").
3. Schreibe für jedes Thema:
   - **Thema:** (kurzer, prägnanter Titel)
   - **Warum relevant:** (1-2 Sätze: was passiert gerade, warum ist es wichtig)
   - **Quelle:** (welches Medium hat darüber berichtet)

Antworte auf Deutsch. Strukturiere deine Antwort klar."""

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


def _format_articles(articles: list[dict]) -> str:
    if not articles:
        return "Keine RSS-Artikel verfügbar."

    lines = []
    for i, a in enumerate(articles[:40], 1):
        date_str = a["published"].strftime("%d.%m.%Y %H:%M") if a.get("published") else "unbekannt"
        summary = f" – {a['summary'][:200]}" if a.get("summary") else ""
        lines.append(f"{i}. [{a['source']}] {a['title']} ({date_str}){summary}")

    return "\n".join(lines)
