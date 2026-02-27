"""
Test: GSC-Metriken dürfen nicht in Artikel-Abschnitten erscheinen.

Läuft Researcher + Writer mit synthetischen Daten durch und prüft,
ob Begriffe wie "Impressionen", "Klicks", "CTR", "Pos." in sections auftauchen.
"""

import json
import os
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI

import agents.researcher as researcher_agent
import agents.writer as writer_agent
from config import BRAND_VOICE, FORBIDDEN_PHRASES, ARTICLE_TARGET_WORDS

load_dotenv()

# ── Mock-Daten ────────────────────────────────────────────────────────────────

IDEA = {
    "title": "Warum KMU jetzt auf KI-gestützte Buchhaltung setzen",
    "why_now": "Neue Pflicht zur E-Rechnung ab 2025 zwingt Unternehmen zur Digitalisierung",
    "category": "Digitalisierung",
}

RSS_ARTICLES = [
    {
        "source": "Handelsblatt",
        "title": "E-Rechnung: Das müssen KMU jetzt wissen",
        "published": "2025-01-15",
        "summary": "Ab 2025 gilt in Deutschland die Pflicht zur elektronischen Rechnung. "
                   "Rund 3,5 Millionen kleine Unternehmen sind betroffen. "
                   "Experten empfehlen, die Umstellung frühzeitig anzugehen.",
    },
    {
        "source": "WirtschaftsWoche",
        "title": "KI in der Buchhaltung spart bis zu 40 Prozent Zeit",
        "published": "2025-01-20",
        "summary": "Eine Studie des Bitkom zeigt: Unternehmen, die KI-gestützte Buchhaltungssoftware "
                   "einsetzen, sparen im Schnitt 40 Prozent ihrer Buchhaltungszeit. "
                   "Besonders profitieren Firmen mit 10–50 Mitarbeitern.",
    },
]

# GSC-Daten mit echten Metriken — genau das, was NICHT im Artikel landen soll
GSC_QUERIES = [
    {"query": "ki buchhaltung kmu", "impressions": 1240, "clicks": 87, "ctr": 7.0, "position": 3.2},
    {"query": "e-rechnung pflicht 2025", "impressions": 5800, "clicks": 412, "ctr": 7.1, "position": 1.8},
    {"query": "buchhaltungssoftware vergleich", "impressions": 890, "clicks": 31, "ctr": 3.5, "position": 6.4},
    {"query": "digitale buchhaltung vorteile", "impressions": 430, "clicks": 19, "ctr": 4.4, "position": 5.1},
]

# ── Leak-Erkennungs-Pattern ───────────────────────────────────────────────────

LEAK_PATTERNS = [
    r"\d+\s*Impressionen",
    r"\d+\s*Klicks",
    r"CTR\s+\d",
    r"CTR\s*[\d,\.]+\s*%",
    r"Pos\.\s*[\d,\.]+",
    r"Position\s+[\d,\.]+",
    r"[\d,\.]+\s*%\s*CTR",
]


def check_article_for_leaks(article: dict) -> list[str]:
    """Prüft title, lead und alle sections auf GSC-Metrik-Leaks."""
    leaks = []

    fields_to_check = []
    fields_to_check.append(("title", article.get("title", "")))
    fields_to_check.append(("lead", article.get("lead", "")))
    for i, sec in enumerate(article.get("sections", [])):
        fields_to_check.append((f"sections[{i}].heading", sec.get("heading", "")))
        fields_to_check.append((f"sections[{i}].content", sec.get("content", "")))

    for field_name, text in fields_to_check:
        for pattern in LEAK_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                leaks.append(f"  LEAK in '{field_name}': Pattern '{pattern}' gefunden")
                leaks.append(f"    → {text[:200]}")

    return leaks


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("FEHLER: OPENAI_API_KEY nicht gesetzt.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("=" * 60)
    print("GSC-Leak-Test")
    print("=" * 60)

    # Step 1: Researcher
    print("\n[1/2] Researcher läuft...")
    research_notes = researcher_agent.run(client, IDEA, RSS_ARTICLES, GSC_QUERIES)
    print("Research-Notes (Auszug):")
    print(research_notes[:800])
    print("...")

    # Prüfen, ob SEO-Kontext-Block im Research erscheint
    has_seo_block = "SEO-Kontext" in research_notes or "JOURNALIST_NOTES" in research_notes or "journalist_notes" in research_notes.lower()
    print(f"\nSEO-Kontext-Block im Research vorhanden: {'JA ✓' if has_seo_block else 'NEIN (kein explizites Label)'}")

    # Step 2: Writer
    print("\n[2/2] Writer läuft...")
    article = writer_agent.run(
        client,
        IDEA,
        research_notes,
        BRAND_VOICE,
        FORBIDDEN_PHRASES,
        target_words=ARTICLE_TARGET_WORDS,
    )

    journalist_notes = article.get("journalist_notes", "")

    # Step 3: Leak-Check
    print("\n" + "=" * 60)
    print("ERGEBNIS")
    print("=" * 60)

    leaks = check_article_for_leaks(article)

    if leaks:
        print("\n❌ GSC-METRIKEN IM ARTIKEL GEFUNDEN:")
        for leak in leaks:
            print(leak)
    else:
        print("\n✅ Keine GSC-Metriken in Artikel-Abschnitten gefunden.")

    # journalist_notes prüfen
    notes_has_metrics = any(
        kw in journalist_notes for kw in ["Impressionen", "Klicks", "CTR", "Pos.", "Position"]
    )
    if notes_has_metrics:
        print("✅ journalist_notes enthält GSC-Metriken (korrekt).")
    else:
        print("⚠️  journalist_notes enthält KEINE GSC-Metriken (ggf. leer oder unvollständig).")

    print(f"\njournalist_notes:\n{journalist_notes[:600] or '(leer)'}")

    # Artikel-Struktur ausgeben
    print("\n" + "=" * 60)
    print("ARTIKEL-ABSCHNITTE")
    print("=" * 60)
    print(f"Titel: {article.get('title', '')}")
    print(f"Lead: {article.get('lead', '')[:200]}")
    for i, sec in enumerate(article.get("sections", [])):
        print(f"\n[{i+1}] {sec.get('heading', '')}")
        print(sec.get("content", "")[:300])

    return len(leaks) == 0


if __name__ == "__main__":
    passed = main()
    sys.exit(0 if passed else 1)
