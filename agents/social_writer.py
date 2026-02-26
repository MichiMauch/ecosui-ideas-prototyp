"""
Social Writer Agent

Generates social media snippets from a finished article:
  - LinkedIn post (~1200 chars, professional, ends with question/CTA)
  - X/Twitter post (max. 280 chars, punchy, minimal hashtags)
  - Newsletter teaser (2 sentences, curiosity-driven)
"""

import json

from openai import OpenAI

from config import OPENAI_MODEL_PRO as OPENAI_MODEL


def run(client: OpenAI, article: dict, idea_title: str) -> dict:
    """
    Generate social media snippets from a finished article.

    Args:
        client:     OpenAI client
        article:    Finished article dict (title, lead, sections, meta_description)
        idea_title: Original idea title as fallback

    Returns:
        {
            "linkedin": str,
            "twitter": str,
            "newsletter_teaser": str,
        }
    """

    title = article.get("title", idea_title)
    lead = article.get("lead", "")
    sections = article.get("sections", [])

    # Use first 3 sections for context (avoid overly long prompts)
    sections_text = "\n\n".join(
        f"## {s.get('heading', '')}\n{s.get('content', '')}"
        for s in sections[:3]
    )

    system_prompt = """Du bist ein Social-Media-Redakteur für eine deutschsprachige Wirtschaftspublikation.

Erstelle drei Social-Media-Texte basierend auf dem gegebenen Artikel.
Schreibe auf Deutsch, sachlich und prägnant. Passe den Ton ans jeweilige Medium an.

Gib die Antwort als JSON zurück mit exakt dieser Struktur:
{
  "linkedin": "LinkedIn-Post: 3 kurze Absätze, professionell-sachlich, endet mit einer Frage oder einem Call-to-Action, ca. 1200 Zeichen",
  "twitter": "X/Twitter-Post: max. 280 Zeichen, prägnant, maximal 1-2 relevante Hashtags, kein Hashtag-Spam",
  "newsletter_teaser": "Newsletter-Teaser: genau 2 Sätze, weckt Neugier, für E-Mail-Betreff optimiert"
}"""

    user_prompt = f"""Artikel-Titel: {title}

Lead: {lead}

{sections_text}

Erstelle passende Social-Media-Texte für diesen Wirtschaftsartikel."""

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
    snippets = json.loads(raw)

    snippets.setdefault("linkedin", "")
    snippets.setdefault("twitter", "")
    snippets.setdefault("newsletter_teaser", "")

    return snippets
