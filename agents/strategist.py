"""
Agent 3: Der Stratege

Kombiniert die Erkenntnisse aus Analyst und Trend-Scout.
Generiert 10 konkrete, spezifische Content-Ideen mit Kernbotschaft.
"""

from openai import OpenAI
from config import OPENAI_MODEL, IDEAS_COUNT


def run(
    client: OpenAI,
    analyst_output: str,
    trend_scout_output: str,
    token_callback=None,
) -> str:
    """
    Combine analyst and trend scout findings into 10 raw content ideas.
    """

    prompt = f"""Du bist ein erfahrener Content-Stratege für ein deutschsprachiges Wirtschaftsmedium.

Du bekommst zwei Analysen:

**ANALYSE 1 – Performance-Erkenntnisse (Google Analytics + Search Console):**
{analyst_output}

**ANALYSE 2 – Aktuelle Trends (Wirtschaftsmedien RSS):**
{trend_scout_output}

Deine Aufgabe:
Identifiziere Schnittmengen zwischen den Performance-Daten und den aktuellen Trends.
Entwickle daraus genau {IDEAS_COUNT} spezifische Content-Ideen.

Für jede Idee:
- **Idee [Nummer]:** (noch kein fertiger Titel – nur das Thema/Konzept)
- **Kernbotschaft:** (was ist der zentrale Inhalt des Artikels?)
- **Daten-Basis:** (welche Signale aus Analytics/GSC/RSS stützen diese Idee?)

Wichtig:
- Sei spezifisch. Nicht "Zinsen" sondern "Wie sich der neue EZB-Leitzins auf Festgeld-Angebote 2025 auswirkt"
- Vermeide offensichtliche oder generische Themen
- Priorisiere Themen, die sowohl aktuell (RSS) als auch gesucht (GSC) sind

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
