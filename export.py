"""Article export utilities: Markdown and PDF."""

from __future__ import annotations

import re
import unicodedata
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


def article_to_markdown(article: dict, social_snippets: dict | None = None) -> str:
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

    return "\n".join(parts)


def article_to_pdf(article: dict, social_snippets: dict | None = None) -> bytes:
    """Return the article as PDF bytes using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    title = article.get("title", "")
    lead = article.get("lead", "")
    sections = article.get("sections", [])
    meta_description = article.get("meta_description", "")

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
        heading = section.get("heading", "")
        content = section.get("content", "")
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

        linkedin = social_snippets.get("linkedin", "")
        twitter = social_snippets.get("twitter", "") or social_snippets.get("x", "")
        newsletter = social_snippets.get("newsletter_teaser", "")

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

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
