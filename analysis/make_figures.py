#!/usr/bin/env python3
"""Generate publication SVGs from the public frozen endpoint records."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
COLORS = {"N0_DIRECT_OUTPUT": "#8A94A6", "N1_CALCULATOR": "#D79A3B", "N2_DECLARATIVE_EXECUTION": "#177E89"}
LABELS = {"N0_DIRECT_OUTPUT": "N0 Direct", "N1_CALCULATOR": "N1 Calculator", "N2_DECLARATIVE_EXECUTION": "N2 Declarative"}


def load(name):
    with (ROOT / "public_results" / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def svg_start(width, height, title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{title}</text>']


def success_figure():
    batches = [("Main", load("public_results.csv")), ("Independent replication", load("replication_results.csv"))]
    width, height = 900, 500
    lines = svg_start(width, height, "Strict end-to-end success by execution mode")
    left, top, chart_h = 80, 70, 320
    for tick in range(0, 51, 10):
        y = top + chart_h - tick / 50 * chart_h
        lines += [f'<line x1="{left}" y1="{y}" x2="850" y2="{y}" stroke="#D8DDE5"/>', f'<text x="68" y="{y+5}" text-anchor="end" font-family="Arial" font-size="12">{tick}%</text>']
    centers = [280, 650]
    for (batch, rows), center in zip(batches, centers):
        for index, mode in enumerate(COLORS):
            selected = [row for row in rows if row["execution_mode"] == mode]
            successes = sum(int(row["end_to_end_success_J_D2"]) for row in selected)
            percent = 100 * successes / len(selected)
            x = center - 105 + index * 78
            h = percent / 50 * chart_h
            y = top + chart_h - h
            lines += [f'<rect x="{x}" y="{y}" width="58" height="{h}" rx="3" fill="{COLORS[mode]}"/>', f'<text x="{x+29}" y="{max(y-8,55)}" text-anchor="middle" font-family="Arial" font-size="12" font-weight="700">{successes}/{len(selected)}</text>']
        lines.append(f'<text x="{center-27}" y="420" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">{batch}</text>')
    for index, mode in enumerate(COLORS):
        x = 175 + index * 220
        lines += [f'<rect x="{x}" y="454" width="16" height="16" fill="{COLORS[mode]}"/>', f'<text x="{x+23}" y="467" font-family="Arial" font-size="13">{LABELS[mode]}</text>']
    lines.append('</svg>')
    (OUT / "figure1_success_rates.svg").write_text("\n".join(lines) + "\n")


def interval_figure():
    values = [("Main", 21.875, 12.5, 32.8125), ("Independent replication", 37.5, 18.75, 56.25)]
    width, height = 1050, 330
    lines = svg_start(width, height, "N2 minus N0: paired-world percentage-point difference")
    left, right, top, bottom = 190, 900, 70, 240
    scale = lambda v: left + (v + 10) / 70 * (right - left)
    zero = scale(0)
    lines.append(f'<line x1="{zero}" y1="{top}" x2="{zero}" y2="{bottom}" stroke="#555" stroke-dasharray="5 4"/>')
    for tick in range(-10, 61, 10):
        x = scale(tick)
        lines += [f'<line x1="{x}" y1="{bottom}" x2="{x}" y2="{bottom+6}" stroke="#333"/>', f'<text x="{x}" y="{bottom+24}" text-anchor="middle" font-family="Arial" font-size="12">{tick}</text>']
    lines.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#333"/>')
    for idx, (label, estimate, low, high) in enumerate(values):
        y = 115 + idx * 80
        lines += [f'<text x="175" y="{y+5}" text-anchor="end" font-family="Arial" font-size="14">{label}</text>', f'<line x1="{scale(low)}" y1="{y}" x2="{scale(high)}" y2="{y}" stroke="#177E89" stroke-width="5"/>', f'<circle cx="{scale(estimate)}" cy="{y}" r="8" fill="#D79A3B" stroke="#333"/>', f'<text x="{scale(high)+12}" y="{y+5}" font-family="Arial" font-size="12">{estimate:.2f} [{low:.2f}, {high:.2f}]</text>']
    lines.append('<text x="545" y="305" text-anchor="middle" font-family="Arial" font-size="13">Percentage points; percentile 95% bootstrap interval over worlds</text>')
    lines.append('</svg>')
    (OUT / "figure2_n2_minus_n0.svg").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    success_figure()
    interval_figure()
