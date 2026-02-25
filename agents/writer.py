"""
Writer Agent

Generates a full article (700-1000 words, German) based on an idea and
research notes. Respects brand voice and avoids forbidden phrases.
On revision passes, incorporates evaluator feedback.
"""

import json

from openai import OpenAI

from config import OPENAI_MODEL_PRO as OPENAI_MODEL, ARTICLE_TARGET_WORDS


def run(
    client: OpenAI,
    idea: dict,
    research_notes: str,
    brand_voice: str,
    forbidden_phrases: list[str],
    target_words: int = ARTICLE_TARGET_WORDS,
    revision_feedback: str | None = None,
) -> dict:
    """
    Write or revise a full article.

    Returns:
        {
            "title": str,
            "lead": str,
            "sections": [{"heading": str, "content": str}, ...],
            "meta_description": str,
        }
    """

    forbidden_list = "\n".join(f"- {p}" for p in forbidden_phrases)

    system_prompt = f"""Du bist ein erfahrener Wirtschaftsjournalist.

BRAND VOICE:
{brand_voice.strip()}

VERBOTENE PHRASEN (diese Formulierungen niemals verwenden):
{forbidden_list}

FORMATIERUNG (Markdown innerhalb der section.content Felder):
- Verwende **fettgedruckte** Hervorhebungen für Schlüsselbegriffe und wichtige Zahlen
- Setze Aufzählungslisten (- oder 1.) ein, wenn 3 oder mehr gleichartige Punkte genannt werden
- Trenne Absätze mit Leerzeile für bessere Lesbarkeit
- Jeder Abschnitt soll mindestens 2 Absätze oder eine Liste enthalten
- Verwende niemals h3/h4-Markdown-Überschriften innerhalb von content (###) — nur Fliesstext, Fett und Listen

Schreibe auf Deutsch. Zielumfang: ca. {target_words} Wörter.
Gib die Antwort als JSON zurück mit exakt dieser Struktur:
{{
  "title": "Artikel-Titel",
  "lead": "Einleitungsabsatz (2-3 Sätze)",
  "sections": [
    {{"heading": "Abschnitts-Überschrift", "content": "Abschnittstext"}},
    ...
  ],
  "meta_description": "SEO-Meta-Beschreibung (max. 160 Zeichen)"
}}"""

    idea_title = idea.get("title", "")
    idea_why = idea.get("why_now", "")
    idea_category = idea.get("category", "")

    if revision_feedback:
        task_description = f"""Überarbeite den Artikel basierend auf folgendem Feedback:

FEEDBACK:
{revision_feedback}

Stelle sicher, dass alle genannten Punkte verbessert werden."""
    else:
        task_description = "Schreibe einen vollständigen Artikel zu dieser Idee."

    user_prompt = f"""Artikel-Idee: {idea_title}
Kategorie: {idea_category}
Warum jetzt: {idea_why}

Research-Notes:
{research_notes}

{task_description}

Der Artikel soll:
- ca. {target_words} Wörter umfassen (mindestens {target_words - 150}, höchstens {target_words + 200})
- 4-6 thematische Abschnitte haben
- mindestens 2 Abschnitte mit Aufzählungen oder nummerierten Listen enthalten
- konkrete Zahlen, Namen und Fakten aus den Research-Notes verwenden (**fettgedruckt** hervorheben)
- mit einem Abschnitt "Fazit" oder "Was bedeutet das?" enden
- keine werbliche Sprache enthalten
- für ein gebildetes Wirtschaftspublikum verständlich sein"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.7,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    article = json.loads(raw)

    # Ensure required keys exist
    article.setdefault("title", idea_title)
    article.setdefault("lead", "")
    article.setdefault("sections", [])
    article.setdefault("meta_description", "")

    return article
