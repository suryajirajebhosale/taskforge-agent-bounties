#!/usr/bin/env python3
"""Render docs/business-model.md to a print-ready PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
MD = ROOT / "business-model.md"
PDF = ROOT / "Merit-Business-Model.pdf"

NAVY = HexColor("#0b1220")
LAVENDER = HexColor("#0179F3")
MUTED = HexColor("#4a5568")
RULE = HexColor("#d0d7e2")
ROW = HexColor("#f4f7fb")


def styles():
    base = getSampleStyleSheet()
    return {
        "cover_kicker": ParagraphStyle(
            "cover_kicker",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=11,
            textColor=LAVENDER,
            tracking=1.2,
            spaceAfter=12,
        ),
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=28,
            leading=34,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=12,
            leading=16,
            textColor=MUTED,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            textColor=NAVY,
            spaceBefore=18,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=13,
            leading=17,
            textColor=LAVENDER,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=base["Heading3"],
            fontName="Times-Bold",
            fontSize=11.5,
            leading=15,
            textColor=NAVY,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            textColor=NAVY,
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=13,
            textColor=NAVY,
            leftIndent=12,
        ),
        "th": ParagraphStyle(
            "th",
            parent=base["Normal"],
            fontName="Times-Bold",
            fontSize=8,
            leading=11,
            textColor=white,
        ),
        "td": ParagraphStyle(
            "td",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=8,
            leading=11,
            textColor=NAVY,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Times-Italic",
            fontSize=8,
            textColor=MUTED,
        ),
        "pre": ParagraphStyle(
            "pre",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=NAVY,
        ),
    }


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("**", "")
    )


def inline(text: str) -> str:
    """Minimal markdown: **bold** and `code`."""
    out = []
    i = 0
    s = text
    while i < len(s):
        if s.startswith("**", i):
            j = s.find("**", i + 2)
            if j != -1:
                out.append(f"<b>{esc(s[i + 2 : j])}</b>")
                i = j + 2
                continue
        if s[i] == "`":
            j = s.find("`", i + 1)
            if j != -1:
                out.append(f"<font face='Courier' size='8'>{esc(s[i + 1 : j])}</font>")
                i = j + 1
                continue
        j = i + 1
        while j < len(s) and s[j] not in "*`":
            j += 1
        # allow single * later
        chunk = s[i:j]
        if "*" in chunk and not chunk.startswith("*"):
            pass
        out.append(esc(chunk).replace("\n", " "))
        i = j
    return "".join(out)


def parse_table(rows: list[str], st) -> Table:
    parsed = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        parsed.append(cells)
    header, body = parsed[0], parsed[2:]  # skip |---|
    data = [[Paragraph(inline(c), st["th"]) for c in header]]
    for r in body:
        data.append([Paragraph(inline(c), st["td"]) for c in r])
    colw = 7.2 * inch / max(len(header), 1)
    t = Table(data, colWidths=[colw] * len(header), repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LAVENDER),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("BACKGROUND", (0, 1), (-1, -1), ROW),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, RULE),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.setFont("Times-Italic", 8)
    canvas.drawString(0.85 * inch, 0.5 * inch, "Merit — Business Model  ·  Confidential")
    canvas.drawRightString(7.65 * inch, 0.5 * inch, f"{doc.page}")
    canvas.setStrokeColor(RULE)
    canvas.line(0.85 * inch, 0.65 * inch, 7.65 * inch, 0.65 * inch)
    canvas.restoreState()


def build():
    st = styles()
    story: list = []
    lines = MD.read_text().splitlines()

    # Cover from first heading block
    story.append(Spacer(1, 1.6 * inch))
    story.append(Paragraph("TASKFORGE  /  MERIT", st["cover_kicker"]))
    story.append(Paragraph("Business Model", st["cover_title"]))
    story.append(
        Paragraph(
            "Store, meter, and referee for productized agents — "
            "how Merit makes money from companies and builders.",
            st["cover_sub"],
        )
    )
    story.append(Paragraph("20 August 2026  ·  Internal strategy  ·  Catalog / Run / Hire + attested harness", st["cover_sub"]))
    story.append(PageBreak())

    i = 0
    # skip title lines already used
    while i < len(lines) and not lines[i].startswith("## "):
        i += 1

    bullets: list[str] = []
    table_buf: list[str] = []

    def flush_bullets():
        nonlocal bullets
        if not bullets:
            return
        items = [ListItem(Paragraph(inline(b), st["bullet"]), leftIndent=8) for b in bullets]
        story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=18, spaceAfter=8))
        bullets = []

    def flush_table():
        nonlocal table_buf
        if not table_buf:
            return
        story.append(parse_table(table_buf, st))
        story.append(Spacer(1, 8))
        table_buf = []

    while i < len(lines):
        line = lines[i]
        if line.startswith("|") and "|" in line[1:]:
            flush_bullets()
            table_buf.append(line)
            i += 1
            continue
        flush_table()

        if line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(inline(line[3:]), st["h1"]))
        elif line.startswith("### "):
            flush_bullets()
            story.append(Paragraph(inline(line[4:]), st["h2"]))
        elif line.startswith("#### "):
            flush_bullets()
            story.append(Paragraph(inline(line[5:]), st["h3"]))
        elif line.startswith("---"):
            flush_bullets()
        elif line.startswith("- "):
            bullets.append(line[2:])
        elif line.startswith("```"):
            flush_bullets()
            i += 1
            block = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            story.append(Preformatted("\n".join(block), st["pre"]))
        elif line.strip() == "":
            flush_bullets()
        elif line.startswith("# "):
            pass
        else:
            flush_bullets()
            story.append(Paragraph(inline(line), st["body"]))
        i += 1

    flush_table()
    flush_bullets()

    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.85 * inch,
        title="Merit Business Model",
        author="TaskForge / Merit",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Wrote {PDF}")


if __name__ == "__main__":
    build()
