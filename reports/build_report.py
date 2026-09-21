#!/usr/bin/env python3
"""Build the public SplitSense technical report PDF with ReportLab."""

from pathlib import Path
import re

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Circle, Drawing, Line, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "SPLITSENSE_D2_REPORT.md"
OUTPUT = HERE / "SPLITSENSE_D2_REPORT.pdf"


def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def success_chart():
    drawing = Drawing(500, 245)
    chart = VerticalBarChart()
    chart.x, chart.y, chart.width, chart.height = 60, 48, 400, 155
    chart.data = [(0, 0), (20.3125, 21.875), (21.875, 37.5)]
    chart.categoryAxis.categoryNames = ["Main", "Independent replication"]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.valueAxis.valueMin, chart.valueAxis.valueMax, chart.valueAxis.valueStep = 0, 50, 10
    chart.valueAxis.labelTextFormat = "%d%%"
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 8
    chart.bars[0].fillColor = colors.HexColor("#8A94A6")
    chart.bars[1].fillColor = colors.HexColor("#D79A3B")
    chart.bars[2].fillColor = colors.HexColor("#177E89")
    chart.barLabels.nudge = 7
    chart.barLabels.fontName = "Helvetica-Bold"
    chart.barLabels.fontSize = 7
    chart.barLabelFormat = "%.1f%%"
    drawing.add(chart)
    drawing.add(String(250, 226, "Strict end-to-end success", textAnchor="middle", fontName="Helvetica-Bold", fontSize=12))
    for x, color, label in [(85, "#8A94A6", "N0 Direct"), (215, "#D79A3B", "N1 Calculator"), (350, "#177E89", "N2 Declarative")]:
        drawing.add(Line(x, 18, x + 16, 18, strokeColor=colors.HexColor(color), strokeWidth=7))
        drawing.add(String(x + 22, 14, label, fontName="Helvetica", fontSize=8))
    return drawing


def interval_chart():
    drawing = Drawing(500, 170)
    left, right = 140, 465
    def scale(value): return left + (value + 10) / 70 * (right - left)
    drawing.add(String(250, 152, "N2 minus N0 (percentage points)", textAnchor="middle", fontName="Helvetica-Bold", fontSize=12))
    drawing.add(Line(scale(0), 35, scale(0), 130, strokeColor=colors.grey, strokeDashArray=[4, 3]))
    for tick in range(-10, 61, 10):
        x = scale(tick)
        drawing.add(Line(x, 31, x, 36, strokeColor=colors.black))
        drawing.add(String(x, 17, str(tick), textAnchor="middle", fontName="Helvetica", fontSize=7))
    drawing.add(Line(left, 35, right, 35, strokeColor=colors.black))
    for label, estimate, low, high, y in [("Main", 21.875, 12.5, 32.8125, 110), ("Replication", 37.5, 18.75, 56.25, 70)]:
        drawing.add(String(125, y - 3, label, textAnchor="end", fontName="Helvetica", fontSize=9))
        drawing.add(Line(scale(low), y, scale(high), y, strokeColor=colors.HexColor("#177E89"), strokeWidth=4))
        drawing.add(Circle(scale(estimate), y, 5, fillColor=colors.HexColor("#D79A3B"), strokeColor=colors.black))
        drawing.add(String(min(scale(high) + 7, 420), y - 3, f"{estimate:.2f} [{low:.2f}, {high:.2f}]", fontName="Helvetica", fontSize=7))
    return drawing


def page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#5D6673"))
    canvas.drawString(18 * mm, 11 * mm, "SplitSense-Bench Diagnostic-D2 public technical report")
    canvas.drawRightString(192 * mm, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    styles = getSampleStyleSheet()
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.1, leading=12.4, spaceAfter=5.5, alignment=TA_LEFT)
    abstract = ParagraphStyle("Abstract", parent=body, fontSize=8.7, leading=11.7, leftIndent=8 * mm, rightIndent=8 * mm)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=17, textColor=colors.HexColor("#153B50"), spaceBefore=8, spaceAfter=5)
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=23, leading=28, textColor=colors.HexColor("#153B50"), alignment=TA_CENTER, spaceAfter=15)
    subtitle = ParagraphStyle("Subtitle", parent=body, fontName="Helvetica-Oblique", alignment=TA_CENTER, fontSize=10, textColor=colors.HexColor("#5D6673"), spaceAfter=18)
    quote = ParagraphStyle("Quote", parent=body, leftIndent=10 * mm, rightIndent=10 * mm, borderColor=colors.HexColor("#D79A3B"), borderWidth=0, borderPadding=5, backColor=colors.HexColor("#F8F4EA"))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="SplitSense-Bench: Separating Data-Science Reasoning from Numerical Execution", author="Ouyang Kuang")
    lines = SOURCE.read_text().splitlines()
    story = []
    paragraph = []
    in_abstract = False

    def flush():
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph)
            style = abstract if in_abstract else quote if text.startswith("&gt;") else body
            story.append(Paragraph(inline(text), style))
            paragraph = []

    for line in lines:
        if line.startswith("# "):
            flush(); story.append(Spacer(1, 28)); story.append(Paragraph(inline(line[2:]), title))
        elif line.startswith("**Public technical report"):
            flush(); story.append(Paragraph(inline(line), subtitle))
            story.append(Spacer(1, 22))
            story.append(Paragraph("<b>Frozen Diagnostic-D2 result</b><br/><br/>Main N2 - N0: <b>+21.88 percentage points</b>, 95% CI [12.50, 32.81]<br/><br/>Independent replication: <b>+37.50 percentage points</b>, 95% CI [18.75, 56.25]", quote))
            story.append(Spacer(1, 28))
            story.append(Paragraph("A controlled study of validation-evidence semantics, bounded numerical execution, and strict complete delivery.", subtitle))
            story.append(PageBreak())
        elif line.startswith("## "):
            flush()
            heading = line[3:]
            if heading.startswith(("8. ", "14. ")):
                story.append(PageBreak())
            in_abstract = heading == "Abstract"
            story.append(Paragraph(inline(heading), h1))
        elif line.startswith("![Strict success rates]"):
            flush(); story.append(KeepTogether([success_chart(), Paragraph("Figure 1. Strict complete-delivery rates. Labels show percentages; exact counts are reported in text.", abstract)]))
        elif line.startswith("![N2 minus N0 intervals]"):
            flush(); story.append(KeepTogether([interval_chart(), Paragraph("Figure 2. Paired-world mean differences and frozen percentile bootstrap 95% intervals.", abstract)]))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line)
    flush()
    doc.build(story, onFirstPage=page, onLaterPages=page)


if __name__ == "__main__":
    build()
