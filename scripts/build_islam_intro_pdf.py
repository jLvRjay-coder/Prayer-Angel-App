"""Build the public introduction PDF from the reader's canonical Markdown.

Development dependency: reportlab. Not imported by the deployed application.
"""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]


def build():
    font_root = Path("/usr/share/fonts/truetype/dejavu")
    for name, filename in (("Body", "DejaVuSans.ttf"), ("BodyBold", "DejaVuSans-Bold.ttf"),
                           ("TitleSerif", "DejaVuSerif.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(font_root / filename)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyBold", italic="Body", boldItalic="BodyBold")
    ink = colors.HexColor("#17283b")
    gold = colors.HexColor("#846239")
    line = colors.HexColor("#dedbd3")
    styles = getSampleStyleSheet()
    body = ParagraphStyle("ReaderBody", fontName="Body", fontSize=10, leading=15.5,
                          textColor=ink, spaceAfter=10)
    heading = ParagraphStyle("ReaderHeading", parent=body, fontName="TitleSerif", fontSize=17,
                             leading=21, spaceBefore=17, spaceAfter=10, keepWithNext=True)
    title = ParagraphStyle("ReaderTitle", parent=heading, fontSize=29, leading=34, spaceAfter=18)
    small = ParagraphStyle("ReaderSmall", parent=body, fontSize=8.3, leading=12.3)
    cell = ParagraphStyle("ReaderCell", parent=body, fontSize=8.4, leading=12, spaceAfter=0)
    head_cell = ParagraphStyle("ReaderHeaderCell", parent=cell, fontName="BodyBold", textColor=colors.white)

    def inline(text):
        text = escape(text)
        text = re.sub(r"\[([^\]]+)\]\((https://[^\s)]+)\)", r'<a href="\2" color="#846239">\1</a>', text)
        def citation(match):
            return "[" + "; ".join('<a href="#source-' + code + '" color="#846239">' + code + '</a>'
                                     for code in match[1].split("; ")) + "]"
        text = re.sub(r"\[([A-Z]+\d+(?:; [A-Z]+\d+)*)\]", citation, text)
        return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    story = [Paragraph("THE BELIEF FILES · 00 · START HERE", ParagraphStyle("Eyebrow", parent=small, textColor=gold)), Spacer(1, 8)]
    lines = (ROOT / "belief_case_islam_00.md").read_text().splitlines()
    i = 0
    in_sources = False
    while i < len(lines):
        text = lines[i].strip()
        if not text:
            i += 1
            continue
        if text.startswith("# "):
            story.append(Paragraph(inline(text[2:]), title))
        elif text.startswith("## "):
            if text == "## Sources and reading":
                story.append(PageBreak())
                in_sources = True
            story.append(Paragraph(inline(text[3:]), heading))
        elif text.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                values = [v.strip() for v in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", v) for v in values):
                    rows.append(values)
                i += 1
            contents = [[Paragraph(inline(v), head_cell if r == 0 else cell) for v in row] for r, row in enumerate(rows)]
            table = Table(contents, colWidths=[(468 / len(rows[0]))] * len(rows[0]), repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ink),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f4f0e7")),
                ("GRID", (0, 0), (-1, -1), .45, line),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]))
            story.extend((table, Spacer(1, 14)))
            continue
        else:
            paragraph = [text]
            while i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith(("#", "|")) and not re.match(r"^\d+\. ", lines[i + 1]):
                i += 1
                paragraph.append(lines[i].strip())
            anchor = re.match(r"^\*\*([A-Z]+\d+)\*\*", text) if in_sources else None
            prefix = '<a name="source-' + anchor[1] + '"/>' if anchor else ''
            story.append(Paragraph(prefix + inline(" ".join(paragraph)), small if in_sources else body))
        i += 1

    def page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.line(72, 744, 540, 744)
        canvas.setFont("Body", 8)
        canvas.setFillColor(gold)
        canvas.drawString(72, 757, "BEYOND THE MESSAGE")
        canvas.setFillColor(ink)
        canvas.drawString(72, 39, "Islam & biblical Christianity · The Belief Files")
        canvas.drawRightString(540, 39, str(doc.page))
        canvas.restoreState()

    output = ROOT / "belief_case_islam_00.pdf"
    document = SimpleDocTemplate(str(output), pagesize=(612, 792), leftMargin=72, rightMargin=72,
                                 topMargin=66, bottomMargin=65, title="Islam & biblical Christianity | Start Here",
                                 author="Beyond the Message")
    document.build(story, onFirstPage=page, onLaterPages=page)
    print(output.name)


if __name__ == "__main__":
    build()
