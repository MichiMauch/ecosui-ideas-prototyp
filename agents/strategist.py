"""
Agent 3: Der Stratege

Kombiniert die Erkenntnisse aus Analyst und Trend-Scout.
Generiert 10 konkrete, spezifische Content-Ideen mit Kernbotschaft.

Neu: Bekommt gecrawlte Zusammenfassungen bestehender Top-Seiten, um
  - Themen-Duplikate zu vermeiden
  - Neue Winkel auf bereits behandelte Themen vorzuschlagen
  - Update-Kandidaten zu identifizieren (veraltete Artikel)
"""

from openai import OpenAI
from config import OPENAI_MODEL, IDEAS_COUNT


def run(
    client: OpenAI,
    analyst_output: str,
    trend_scout_output: str,
    crawl_summaries: str = "",
    token_callback=None,
) -> str:
    """
    Combine analyst and trend scout findings into raw content ideas.

    Args:
        crawl_summaries: Formatted string of existing top-page content
                         (from data/content_crawler.py).  Pass "" if unavailable.
    """

    existing_content_section = ""
    if crawl_summaries and crawl_summaries.strip() not in (
        "", "Keine bestehenden Seiten gecrawlt.", "Keine gecrawlten Seiten verfügbar."
    ):
        existing_content_section = f"""
**BESTEHENDER CONTENT (Top-Seiten der eigenen Website):**
{crawl_summaries}

Wichtig für die Ideen-Entwicklung:
- Schlage KEINE Themen vor, die auf diesen Seiten bereits umfassend behandelt werden
- Wenn ein Thema bereits vorhanden ist, entwickle einen neuen Blickwinkel oder schlage ein Update vor
- Markiere Update-Ideen explizit mit [UPDATE] vor der Idee-Nummer
- Artikel, die älter als 2 Jahre wirken und noch viel Traffic haben, sind prime Update-Kandidaten
"""

    prompt = f"""Du bist ein erfahrener Content-Stratege für ein deutschsprachiges Wirtschaftsmedium.

Du bekommst zwei Analysen und optional eine Übersicht der bestehenden Top-Artikel der eigenen Website:

**ANALYSE 1 – Performance-Erkenntnisse (Google Analytics + Search Console):**
{analyst_output}

**ANALYSE 2 – Aktuelle Trends (Wirtschaftsmedien RSS):**
{trend_scout_output}
{existing_content_section}
Deine Aufgabe:
Identifiziere Schnittmengen zwischen den Performance-Daten und den aktuellen Trends.
Entwickle daraus genau {IDEAS_COUNT} spezifische Content-Ideen.

Für jede Idee:
- **Idee [Nummer]:** (noch kein fertiger Titel – nur das Thema/Konzept)
- **Kernbotschaft:** (was ist der zentrale Inhalt des Artikels?)
- **Daten-Basis:** (welche Signale aus Analytics/GSC/RSS stützen diese Idee?)
- **Typ:** Neuer Artikel oder [UPDATE] eines bestehenden Artikels?

Wichtig:
- Sei spezifisch. Nicht "Zinsen" sondern "Wie sich der neue EZB-Leitzins auf Festgeld-Angebote 2025 auswirkt"
- Vermeide offensichtliche oder generische Themen
- Priorisiere Themen, die sowohl aktuell (RSS) als auch gesucht (GSC) sind
- Falls bestehender Content vorhanden: Duplikate vermeiden, neue Winkel bevorzugen

Antworte auf Deutsch."""

    if token_callback:
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
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
            temperature=0.5,
        )
        return response.choices[0].message.content
