"""
Evaluator Agent

Scores the article on 4 dimensions (0-100 each).
Returns pass/fail based on EVALUATOR_MIN_SCORE threshold.
"""

import json

from openai import OpenAI

from config import OPENAI_MODEL_PRO as OPENAI_MODEL, EVALUATOR_MIN_SCORE


def run(
    client: OpenAI,
    article: dict,
    idea: dict,
) -> dict:
    """
    Evaluate article quality on 4 dimensions.

    Returns:
        {
            "scores": {
                "authentizitaet": int,   # 0-100
                "tiefe": int,            # 0-100
                "klarheit": int,         # 0-100
                "relevanz": int,         # 0-100
            },
            "overall": int,              # average of 4 scores
            "passed": bool,              # overall >= EVALUATOR_MIN_SCORE
            "feedback": str,             # actionable improvement notes
        }
    """

    article_json = json.dumps(article, ensure_ascii=False, indent=2)
    idea_title = idea.get("title", "")
    idea_why = idea.get("why_now", "")

    system_prompt = (
        "Du bist ein kritischer Chefredakteur für einen Wirtschafts-Newsroom. "
        "Bewerte Artikel streng aber fair auf 4 Dimensionen. "
        "Antworte ausschließlich als JSON."
    )

    user_prompt = f"""Artikel-Idee: {idea_title}
Warum jetzt: {idea_why}

Artikel (JSON):
{article_json}

Bewerte den Artikel auf diesen 4 Dimensionen (je 0-100 Punkte):

1. **Authentizität** (authentizitaet): Ist der Ton sachlich und glaubwürdig? Keine werbliche Sprache?
2. **Tiefe** (tiefe): Werden Themen substanziell behandelt? Konkrete Fakten statt Allgemeinplätze?
3. **Klarheit** (klarheit): Ist der Artikel verständlich strukturiert? Klare Argumentation?
4. **Relevanz** (relevanz): Passt der Artikel zur Idee? Ist er aktuell und für die Zielgruppe relevant?

Gib zurück:
{{
  "scores": {{
    "authentizitaet": <0-100>,
    "tiefe": <0-100>,
    "klarheit": <0-100>,
    "relevanz": <0-100>
  }},
  "overall": <Durchschnitt der 4 Scores, gerundet>,
  "passed": <true wenn overall >= {EVALUATOR_MIN_SCORE}, sonst false>,
  "feedback": "<Konkrete Verbesserungshinweise für den Writer, falls passed=false. Sonst leerer String.>"
}}"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    evaluation = json.loads(raw)

    # Ensure structure and recompute overall + passed for safety
    scores = evaluation.get("scores", {})
    score_values = [
        scores.get("authentizitaet", 0),
        scores.get("tiefe", 0),
        scores.get("klarheit", 0),
        scores.get("relevanz", 0),
    ]
    overall = round(sum(score_values) / max(len(score_values), 1))
    evaluation["overall"] = overall
    evaluation["passed"] = overall >= EVALUATOR_MIN_SCORE
    evaluation.setdefault("feedback", "")

    return evaluation
