# app/report/render_pdf.py
from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def render_pdf(markdown_text: str, out_path: Path) -> None:
    styles = getSampleStyleSheet()
    story = []

    for raw in markdown_text.splitlines():
        line = raw.strip()

        if not line:
            story.append(Spacer(1, 10))
            continue

        # Escape text so ReportLab Paragraph doesn't choke on &, <, >
        safe = escape(line)

        if line.startswith("# "):
            story.append(Paragraph(f"<b>{escape(line[2:])}</b>", styles["Title"]))
        elif line.startswith("## "):
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"<b>{escape(line[3:])}</b>", styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"• {escape(line[2:])}", styles["Normal"]))
        else:
            story.append(Paragraph(safe, styles["Normal"]))

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=LETTER,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    doc.build(story)
