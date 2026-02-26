"""
Evaluator-Agent: Bewertet User-Idee, gibt Verdict + Pro/Contra zurück.

Bewertet anhand von 4 Dimensionen (je 0-100):
  - Aktualität:    Gibt es einen aktuellen RSS-Anlass?
  - Nachfrage:     Suchen Leser danach (GSC-Signale)?
  - Einzigartigkeit: Lücke im bestehenden Content (GA4)?
  - Relevanz:      Passt es zum Wirtschafts-Newsroom?

Score = Durchschnitt der 4 Dimensionen.
Verdict: ≥ 70 → "Empfohlen", 45–69 → "Mit Vorbehalt", < 45 → "Nicht empfohlen"
"""

import json
from openai import OpenAI
from config import OPENAI_MODEL


def run(client: OpenAI, idea_title: str, idea_desc: str, context: str) -> dict:
    """
    Bewertet die eingereichte Idee anhand des Kontext-Agent-Outputs.

    Returns:
        {
            "verdict":         "Empfohlen" | "Mit Vorbehalt" | "Nicht empfohlen",
            "score":           0-100,
            "pros":            ["...", "..."],   # 2-4 Punkte
            "cons":            ["...", "..."],   # 2-4 Punkte
            "recommendation":  "2-3 Sätze Handlungsempfehlung",
        }
    """
    desc_section = f"\n**Beschreibung:** {idea_desc.strip()}" if idea_desc.strip() else ""

    prompt = f"""Du bist ein erfahrener Chefredakteur eines deutschsprachigen Wirtschaftsmediums.

Bewerte die folgende Artikel-Idee anhand der vorliegenden Datenlage.

**Eingereichte Idee:**
**Titel:** {idea_title}{desc_section}

**Kontext-Analyse (von Daten-Rechercheur):**
{context}

---

Bewerte die Idee entlang dieser 4 Dimensionen (je 0–100 Punkte):

1. **Aktualität** (0–100): Gibt es einen konkreten aktuellen RSS-Anlass? Ist das Thema gerade in den Nachrichten?
2. **Nachfrage** (0–100): Zeigen GSC-Daten, dass Leser aktiv danach suchen? Gibt es Suchvolumen?
3. **Einzigartigkeit** (0–100): Besteht eine Content-Lücke? Gibt es wenig oder kein bestehendes GA4-Material zu diesem Thema?
4. **Relevanz** (0–100): Passt die Idee zum Wirtschafts-Newsroom (Geldpolitik, Investitionen, Konjunktur, Unternehmen, Steuern)?

Der Gesamt-Score ist der Durchschnitt der 4 Dimensionen.

Verdict-Mapping:
- Score ≥ 70 → "Empfohlen"
- Score 45–69 → "Mit Vorbehalt"
- Score < 45 → "Nicht empfohlen"

Antworte ausschliesslich mit einem JSON-Objekt in diesem Format:
{{
  "scores": {{
    "aktualitaet": <0-100>,
    "nachfrage": <0-100>,
    "einzigartigkeit": <0-100>,
    "relevanz": <0-100>
  }},
  "score": <Durchschnitt 0-100, gerundet auf ganze Zahl>,
  "verdict": "Empfohlen" | "Mit Vorbehalt" | "Nicht empfohlen",
  "pros": ["<Punkt 1>", "<Punkt 2>", "<Punkt 3>"],
  "cons": ["<Punkt 1>", "<Punkt 2>"],
  "recommendation": "<2-3 Sätze Handlungsempfehlung auf Deutsch>"
}}

Wichtig:
- "pros" und "cons": je 2–4 konkrete, faktenbezogene Punkte
- "recommendation": praxisnah, was der Redakteur als nächstes tun soll
- Antworte ausschliesslich mit dem JSON-Objekt, ohne Erklärungen davor oder danach"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    # Normalize and validate output
    scores = data.get("scores", {})
    dims = [
        scores.get("aktualitaet", 0),
        scores.get("nachfrage", 0),
        scores.get("einzigartigkeit", 0),
        scores.get("relevanz", 0),
    ]
    computed_score = round(sum(dims) / len(dims)) if dims else 0
    score = int(data.get("score", computed_score))

    # Enforce verdict based on score
    if score >= 70:
        verdict = "Empfohlen"
    elif score >= 45:
        verdict = "Mit Vorbehalt"
    else:
        verdict = "Nicht empfohlen"

    return {
        "verdict": verdict,
        "score": score,
        "pros": data.get("pros", []),
        "cons": data.get("cons", []),
        "recommendation": data.get("recommendation", ""),
    }
