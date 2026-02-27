"""Article export utilities: Markdown and PDF."""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from io import BytesIO


def _slugify(text: str) -> str:
    """Convert a title to a filesystem-friendly slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = text.strip("-")
    return text or "artikel"


def article_to_markdown(article: dict, social_snippets: dict | None = None, journalist_notes: str = "") -> str:
    """Return the article as a Markdown string."""
    parts: list[str] = []

    title = article.get("title", "")
    lead = article.get("lead", "")
    sections = article.get("sections", [])
    meta_description = article.get("meta_description", "")

    if title:
        parts.append(f"# {title}")
        parts.append("")

    if lead:
        parts.append(f"_{lead}_")
        parts.append("")
        parts.append("---")
        parts.append("")

    for section in sections:
        heading = section.get("heading", "")
        content = section.get("content", "")
        if heading:
            parts.append(f"## {heading}")
        if content:
            parts.append(content)
        parts.append("")

    if meta_description:
        parts.append("---")
        parts.append("")
        parts.append(f"**Meta-Beschreibung:** {meta_description}")
        parts.append("")

    if social_snippets:
        parts.append("---")
        parts.append("")
        parts.append("## Social Media")
        parts.append("")

        linkedin = social_snippets.get("linkedin", "")
        twitter = social_snippets.get("twitter", "") or social_snippets.get("x", "")
        newsletter = social_snippets.get("newsletter_teaser", "")

        if linkedin:
            parts.append("### LinkedIn")
            parts.append(linkedin)
            parts.append("")

        if twitter:
            parts.append("### X / Twitter")
            parts.append(twitter)
            parts.append("")

        if newsletter:
            parts.append("### Newsletter-Teaser")
            parts.append(newsletter)
            parts.append("")

    if journalist_notes:
        parts.append("---")
        parts.append("")
        parts.append("## Hinweise für den Journalisten")
        parts.append("")
        parts.append(journalist_notes)

    return "\n".join(parts)


def _sanitize_for_pdf(text: str) -> str:
    """Replace Unicode characters that Latin-1 (fpdf built-in fonts) cannot encode."""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2012": "-",   # figure dash
        "\u2015": "-",   # horizontal bar
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201A": "'",   # single low-9 quote
        "\u201C": '"',   # left double quote
        "\u201D": '"',   # right double quote
        "\u201E": '"',   # double low-9 quote
        "\u2026": "...", # ellipsis
        "\u2022": "-",   # bullet
        "\u2033": '"',   # double prime
        "\u2032": "'",   # prime
        "\u00A0": " ",   # non-breaking space
        "\u200B": "",    # zero-width space
        "\u200C": "",    # zero-width non-joiner
        "\u200D": "",    # zero-width joiner
        "\uFEFF": "",    # BOM
    }
    for char, repl in replacements.items():
        text = text.replace(char, repl)
    # Fallback: encode to Latin-1, replacing any remaining unknown chars
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text


def article_to_pdf(article: dict, social_snippets: dict | None = None, journalist_notes: str = "") -> bytes:
    """Return the article as PDF bytes using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    title = _sanitize_for_pdf(article.get("title", ""))
    lead = _sanitize_for_pdf(article.get("lead", ""))
    sections = article.get("sections", [])
    meta_description = _sanitize_for_pdf(article.get("meta_description", ""))

    # Title
    if title:
        pdf.set_font("Helvetica", style="B", size=20)
        pdf.multi_cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Lead
    if lead:
        pdf.set_font("Helvetica", style="I", size=12)
        pdf.multi_cell(0, 7, lead, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_draw_color(180, 180, 180)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(6)

    # Sections
    for section in sections:
        heading = _sanitize_for_pdf(section.get("heading", ""))
        content = _sanitize_for_pdf(section.get("content", ""))
        if heading:
            pdf.set_font("Helvetica", style="B", size=14)
            pdf.multi_cell(0, 8, heading, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        if content:
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, content, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Meta description
    if meta_description:
        pdf.set_draw_color(180, 180, 180)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)
        pdf.set_font("Helvetica", style="I", size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(0, 5, f"Meta-Beschreibung: {meta_description}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    # Social snippets on a new page
    if social_snippets:
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(0, 10, "Social Media", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        linkedin = _sanitize_for_pdf(social_snippets.get("linkedin", ""))
        twitter = _sanitize_for_pdf(social_snippets.get("twitter", "") or social_snippets.get("x", ""))
        newsletter = _sanitize_for_pdf(social_snippets.get("newsletter_teaser", ""))

        if linkedin:
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(0, 8, "LinkedIn", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, linkedin, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        if twitter:
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(0, 8, "X / Twitter", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, twitter, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        if newsletter:
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.cell(0, 8, "Newsletter-Teaser", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
            pdf.multi_cell(0, 6, newsletter, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

    if journalist_notes:
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(0, 10, "Hinweise fur den Journalisten", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, _sanitize_for_pdf(journalist_notes))

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def create_client_report(result, calendar: list[dict] | None = None) -> bytes:
    """
    Generate a multi-page professional PDF client report (5 pages):
    1. Cover page
    2. Executive Summary
    3. SEO potential & Quick Wins
    4. Top 3 Content ideas
    5. 4-week editorial calendar
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    def h1(text: str):
        pdf.set_font("Helvetica", style="B", size=22)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 12, _sanitize_for_pdf(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    def h2(text: str):
        pdf.set_font("Helvetica", style="B", size=15)
        pdf.set_text_color(50, 80, 150)
        pdf.multi_cell(0, 9, _sanitize_for_pdf(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def h3(text: str):
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 7, _sanitize_for_pdf(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def body(text: str):
        pdf.set_font("Helvetica", size=11)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 6, _sanitize_for_pdf(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    def caption(text: str):
        pdf.set_font("Helvetica", style="I", size=9)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 5, _sanitize_for_pdf(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    def divider():
        pdf.set_draw_color(200, 200, 200)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(4)

    # ── Page 1: Cover ──────────────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", style="B", size=28)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(0, 14, "Content-Strategie Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", size=14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, date.today().strftime("%d. %B %Y"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", style="I", size=11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 7, "Erstellt mit KI-Content-Analyse", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_draw_color(50, 80, 150)
    pdf.set_line_width(0.8)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.set_line_width(0.2)
    pdf.set_text_color(0, 0, 0)

    # ── Page 2: Executive Summary ──────────────────────────────────────────────
    pdf.add_page()
    h1("Executive Summary")
    divider()

    ideas = getattr(result, "ideas", []) or []
    gsc_queries = getattr(result, "gsc_queries", []) or []
    rss_articles = getattr(result, "rss_articles", []) or []
    ga4_pages = getattr(result, "ga4_pages", []) or []
    seo_pot = getattr(result, "seo_potential", {}) or {}
    trends_data = getattr(result, "trends_data", []) or []

    # Data sources bullet
    sources = []
    if ga4_pages:
        sources.append(f"Google Analytics 4 ({len(ga4_pages)} Seiten)")
    if gsc_queries:
        sources.append(f"Search Console ({len(gsc_queries)} Suchanfragen)")
    if rss_articles:
        sources.append(f"RSS-Feeds ({len(rss_articles)} Artikel)")
    if trends_data:
        sources.append(f"Google Trends ({len(trends_data)} Keywords)")

    # Strongest signal
    top_idea = ideas[0] if ideas else None
    strongest_signal = ""
    if top_idea:
        sigs = top_idea.get("signals", {})
        for key in ("rss", "gsc", "ga4"):
            if sigs.get(key):
                strongest_signal = str(sigs[key])[:120]
                break

    bullets = [
        f"Analysierte Content-Ideen: {len(ideas)}",
        f"Datenquellen: {', '.join(sources) if sources else 'Keine Daten verfuegbar'}",
        f"Starktes Signal: {strongest_signal}" if strongest_signal else "Kein dominierendes Signal identifiziert",
        f"Geschaetztes Traffic-Potenzial: +{seo_pot.get('total_potential', 0):,} Besucher/Monat" if seo_pot.get("total_potential") else "Traffic-Potenzial: Keine GSC-Daten",
    ]
    if seo_pot.get("top_opportunities"):
        top_opp = seo_pot["top_opportunities"][0]
        bullets.append(f"Top Quick Win: {top_opp['label']} (+{top_opp['monthly_delta']:,} Klicks/Monat)")
    else:
        bullets.append("Top Quick Win: Keine Daten verfuegbar")

    pdf.ln(2)
    for bullet in bullets:
        pdf.set_font("Helvetica", size=11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(6, 7, "-", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(0, 7, _sanitize_for_pdf(bullet), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    # ── Page 3: SEO Potential ──────────────────────────────────────────────────
    pdf.add_page()
    h1("SEO-Chancen & Quick Wins")
    divider()

    if seo_pot:
        h2("Zusammenfassung Potenzial")
        body(f"Fast-Ranker-Potenzial: +{seo_pot.get('fast_ranker_potential', 0):,} Klicks/Monat")
        body(f"CTR-Lucken-Potenzial: +{seo_pot.get('ctr_gap_potential', 0):,} Klicks/Monat")
        body(f"Gesamt-Potenzial: +{seo_pot.get('total_potential', 0):,} Klicks/Monat")
        pdf.ln(4)

        top_opps = seo_pot.get("top_opportunities", [])
        if top_opps:
            h2("Top Opportunitaten (Quick Wins)")
            # Table header
            pdf.set_fill_color(230, 235, 245)
            pdf.set_font("Helvetica", style="B", size=10)
            col_w = [90, 30, 50]
            headers = ["Seite / Keyword", "Position", "+Klicks/Monat"]
            for header, w in zip(headers, col_w):
                pdf.cell(w, 8, header, border=1, fill=True, new_x="RIGHT", new_y="TOP")
            pdf.ln(8)
            # Table rows
            pdf.set_font("Helvetica", size=9)
            for opp in top_opps:
                label = _sanitize_for_pdf(opp.get("label", ""))[:45]
                pos = str(opp.get("current_position", ""))
                delta = f"+{opp.get('monthly_delta', 0):,}"
                pdf.cell(col_w[0], 7, label, border=1, new_x="RIGHT", new_y="TOP")
                pdf.cell(col_w[1], 7, pos, border=1, align="C", new_x="RIGHT", new_y="TOP")
                pdf.cell(col_w[2], 7, delta, border=1, align="C", new_x="RIGHT", new_y="TOP")
                pdf.ln(7)
    else:
        body("Keine GSC-Daten verfuegbar. Verbinden Sie Google Search Console fuer Traffic-Potenzial-Berechnungen.")

    # ── Page 4: Top 3 Ideas ────────────────────────────────────────────────────
    pdf.add_page()
    h1("Top 3 Content-Ideen")
    divider()

    for idx, idea in enumerate(ideas[:3], 1):
        title = _sanitize_for_pdf(idea.get("title", ""))
        category = _sanitize_for_pdf(idea.get("category", ""))
        score = idea.get("score", "")
        why_now = _sanitize_for_pdf(idea.get("why_now", ""))
        signals = idea.get("signals", {})

        h3(f"{idx}. {title}")
        caption_parts = []
        if category:
            caption_parts.append(f"Kategorie: {category}")
        if score:
            caption_parts.append(f"Score: {score}")
        if caption_parts:
            caption(" | ".join(caption_parts))
        if why_now:
            body(f"Warum jetzt? {why_now}")

        signal_parts = []
        for key, label in [("ga4", "GA4"), ("gsc", "Search Console"), ("rss", "RSS")]:
            if signals.get(key):
                signal_parts.append(f"{label}: {str(signals[key])[:100]}")
        if signal_parts:
            pdf.set_font("Helvetica", style="I", size=9)
            pdf.set_text_color(80, 80, 80)
            for sp in signal_parts:
                pdf.multi_cell(0, 5, _sanitize_for_pdf(f"- {sp}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)

        if idx < min(3, len(ideas)):
            divider()

    # ── Page 5: Editorial Calendar ─────────────────────────────────────────────
    pdf.add_page()
    h1("4-Wochen-Redaktionsplan")
    divider()

    if calendar:
        # Table header
        pdf.set_fill_color(230, 235, 245)
        pdf.set_font("Helvetica", style="B", size=10)
        col_w = [20, 25, 90, 30, 15]
        headers = ["Woche", "Datum", "Titel", "Kategorie", "Score"]
        for header, w in zip(headers, col_w):
            pdf.cell(w, 8, header, border=1, fill=True, new_x="RIGHT", new_y="TOP")
        pdf.ln(8)
        # Table rows
        pdf.set_font("Helvetica", size=9)
        for entry in calendar:
            idea = entry["idea"]
            week_str = str(entry["week"])
            date_str = entry["publish_date"].strftime("%d.%m.")
            title_str = _sanitize_for_pdf(idea.get("title", ""))[:55]
            cat_str = _sanitize_for_pdf(idea.get("category", ""))[:20]
            score_str = idea.get("score", "")
            pdf.cell(col_w[0], 7, week_str, border=1, align="C", new_x="RIGHT", new_y="TOP")
            pdf.cell(col_w[1], 7, date_str, border=1, align="C", new_x="RIGHT", new_y="TOP")
            pdf.cell(col_w[2], 7, title_str, border=1, new_x="RIGHT", new_y="TOP")
            pdf.cell(col_w[3], 7, cat_str, border=1, new_x="RIGHT", new_y="TOP")
            pdf.cell(col_w[4], 7, score_str, border=1, align="C", new_x="RIGHT", new_y="TOP")
            pdf.ln(7)
    else:
        body("Kein Redaktionsplan verfugbar.")

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
