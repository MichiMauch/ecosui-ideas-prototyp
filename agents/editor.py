"""
Agent 4: Der Redakteur

Verfeinert die Roh-Ideen des Strategen.
Schreibt für jede Idee:
  - Einen clickwürdigen, präzisen Artikel-Titel
  - Eine kurze "Warum jetzt?"-Begründung (2-3 Sätze)

Gibt strukturiertes JSON zurück, das direkt in der UI dargestellt werden kann.
"""

import json
from openai import OpenAI
from config import OPENAI_MODEL, IDEAS_COUNT


def run(client: OpenAI, strategist_output: str, rss_articles: list[dict] | None = None) -> list[dict]:
    """
    Refine raw ideas into polished titles with 'why now' justifications.

    Returns a list of dicts:
        [{"title": str, "why_now": str, "category": str, "signals": dict, "rss_links": list}, ...]
    """

    # Build RSS context block for the prompt
    rss_context = ""
    if rss_articles:
        lines = []
        for a in rss_articles[:30]:  # cap to avoid token overflow
            title = a.get("title", "")
            url = a.get("url", "")
            source = a.get("source", "")
            if title and url:
                lines.append(f'- "{title}" ({source}) → {url}')
        if lines:
            rss_context = "\n\nVerfügbare RSS-Artikel (Title, Quelle, URL):\n" + "\n".join(lines)

    prompt = f"""Du bist ein erfahrener digitaler Redakteur bei einem deutschsprachigen Wirtschaftsmedium.

Hier sind {IDEAS_COUNT} Content-Ideen von unserem Strategen (inkl. Daten-Basis):

{strategist_output}{rss_context}

Deine Aufgabe:
Verfeinere jede Idee zu einer vollständigen Content-Empfehlung.

Antworte als JSON-Objekt mit einem Schlüssel "ideas", dessen Wert ein Array mit genau {IDEAS_COUNT} Objekten ist. Jedes Objekt hat diese Felder:
- "title": Ein prägnanter, clickwürdiger Artikel-Titel (10-15 Wörter). Deutsch.
- "why_now": 2-3 Sätze, warum dieses Thema JETZT besonders relevant ist. Referenziere konkrete Signale (EZB-Entscheid, hohe Suchanfragen, etc.). Deutsch.
- "category": Themen-Kategorie, z.B. "Geldpolitik", "Investitionen", "Konjunktur", "Unternehmen", "Steuern & Recht"
- "signals": Ein Objekt mit den konkreten Daten-Signalen, die diese Idee stützen. Jeder Wert soll ZUERST die Beobachtung nennen und dann mit " → " die kausale Verbindung zur Idee erklären (warum dieses Signal genau DIESE Idee nahelegt):
  - "ga4": Welche GA4-Seiten oder Engagement-Daten sprechen für dieses Thema, und warum? (1-2 Sätze, mit " → Begründung")
  - "gsc": Welche Suchanfragen oder CTR-Lücken aus der Search Console begründen die Idee, und warum? (1-2 Sätze, mit " → Begründung")
  - "rss": Welche aktuellen Artikel aus den RSS-Feeds machen das Thema jetzt relevant, und warum? (1-2 Sätze mit Quellname, mit " → Begründung")
  Falls ein Signal-Typ nicht relevant ist, leerer String "".
- "rss_links": Array mit 1–3 RSS-Artikeln, die inhaltlich am besten zu dieser Idee passen. Wähle nur aus der oben gegebenen RSS-Artikel-Liste. Jedes Objekt hat: "title" (Artikeltitel), "url" (exakt wie angegeben), "source" (Quellenname). Leeres Array [] wenn kein RSS-Signal relevant ist.

Wichtig:
- Titel sollen neugierig machen, aber keine Clickbait-Übertreibungen
- signals soll die Daten-Basis aus dem Strategen-Output direkt widerspiegeln
- Die " → Begründung" in signals erklärt den kausalen Zusammenhang zur Idee in einem Satz

Beispiel:
{{
  "ideas": [
    {{
      "title": "EZB-Wende: Warum dein Festgeld jetzt zur Falle werden könnte",
      "why_now": "Der gestrige EZB-Zinsentscheid hat die Erwartungen vieler Anleger auf den Kopf gestellt. Gleichzeitig suchen laut unseren Daten besonders viele Leser nach Alternativen zu klassischen Sparformen. Ein erklärender Ratgeber füllt diese Lücke optimal.",
      "category": "Geldpolitik",
      "signals": {{
        "ga4": "Die Seite /festgeld-vergleich erzielte letzte Woche 3.200 Aufrufe mit 72% Engagement-Rate. → Bestehendes Leserinteresse zeigt, ein Folgeartikel mit aktueller Zinsperspektive baut direkt darauf auf.",
        "gsc": "Die Suchanfrage 'Festgeld Zinsen 2025' hat 1.800 Impressionen bei nur 1,4% CTR. → Klare Inhaltslücke: Leser suchen aktiv, finden aber keine zufriedenstellende Antwort auf unserer Seite.",
        "rss": "NZZ und SRF berichteten beide über den überraschenden EZB-Entscheid vom 23.02. → Das Thema ist medial präsent; ein Ratgeber-Artikel positioniert uns als erste Anlaufstelle für verunsicherte Anleger."
      }},
      "rss_links": [
        {{"title": "EZB überrascht mit Zinssenkung", "url": "https://www.nzz.ch/finanzen/ezb-zinssenkung-2025", "source": "NZZ"}}
      ]
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    parsed = json.loads(raw)

    # Extract list from response object
    candidate_list = None
    if isinstance(parsed, list):
        candidate_list = parsed
    else:
        for key in ("ideas", "items", "results", "content_ideas"):
            if key in parsed and isinstance(parsed[key], list):
                candidate_list = parsed[key]
                break
        if candidate_list is None:
            for value in parsed.values():
                if isinstance(value, list):
                    candidate_list = value
                    break

    if candidate_list is None:
        return []

    # Ensure all items are dicts with the expected structure and default signals
    result = []
    for item in candidate_list:
        if not isinstance(item, dict):
            continue
        if "signals" not in item or not isinstance(item["signals"], dict):
            item["signals"] = {"ga4": "", "gsc": "", "rss": ""}
        else:
            item["signals"].setdefault("ga4", "")
            item["signals"].setdefault("gsc", "")
            item["signals"].setdefault("rss", "")
        item.setdefault("rss_links", [])
        # Compute A/B/C data-confidence score based on signal count
        item["score"] = _compute_score(item["signals"])
        result.append(item)

    # Sort by score: A first, then B, then C
    score_order = {"A": 0, "B": 1, "C": 2}
    result.sort(key=lambda x: score_order.get(x.get("score", "C"), 2))

    return result


def _compute_score(signals: dict) -> str:
    """
    Compute data-confidence score A/B/C based on number of populated signals.

    A = all 3 signals (ga4, gsc, rss) present
    B = 2 signals present
    C = 0 or 1 signal present
    """
    count = sum(1 for v in (signals.get("ga4"), signals.get("gsc"), signals.get("rss")) if v)
    if count >= 3:
        return "A"
    if count == 2:
        return "B"
    return "C"
