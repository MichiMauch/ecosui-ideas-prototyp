"""
Fact-Checker Agent

Verifies claims in an article against research notes.
Removes or corrects unsupported statements.
Returns a corrected article dict with the same structure as the Writer output.
"""

import json

from openai import OpenAI

from config import OPENAI_MODEL_PRO as OPENAI_MODEL


def run(
    client: OpenAI,
    article: dict,
    research_notes: str,
) -> dict:
    """
    Check facts in the article against research_notes.

    Returns corrected article dict:
        {
            "title": str,
            "lead": str,
            "sections": [{"heading": str, "content": str}, ...],
            "meta_description": str,
        }
    """

    article_json = json.dumps(article, ensure_ascii=False, indent=2)

    system_prompt = (
        "Du bist ein strenger Fact-Checker für einen Wirtschafts-Newsroom. "
        "Prüfe jeden faktischen Anspruch im Artikel gegen die Research-Notes. "
        "Korrigiere oder entferne Aussagen, die in den Research-Notes nicht belegt sind. "
        "Erfinde keine neuen Fakten. Behalte Struktur und Stil des Artikels bei. "
        "Antworte auf Deutsch als JSON mit exakt der gleichen Struktur wie der Input-Artikel."
    )

    user_prompt = f"""Research-Notes (einzige Wahrheitsquelle):
{research_notes}

Artikel zum Prüfen (JSON):
{article_json}

Aufgabe:
1. Prüfe jeden faktischen Anspruch (Zahlen, Namen, Daten, Ereignisse) gegen die Research-Notes
2. Korrigiere falsche oder unbelegte Fakten
3. Entferne Aussagen, die sich gar nicht belegen lassen
4. Behalte korrekte Aussagen unverändert bei
5. Verändere Stil und Struktur möglichst wenig

Gib den korrigierten Artikel als JSON zurück (gleiche Struktur: title, lead, sections, meta_description)."""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    corrected = json.loads(raw)

    # Fall back to original values if keys are missing
    corrected.setdefault("title", article.get("title", ""))
    corrected.setdefault("lead", article.get("lead", ""))
    corrected.setdefault("sections", article.get("sections", []))
    corrected.setdefault("meta_description", article.get("meta_description", ""))

    return corrected
