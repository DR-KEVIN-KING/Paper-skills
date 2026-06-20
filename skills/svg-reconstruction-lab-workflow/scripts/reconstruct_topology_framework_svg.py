#!/usr/bin/env python3
"""High-fidelity SVG reconstruction starter used by svg-reconstruction-lab-workflow.

This is the proven topology-framework example from the reconstruction lab trial.
For a new reference figure, keep the math/QA/rendering utilities and patch the
scene-specific helpers and coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import math
import re
import shutil
import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat

import matplotlib

matplotlib.use("svg")
from matplotlib import rcParams
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure


rcParams.update(
    {
        "svg.fonttype": "path",
        "mathtext.fontset": "stix",
        "font.family": "STIXGeneral",
    }
)


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR
REFERENCE = ROOT / "reference.png"
OUTPUT_NAME = "framework_reconstruction"
SVG_OUT = ROOT / f"{OUTPUT_NAME}.svg"
PNG_OUT = ROOT / f"{OUTPUT_NAME}.png"
SIDE_BY_SIDE = ROOT / f"{OUTPUT_NAME}_side_by_side.png"
DIFF_OUT = ROOT / f"{OUTPUT_NAME}_diff.png"
ROI_SHEET = ROOT / f"{OUTPUT_NAME}_roi_sheet.png"
REPORT = ROOT / "qa_report.md"

W, H = 1693, 929
BLUE = "#123f73"
DASH_BLUE = "#6f8fb0"
LIGHT_BLUE = "#f7fbff"
GREEN = "#356f3b"
SOFT_GREEN = "#4b8a52"
RED = "#c74343"
SOFT_RED = "#d25f5f"
BROWN = "#5a4032"
DASH_BROWN = "#9a8476"
INK = "#161616"
GRAY = "#59636f"
LIGHT_GRAY = "#eef2f5"
MID_GRAY = "#8a939b"
VIEWBOX_RE = re.compile(r'viewBox="([^"]+)"')
MATH_CACHE: dict[tuple[str, float, str], tuple[str, float, float]] = {}


def configure_outputs(reference: Path, out_dir: Path, name: str) -> None:
    """Set global IO paths while keeping the original reference untouched."""
    global ROOT, REFERENCE, OUTPUT_NAME, SVG_OUT, PNG_OUT, SIDE_BY_SIDE, DIFF_OUT, ROI_SHEET, REPORT

    ROOT = out_dir.resolve()
    ROOT.mkdir(parents=True, exist_ok=True)
    REFERENCE = reference.resolve()
    OUTPUT_NAME = name
    SVG_OUT = ROOT / f"{OUTPUT_NAME}.svg"
    PNG_OUT = ROOT / f"{OUTPUT_NAME}.png"
    SIDE_BY_SIDE = ROOT / f"{OUTPUT_NAME}_side_by_side.png"
    DIFF_OUT = ROOT / f"{OUTPUT_NAME}_diff.png"
    ROI_SHEET = ROOT / f"{OUTPUT_NAME}_roi_sheet.png"
    REPORT = ROOT / "qa_report.md"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def math_svg_asset(tex: str, size: float, color: str) -> tuple[str, float, float]:
    key = (tex, size, color)
    if key in MATH_CACHE:
        return MATH_CACHE[key]

    fig = Figure(figsize=(0.01, 0.01), dpi=100)
    fig.patch.set_alpha(0)
    FigureCanvasSVG(fig)
    fig.text(
        0,
        0,
        f"${tex}$",
        fontsize=size,
        color=color,
        ha="left",
        va="baseline",
    )
    buf = BytesIO()
    fig.savefig(
        buf,
        format="svg",
        transparent=True,
        bbox_inches="tight",
        pad_inches=0.008,
        metadata={"Date": None},
    )
    raw = buf.getvalue().decode("utf-8")
    match = VIEWBOX_RE.search(raw)
    if not match:
        raise RuntimeError(f"Matplotlib SVG has no viewBox for formula: {tex}")
    _, _, width, height = [float(v) for v in match.group(1).split()]
    start = raw.find('<g id="figure_1">')
    end = raw.rfind("</g>")
    if start < 0 or end < 0:
        raise RuntimeError(f"Matplotlib SVG has no figure group for formula: {tex}")
    fragment = raw[start : end + 4]
    prefix = f"m{hashlib.sha1('|'.join(map(str, key)).encode('utf-8')).hexdigest()[:10]}_"
    ids = sorted(set(re.findall(r'id="([^"]+)"', fragment)), key=len, reverse=True)
    for old in ids:
        new = f"{prefix}{old}"
        fragment = fragment.replace(f'id="{old}"', f'id="{new}"')
        fragment = fragment.replace(f'#{old}', f'#{new}')
    MATH_CACHE[key] = (fragment, width, height)
    return MATH_CACHE[key]


class SVG:
    def __init__(self) -> None:
        self.parts: list[str] = []

    def add(self, raw: str) -> None:
        self.parts.append(raw)

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rx: float = 0,
        fill: str = "none",
        stroke: str = INK,
        sw: float = 1.5,
        dash: str | None = None,
        opacity: float | None = None,
        cls: str | None = None,
    ) -> None:
        attrs = [
            f'x="{x:g}"',
            f'y="{y:g}"',
            f'width="{w:g}"',
            f'height="{h:g}"',
            f'rx="{rx:g}"',
            f'fill="{fill}"',
            f'stroke="{stroke}"',
            f'stroke-width="{sw:g}"',
        ]
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity:g}"')
        if cls:
            attrs.append(f'class="{cls}"')
        self.add(f"<rect {' '.join(attrs)}/>")

    def circle(self, cx: float, cy: float, r: float, fill: str, stroke: str = INK, sw: float = 1.2) -> None:
        self.add(
            f'<circle cx="{cx:g}" cy="{cy:g}" r="{r:g}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw:g}"/>'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        stroke: str = INK,
        sw: float = 2,
        dash: str | None = None,
        marker: str | None = None,
    ) -> None:
        attrs = [
            f'x1="{x1:g}"',
            f'y1="{y1:g}"',
            f'x2="{x2:g}"',
            f'y2="{y2:g}"',
            f'stroke="{stroke}"',
            f'stroke-width="{sw:g}"',
            'fill="none"',
        ]
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if marker:
            attrs.append(f'marker-end="url(#{marker})"')
        self.add(f"<line {' '.join(attrs)}/>")

    def path(
        self,
        d: str,
        fill: str = "none",
        stroke: str = INK,
        sw: float = 2,
        dash: str | None = None,
        marker: str | None = None,
        opacity: float | None = None,
    ) -> None:
        attrs = [f'd="{d}"', f'fill="{fill}"', f'stroke="{stroke}"', f'stroke-width="{sw:g}"']
        if dash:
            attrs.append(f'stroke-dasharray="{dash}"')
        if marker:
            attrs.append(f'marker-end="url(#{marker})"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity:g}"')
        self.add(f"<path {' '.join(attrs)}/>")

    def polygon(self, points: list[tuple[float, float]], fill: str, stroke: str = INK, sw: float = 1.5) -> None:
        pts = " ".join(f"{x:g},{y:g}" for x, y in points)
        self.add(f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw:g}"/>')

    def text(
        self,
        x: float,
        y: float,
        value: str,
        size: float = 16,
        fill: str = INK,
        weight: str = "400",
        anchor: str = "middle",
        italic: bool = False,
        family: str = "Arial, Helvetica, sans-serif",
    ) -> None:
        style = "font-style:italic;" if italic else ""
        self.add(
            f'<text x="{x:g}" y="{y:g}" fill="{fill}" font-size="{size:g}" '
            f'font-weight="{weight}" text-anchor="{anchor}" '
            f'font-family="{family}" style="{style}">{esc(value)}</text>'
        )

    def math(
        self,
        x: float,
        y: float,
        tex: str,
        max_w: float,
        max_h: float,
        size: float = 20,
        fill: str = INK,
        anchor: str = "middle",
    ) -> None:
        fragment, natural_w, natural_h = math_svg_asset(tex, size, fill)
        scale = min(max_w / natural_w, max_h / natural_h)
        width = natural_w * scale
        height = natural_h * scale
        left = x if anchor == "start" else x - width / 2
        top = y - height / 2
        self.add(
            f'<g transform="translate({left:g} {top:g}) scale({scale:g})">{fragment}</g>'
        )

    def multi_text(
        self,
        x: float,
        y: float,
        lines: list[str],
        size: float = 16,
        fill: str = INK,
        weight: str = "400",
        anchor: str = "middle",
        line_gap: float = 22,
    ) -> None:
        for i, line in enumerate(lines):
            self.text(x, y + i * line_gap, line, size=size, fill=fill, weight=weight, anchor=anchor)

    def group_start(self, transform: str = "") -> None:
        self.add(f'<g transform="{transform}">')

    def group_end(self) -> None:
        self.add("</g>")

    def render(self) -> str:
        body = "\n".join(self.parts)
        return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <marker id="arrowBlue" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,4 L0,8 Z" fill="{BLUE}"/>
  </marker>
  <marker id="arrowGreen" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,4 L0,8 Z" fill="{GREEN}"/>
  </marker>
  <marker id="arrowRed" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,4 L0,8 Z" fill="{RED}"/>
  </marker>
  <filter id="softShadow" x="-10%" y="-10%" width="120%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#2d3b4a" flood-opacity="0.12"/>
  </filter>
</defs>
<style>
  .card {{ filter:url(#softShadow); }}
  .formula {{ font-family: Georgia, 'Times New Roman', serif; font-style: italic; }}
  .label {{ font-family: Arial, Helvetica, sans-serif; }}
</style>
<rect x="0" y="0" width="{W}" height="{H}" fill="white"/>
{body}
</svg>
'''


def draw_number(svg: SVG, x: float, y: float, n: int) -> None:
    svg.circle(x, y, 15, "#315f8d", stroke="#214565", sw=1.2)
    svg.text(x, y + 6, str(n), size=21, fill="white", weight="700")


def draw_card(svg: SVG, x: float, y: float, w: float, h: float, n: int, title: list[str], formula_tex: str) -> None:
    svg.rect(x, y, w, h, rx=10, fill="#fbfdff", stroke=BLUE, sw=1.35, cls="card")
    draw_number(svg, x + 29, y + 30, n)
    svg.multi_text(x + w / 2 + 12, y + 34, title, size=17, weight="700", line_gap=22)
    svg.rect(x + 13, y + h - 53, w - 26, 41, rx=5, fill="#fbfbfb", stroke="#677787", sw=1.0)
    svg.math(x + w / 2, y + h - 31, formula_tex, max_w=w - 56, max_h=26, size=24, fill=INK)


def network_icon(
    svg: SVG,
    cx: float,
    cy: float,
    scale: float = 1,
    color: str = "#87a48d",
    stroke: str = INK,
    line_weight: float = 1.1,
) -> None:
    pts = [
        (-37, -6),
        (-10, -32),
        (27, -11),
        (-3, 16),
        (-31, 26),
        (31, 28),
    ]
    pts = [(cx + x * scale, cy + y * scale) for x, y in pts]
    edges = [(0, 1), (1, 2), (2, 5), (5, 3), (3, 0), (0, 4), (4, 3), (1, 3), (2, 3)]
    for a, b in edges:
        svg.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], stroke=stroke, sw=line_weight * scale)
    for px, py in pts:
        svg.circle(px, py, 6.2 * scale, color, stroke=stroke, sw=line_weight * scale)


def topology_graph_icon(
    svg: SVG,
    cx: float,
    cy: float,
    scale: float = 1,
    node_fill: str = "#d7dce1",
    stroke: str = INK,
    sw: float = 1.25,
) -> None:
    pts = [
        (-36, -6),
        (-8, -33),
        (35, -10),
        (0, 15),
        (-28, 31),
        (32, 31),
    ]
    pts = [(cx + x * scale, cy + y * scale) for x, y in pts]
    edges = [(0, 1), (1, 2), (2, 5), (5, 3), (3, 4), (4, 0), (0, 3), (1, 3), (2, 3)]
    for a, b in edges:
        svg.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], stroke=stroke, sw=sw * scale)
    for px, py in pts:
        svg.circle(px, py, 6.6 * scale, node_fill, stroke=stroke, sw=sw * scale)


def trajectory_graph_icon(
    svg: SVG,
    cx: float,
    cy: float,
    scale: float = 1,
    node_fill: str = "#6d9b75",
    stroke: str = INK,
    sw: float = 1.15,
) -> None:
    pts = [
        (-34, -2),
        (-10, -28),
        (24, -16),
        (0, 9),
        (-26, 25),
        (29, 26),
    ]
    pts = [(cx + x * scale, cy + y * scale) for x, y in pts]
    edges = [(0, 1), (1, 2), (2, 5), (5, 3), (3, 4), (4, 0), (0, 3), (1, 3), (2, 3)]
    for a, b in edges:
        svg.line(pts[a][0], pts[a][1], pts[b][0], pts[b][1], stroke=stroke, sw=sw * scale)
    for px, py in pts:
        svg.circle(px, py, 5.4 * scale, node_fill, stroke=stroke, sw=sw * scale)


def grid_icon(svg: SVG, x: float, y: float, cell: float = 14, gap: float = 4) -> None:
    vals = [
        ["#d7dce1", "#b6bec7", "#c7ced5", "#7e8b96"],
        ["#b6bfc8", "#929fa9", "#d7dce1", "#a9b3bd"],
        ["#c4cbd2", "#84919c", "#dfe3e7", "#8d9aa5"],
        ["#6f7c88", "#9da8b2", "#c2cbd3", "#73808c"],
    ]
    for r in range(4):
        for c in range(4):
            svg.rect(x + c * (cell + gap), y + r * (cell + gap), cell, cell, rx=0, fill=vals[r][c], stroke="none", sw=0)


def memory_icon(svg: SVG, x: float, y: float) -> None:
    fills = ["#ffffff", "#ffffff", "#ffffff", "#eef1f4", "#d9dee3", "#cbd2d8"]
    for i, fill in enumerate(fills):
        svg.rect(x + i * 26, y, 25, 34, rx=0, fill=fill, stroke=INK, sw=1.5)
    svg.rect(x, y, 156, 34, rx=1, fill="none", stroke=INK, sw=1.5)


def scales_icon(svg: SVG, x: float, y: float, scale: float = 1) -> None:
    def sx(v: float) -> float:
        return x + v * scale

    def sy(v: float) -> float:
        return y + v * scale

    svg.line(x, sy(-46), x, sy(30), stroke=INK, sw=3.4 * scale)
    svg.line(sx(-42), sy(-35), sx(42), sy(-35), stroke=INK, sw=3.4 * scale)
    svg.line(sx(-34), sy(-31), sx(-50), sy(8), stroke=INK, sw=1.3 * scale)
    svg.line(sx(-34), sy(-31), sx(-18), sy(8), stroke=INK, sw=1.3 * scale)
    svg.path(f"M{sx(-50)},{sy(8)} Q{sx(-34)},{sy(22)} {sx(-18)},{sy(8)}", fill="#a8c8ad", stroke=INK, sw=1.1 * scale)
    svg.line(sx(34), sy(-31), sx(18), sy(8), stroke=INK, sw=1.3 * scale)
    svg.line(sx(34), sy(-31), sx(50), sy(8), stroke=INK, sw=1.3 * scale)
    svg.path(f"M{sx(18)},{sy(8)} Q{sx(34)},{sy(22)} {sx(50)},{sy(8)}", fill="#e4aaa8", stroke=INK, sw=1.1 * scale)
    svg.line(sx(-25), sy(31), sx(25), sy(31), stroke=INK, sw=3.4 * scale)
    svg.circle(x, sy(-46), 3.4 * scale, INK, stroke=INK, sw=0.8 * scale)


def shield_icon(svg: SVG, x: float, y: float, scale: float = 1) -> None:
    def sx(v: float) -> float:
        return x + v * scale

    def sy(v: float) -> float:
        return y + v * scale

    d = f"M{x},{sy(-45)} L{sx(23)},{sy(-28)} L{sx(21)},{sy(12)} Q{x},{sy(39)} {sx(-21)},{sy(12)} L{sx(-23)},{sy(-28)} Z"
    svg.path(d, fill="#f8fbff", stroke="#3c4650", sw=2.4 * scale)
    svg.path(f"M{sx(-10)},{sy(-4)} L{sx(-1)},{sy(7)} L{sx(15)},{sy(-14)}", fill="none", stroke="#3c4650", sw=2.4 * scale)


def magnifier_icon(svg: SVG, x: float, y: float, scale: float = 1) -> None:
    svg.circle(x, y, 31 * scale, "none", stroke=INK, sw=3.4 * scale)
    svg.line(x + 22 * scale, y + 22 * scale, x + 53 * scale, y + 53 * scale, stroke=INK, sw=6 * scale)
    for i, h in enumerate([18, 32, 44]):
        svg.rect(x + (-17 + i * 12) * scale, y + (19 - h) * scale, 7 * scale, h * scale, rx=0, fill="#687581", stroke="none", sw=0)


def heat_grid(svg: SVG, x: float, y: float, red: bool = False, cell: float = 15, gap: float = 3, accent: float = 1.0) -> None:
    if red:
        colors = ["#d7dbe0", "#dee2e6", "#cfd5da", "#efd2d2", "#da9695"] if accent >= 1 else ["#d9dde2", "#e1e5e8", "#d2d8dd", "#efdada", "#e3b8b7"]
    else:
        colors = ["#d9dee3"] * 5
    for r in range(4):
        for c in range(3):
            fill = colors[min(len(colors) - 1, r + c - 1)] if red and c == 2 else "#d8dde2"
            svg.rect(x + c * (cell + gap), y + r * (cell + gap), cell, cell, fill=fill, stroke="none", sw=0)


def gear_icon(svg: SVG, x: float, y: float, r1: float = 28, r2: float = 38) -> None:
    pts = []
    for i in range(16):
        ang = -math.pi / 2 + i * math.pi / 8
        r = r2 if i % 2 == 0 else r1
        pts.append((x + r * math.cos(ang), y + r * math.sin(ang)))
    svg.polygon(pts, fill="#9ba1a6", stroke=INK, sw=1.35)
    svg.circle(x, y, 18.5, "white", stroke=INK, sw=1.35)


def gear_people_icon(svg: SVG, x: float, y: float) -> None:
    gear_icon(svg, x, y - 6, r1=27, r2=37)
    for dx in [-42, 0, 42]:
        head_y = y + 38
        svg.circle(x + dx, head_y, 5.9, "#555b61", stroke=INK, sw=0.75)
        svg.path(
            f"M{x+dx-12},{head_y+22} Q{x+dx},{head_y+7} {x+dx+12},{head_y+22} Z",
            fill="#50565c",
            stroke=INK,
            sw=0.75,
        )


def global_model_icon(svg: SVG, cx: float, cy: float) -> None:
    topology_graph_icon(svg, cx, cy - 6, 0.79, node_fill="#d8dde2", sw=1.13)
    svg.path(f"M{cx-33},{cy+42} Q{cx},{cy+58} {cx+33},{cy+42}", fill="none", stroke=INK, sw=1.25)
    svg.path(f"M{cx-22},{cy+31} Q{cx},{cy+42} {cx+22},{cy+31}", fill="none", stroke=INK, sw=1.25)


def people_icon(svg: SVG, x: float, y: float) -> None:
    for dx in [-40, 0, 40]:
        svg.circle(x + dx, y, 6.4, "#4d5358", stroke=INK, sw=0.9)
        svg.path(f"M{x+dx-13},{y+23} Q{x+dx},{y+6} {x+dx+13},{y+23} Z", fill="#4d5358", stroke=INK, sw=0.9)


def cylinder(svg: SVG, x: float, y: float, w: float = 44, h: float = 54, fill: str = "#f4f5f6") -> None:
    ry = min(8, h * 0.16)
    svg.path(
        f"M{x},{y} C{x},{y-ry} {x+w},{y-ry} {x+w},{y} "
        f"L{x+w},{y+h} C{x+w},{y+h+ry} {x},{y+h+ry} {x},{y+h} Z",
        fill=fill,
        stroke=INK,
        sw=1.25,
    )
    svg.path(f"M{x},{y} C{x},{y+ry} {x+w},{y+ry} {x+w},{y}", fill="none", stroke=INK, sw=1.05)
    for yy in [y + h * 0.28, y + h * 0.55, y + h * 0.82]:
        svg.path(f"M{x},{yy} C{x},{yy+ry} {x+w},{yy+ry} {x+w},{yy}", fill="none", stroke=INK, sw=0.9)


def client_box(svg: SVG, x: float, y: float, w: float, h: float, title: str, color: str, malicious: bool = False) -> None:
    title_color = SOFT_RED if malicious else SOFT_GREEN
    svg.rect(x, y, w, h, rx=9, fill="#fbfffb" if not malicious else "#fffdfd", stroke=title_color, sw=1.2, cls="card")
    svg.text(x + w / 2, y + 32, title, size=18.2, weight="650", fill=title_color)
    node_col = "#76a07d" if not malicious else "#d46a64"
    marker = "arrowGreen" if not malicious else "arrowRed"
    trajectory_graph_icon(svg, x + 61, y + 83, 0.80, node_fill=node_col, stroke=INK, sw=1.05)
    svg.line(x + 113, y + 72, x + 143, y + 72, stroke=title_color, sw=1.85, marker=marker)
    cylinder(svg, x + 155, y + 52, w=38, h=46)
    svg.line(x + 208, y + 72, x + 239, y + 72, stroke=title_color, sw=1.85, marker=marker)
    trajectory_graph_icon(svg, x + w - 58, y + 83, 0.80, node_fill=node_col, stroke=INK, sw=1.05)
    svg.rect(x + 24, y + h - 36, w - 48, 23, rx=3, fill="#fbfbfb", stroke="#596571", sw=0.9)
    svg.text(x + w / 2, y + h - 20, "Local GRIP/GNN training", size=15, weight="700")


def server_icon(svg: SVG, x: float, y: float) -> None:
    for i in range(3):
        yy = y + i * 43
        svg.rect(x, yy, 98, 36, rx=4, fill="#dedede", stroke=INK, sw=2)
        svg.circle(x + 17, yy + 18, 5, "#333", stroke=INK, sw=1)
        svg.circle(x + 34, yy + 18, 5, "#333", stroke=INK, sw=1)
    svg.line(x - 10, y + 129, x + 110, y + 129, stroke=INK, sw=2)


def car_icon(svg: SVG, x: float, y: float, color: str, scale: float = 1) -> None:
    if scale != 1:
        svg.group_start(f"translate({x:g} {y:g}) scale({scale:g})")
        car_icon(svg, 0, 0, color, 1)
        svg.group_end()
        return
    svg.path(
        f"M{x+4},{y+36} L{x+17},{y+17} Q{x+30},{y+4} {x+56},{y+4} "
        f"L{x+82},{y+4} Q{x+96},{y+5} {x+109},{y+24} "
        f"L{x+130},{y+31} Q{x+137},{y+34} {x+140},{y+43} "
        f"L{x+134},{y+51} L{x+8},{y+51} Q{x+2},{y+48} {x+4},{y+36} Z",
        fill="#f6f7f8",
        stroke=INK,
        sw=1.65,
    )
    svg.path(f"M{x+29},{y+11} L{x+48},{y+11} L{x+48},{y+27} L{x+18},{y+27} Z", fill="white", stroke=INK, sw=1.05)
    svg.path(f"M{x+53},{y+11} L{x+78},{y+11} L{x+93},{y+27} L{x+53},{y+27} Z", fill="white", stroke=INK, sw=1.05)
    svg.circle(x + 34, y + 51, 10.4, "#7a7d81", stroke=INK, sw=1.65)
    svg.circle(x + 103, y + 51, 10.4, "#7a7d81", stroke=INK, sw=1.65)
    svg.path(f"M{x+39},{y-20} Q{x+68},{y-40} {x+97},{y-20}", fill="none", stroke=color, sw=4.1)
    svg.path(f"M{x+53},{y-11} Q{x+68},{y-21} {x+83},{y-11}", fill="none", stroke=color, sw=3.1)
    svg.circle(x + 68, y - 3, 2.8, color, stroke=color, sw=0.9)
    svg.line(x - 9, y + 65, x + 184, y + 65, stroke="#4b4b4b", sw=0.95, dash="18 12")


def local_graph_box(svg: SVG, x: float, y: float, color: str) -> None:
    box_color = SOFT_RED if color == RED else SOFT_GREEN
    svg.rect(x, y, 104, 104, rx=6, fill="#fbfffb", stroke=box_color, sw=0.8, dash="6 4")
    trajectory_graph_icon(svg, x + 53, y + 36, 0.64, node_fill="#92ad93" if color != RED else "#d7837e", stroke=INK, sw=0.85)
    svg.multi_text(x + 52, y + 78, ["Local trajectory", "interaction graph"], size=10.8, line_gap=15)


def draw_set_box(
    svg: SVG,
    x: float,
    y: float,
    label: str,
    variable: str,
    subscript: str,
    color: str,
    fill: str,
    w: float = 205,
    h: float = 58,
) -> None:
    svg.rect(x, y, w, h, rx=6, fill=fill, stroke=color, sw=1.25)
    label_color = INK if color in {GREEN, SOFT_GREEN} else color
    # Native SVG text keeps the label transparent over the tinted set box.
    svg.add(
        f'<text x="{x + w / 2:g}" y="{y + 24:g}" fill="{label_color}" font-size="18.3" '
        f'font-weight="400" text-anchor="middle" font-family="Arial, Helvetica, sans-serif">'
        f'{esc(label)}<tspan font-family="STIXGeneral, Times New Roman, serif" '
        f'font-style="italic" dx="5">{esc(variable)}</tspan>'
        f'<tspan baseline-shift="sub" font-size="12" font-family="STIXGeneral, Times New Roman, serif">{esc(subscript)}</tspan>'
        f'</text>'
    )
    for i in range(3):
        svg.circle(x + 52 + i * 28, y + 38, 5.2, color, stroke=color, sw=0.75)
        svg.rect(x + 45.5 + i * 28, y + 46, 13, 6.2, rx=2, fill=color, stroke=color, sw=0.75)
    svg.text(x + w - 41, y + 49, "...", size=24, fill=INK)


def upload_label(svg: SVG, x: float, y: float, idx: str) -> None:
    svg.text(x, y, "Upload:", size=15.5, fill=BLUE, weight="600", anchor="start")
    svg.math(x + 63, y - 4, rf"\Delta_{{{idx}}}^{{\,t}},\ z_{{{idx}}}^{{\,t}}", max_w=76, max_h=24, size=19, fill=BLUE, anchor="start")


def build_svg() -> str:
    svg = SVG()
    svg.text(W / 2, 42, "Topology-Explainable Robust Federated Trajectory Prediction Framework", size=34, weight="800")

    svg.rect(12, 68, 1669, 625, rx=17, fill="none", stroke=DASH_BLUE, sw=0.85, dash="7 8")
    svg.rect(12, 694, 1669, 169, rx=15, fill="none", stroke=DASH_BROWN, sw=0.85, dash="7 8")

    svg.multi_text(91, 181, ["Server-side", "audit and", "aggregation", "layer"], size=20.5, fill=BLUE, weight="600", line_gap=27)
    server_icon(svg, 178, 163)

    top_cards = [
        (312, 95, 216, 249, 1, ["Topology-aware", "audit"], r"\Delta,\ z \to S,\ D"),
        (557, 95, 200, 249, 2, ["Continual", "health memory"], r"Q,\ \sigma"),
        (784, 95, 204, 249, 3, ["Adaptive", "health scoring"], r"\alpha,\ H"),
        (1016, 95, 223, 249, 4, ["Norm-ratio audit", "and isolation"], r"H,\ R \to A,\ I"),
        (1269, 95, 186, 249, 5, ["Robust", "aggregation"], r"A \to \theta"),
        (1480, 95, 164, 249, 6, ["Global", "model"], r"\theta^{t+1}"),
    ]
    for card in top_cards:
        draw_card(svg, *card)

    topology_graph_icon(svg, 374, 221, 0.98, node_fill="#d8dde2", sw=1.15)
    grid_icon(svg, 436, 178)
    memory_icon(svg, 579, 200)
    scales_icon(svg, 850, 235, 0.86)
    shield_icon(svg, 951, 231, 0.84)
    magnifier_icon(svg, 1074, 213, 0.85)
    heat_grid(svg, 1144, 181, red=True, cell=14, gap=3, accent=1.0)
    gear_people_icon(svg, 1361, 204)
    global_model_icon(svg, 1562, 223)

    for x1, x2 in [(528, 557), (757, 784), (988, 1016), (1239, 1269), (1455, 1480)]:
        svg.line(x1, 210, x2, 210, stroke=BLUE, sw=2, marker="arrowBlue")

    svg.line(370, 416, 1174, 416, stroke=BLUE, sw=1.75)
    svg.line(370, 416, 370, 505, stroke=BLUE, sw=1.75, marker="arrowBlue")
    svg.line(754, 416, 754, 505, stroke=BLUE, sw=1.75, marker="arrowBlue")
    svg.line(1174, 416, 1174, 505, stroke=BLUE, sw=1.75, marker="arrowBlue")
    svg.math(462, 397, r"\mathrm{Broadcast:}\ \theta^t", max_w=124, max_h=20, size=16, fill=BLUE, anchor="start")
    svg.math(800, 397, r"\mathrm{Broadcast:}\ \theta^t", max_w=124, max_h=20, size=16, fill=BLUE, anchor="start")
    svg.math(998, 397, r"\mathrm{Broadcast:}\ \theta^t", max_w=124, max_h=20, size=16, fill=BLUE, anchor="start")

    svg.line(326, 505, 326, 417, stroke=BLUE, sw=1.7, dash="7 6", marker="arrowBlue")
    svg.line(713, 505, 713, 417, stroke=BLUE, sw=1.7, dash="7 6", marker="arrowBlue")
    upload_label(svg, 260, 401, "1")
    upload_label(svg, 646, 401, "2")

    client_box(svg, 196, 513, 348, 150, "Client 1 (benign)", GREEN)
    client_box(svg, 588, 513, 332, 150, "Client 2 (benign)", GREEN)
    svg.text(968, 572, "...", size=29, fill="#444444", weight="650")
    client_box(svg, 1022, 513, 304, 150, "Malicious client", RED, malicious=True)

    svg.line(1253, 238, 1253, 448, stroke=DASH_BLUE, sw=0.9, dash="7 7")
    svg.line(1253, 386, 1356, 386, stroke=DASH_BLUE, sw=1.05, dash="7 7", marker="arrowBlue")
    svg.line(1253, 454, 1356, 454, stroke=DASH_BLUE, sw=1.05, dash="7 7", marker="arrowBlue")
    svg.line(1164, 382, 1164, 345, stroke=DASH_BLUE, sw=1.0, dash="7 7", marker="arrowBlue")
    svg.line(1164, 386, 1356, 386, stroke=DASH_BLUE, sw=0.8, dash="7 7")

    draw_set_box(svg, 1359, 357, "Accepted Set", "A", "t", SOFT_GREEN, "#fbfff9")
    draw_set_box(svg, 1359, 425, "Isolated Set", "I", "t", SOFT_RED, "#fffafa")
    svg.rect(1359, 491, 205, 68, rx=8, fill="#ffffff", stroke="#8b98a4", sw=0.85, dash="7 6")
    svg.text(1461.5, 514, "Excluded Updates", size=15.5, weight="700")
    heat_grid(svg, 1442, 524, red=True, cell=13.5, gap=3, accent=0.7)

    svg.multi_text(101, 555, ["Local", "GRIP/GNN", "training", "layer"], size=20.5, fill=SOFT_GREEN, weight="700", line_gap=26)
    svg.rect(34, 511, 134, 154, rx=8, fill="none", stroke=SOFT_GREEN, sw=1.0, dash="7 7")

    svg.line(370, 704, 370, 666, stroke=GREEN, sw=1.6, marker="arrowGreen")
    svg.line(754, 704, 754, 666, stroke=GREEN, sw=1.6, marker="arrowGreen")
    svg.line(1174, 704, 1174, 666, stroke=RED, sw=1.6, marker="arrowRed")

    svg.multi_text(86, 751, ["Connected-", "vehicle", "data layer"], size=19.5, fill=BROWN, weight="700", line_gap=27)

    svg.text(374, 724, "Client 1 (benign)", size=19, fill=GREEN, weight="700")
    car_icon(svg, 223, 772, GREEN, 0.88)
    cylinder(svg, 410, 754, w=39, h=51)
    local_graph_box(svg, 504, 727, GREEN)
    svg.text(654, 757, "...", size=35, weight="700")

    svg.text(797, 724, "Client 2 (benign)", size=19, fill=GREEN, weight="700")
    car_icon(svg, 724, 772, GREEN, 0.88)
    cylinder(svg, 852, 754, w=39, h=51)
    local_graph_box(svg, 912, 727, GREEN)

    svg.text(1222, 724, "Malicious client", size=19, fill=RED, weight="700")
    car_icon(svg, 1099, 772, RED, 0.88)
    cylinder(svg, 1256, 754, w=39, h=51)
    local_graph_box(svg, 1323, 727, RED)

    svg.rect(529, 875, 620, 41, rx=5, fill="#fbfbfb", stroke="#2a5682", sw=0.8)
    svg.rect(625, 888, 13, 17, rx=2, fill="#66717c", stroke="#66717c", sw=0.7)
    svg.path("M627,890 C627,881 636,881 636,890", fill="none", stroke="#66717c", sw=2.2)
    svg.circle(631.5, 896.5, 1.7, "white", stroke="white", sw=0.7)
    svg.text(674, 901, "Raw trajectory data remain local on clients.", size=20.2, fill="#1e4a78", weight="700", anchor="start")

    return svg.render()


def render_png() -> None:
    converter = shutil.which("rsvg-convert")
    if not converter:
        raise RuntimeError("rsvg-convert is required to render PNG preview.")
    subprocess.run([converter, "-w", str(W), "-h", str(H), str(SVG_OUT), "-o", str(PNG_OUT)], check=True)


def make_qa_images() -> dict[str, float]:
    if not REFERENCE.exists():
        raise FileNotFoundError(f"Reference image not found: {REFERENCE}")
    ref = Image.open(REFERENCE).convert("RGB").resize((W, H))
    recon = Image.open(PNG_OUT).convert("RGB").resize((W, H))
    diff = ImageChops.difference(ref, recon)
    stat = ImageStat.Stat(diff)
    mean_abs = sum(stat.mean) / 3
    gray = diff.convert("L")
    px = gray.load()
    count = 0
    total = W * H
    for y in range(H):
        for x in range(W):
            if px[x, y] > 24:
                count += 1
    diff_pct = 100 * count / total

    enhanced = diff.point(lambda p: min(255, int(p * 3.2)))
    enhanced.save(DIFF_OUT)
    make_roi_sheet(ref, recon, enhanced)

    canvas = Image.new("RGB", (W * 2 + 38, H + 62), "white")
    canvas.paste(ref, (0, 52))
    canvas.paste(recon, (W + 38, 52))
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
    except Exception:
        font = ImageFont.load_default()
    draw.text((20, 14), "Reference", fill=(20, 20, 20), font=font)
    draw.text((W + 58, 14), f"Pure-vector SVG reconstruction: {OUTPUT_NAME}", fill=(20, 20, 20), font=font)
    canvas.save(SIDE_BY_SIDE)
    metrics = {"mean_abs_rgb_delta": mean_abs, "pixels_delta_gt_24_pct": diff_pct}
    try:
        import numpy as np
        from skimage.metrics import structural_similarity

        metrics["ssim"] = structural_similarity(
            np.asarray(ref.convert("L")),
            np.asarray(recon.convert("L")),
            data_range=255,
        )
    except Exception:
        metrics["ssim"] = -1
    return metrics


def make_roi_sheet(ref: Image.Image, recon: Image.Image, enhanced_diff: Image.Image) -> None:
    rois = [
        ("top modules", (300, 80, 1655, 355)),
        ("server/data flow", (180, 380, 1338, 675)),
        ("accepted sets", (1338, 340, 1588, 584)),
        ("privacy bar", (500, 866, 1180, 925)),
    ]
    scale = 0.55
    gutter = 18
    label_h = 28
    rows = []
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for label, box in rois:
        crops = [ref.crop(box), recon.crop(box), enhanced_diff.crop(box)]
        tw = int(crops[0].width * scale)
        th = int(crops[0].height * scale)
        row = Image.new("RGB", (tw * 3 + gutter * 4, th + label_h + 10), "white")
        draw = ImageDraw.Draw(row)
        draw.text((gutter, 5), label, fill=(20, 20, 20), font=font)
        for i, crop in enumerate(crops):
            resized = crop.resize((tw, th), Image.Resampling.LANCZOS)
            x = gutter + i * (tw + gutter)
            row.paste(resized, (x, label_h + 8))
            draw.rectangle((x, label_h + 8, x + tw - 1, label_h + th + 7), outline=(210, 216, 224), width=1)
        rows.append(row)
    sheet_w = max(row.width for row in rows)
    sheet_h = sum(row.height for row in rows) + gutter * (len(rows) + 1)
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    y = gutter
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height + gutter
    SHEET_LABELS = ["Reference", "Reconstruction", "Diff x3.2"]
    draw = ImageDraw.Draw(sheet)
    x0 = gutter
    if rows:
        crop_w = int((rois[0][1][2] - rois[0][1][0]) * scale)
        for i, label in enumerate(SHEET_LABELS):
            draw.text((x0 + i * (crop_w + gutter), 0), label, fill=(80, 86, 94), font=font)
    sheet.save(ROI_SHEET)


def write_report(metrics: dict[str, float]) -> None:
    REPORT.write_text(
        f"""# SVG reconstruction lab test: {OUTPUT_NAME}

Reference image: `{REFERENCE}`
Canvas: `{W} x {H}`

## Outputs

- `{SVG_OUT.name}`: pure-vector editable SVG draft with mathtext-rendered formula layers.
- `{PNG_OUT.name}`: raster render from SVG.
- `{SIDE_BY_SIDE.name}`: reference and reconstruction.
- `{DIFF_OUT.name}`: enhanced pixel difference heatmap.
- `{ROI_SHEET.name}`: local ROI reference/reconstruction/diff sheet.

## Automated pixel check

- Mean absolute RGB delta: `{metrics['mean_abs_rgb_delta']:.2f}` / 255
- Pixels with grayscale delta > 24: `{metrics['pixels_delta_gt_24_pct']:.2f}%`
- SSIM: `{metrics['ssim']:.4f}`

The score is expected to be imperfect because the icons are rebuilt with editable primitives rather than raster tracing.

## Included reconstruction techniques

- Clear Upload formulas with mathtext-rendered subscripts/superscripts.
- Centered broadcast down arrows over Client 1, Client 2, and malicious client.
- Layered top-card icons, matrices, memory bars, audit icons, aggregation icon, and global model icon.
- Client training boxes rebuilt from graph/database/arrow primitives.
- Right-side Accepted/Isolated/Excluded update panels.
- Bottom connected-vehicle layer with cars, wireless signs, databases, and local graph boxes.
- Mathtext formulas remain inlined as SVG path groups instead of embedded SVG images.

## Next high-cost iterations

1. Run OCR/visual pass for exact text baselines and formula glyphs.
2. Split the SVG into named layer groups: server cards, communication arrows, client boxes, data layer, privacy bar.
3. Use local crop diff on each card, then optimize positions and line weights independently.
4. Replace icon approximations with precise reusable symbol definitions.
5. Freeze typography after measuring exact font sizes from the reference.
6. Run SVGO only after visual lock, preserving IDs and grouping.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild the topology framework reference as editable SVG and QA previews."
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=SCRIPT_DIR / "reference.png",
        help="Reference bitmap path. The original file is only read, never overwritten.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=SCRIPT_DIR / "outputs",
        help="Directory for SVG, PNG, diff, ROI sheet, and report.",
    )
    parser.add_argument(
        "--name",
        default="framework_reconstruction",
        help="Output filename prefix without extension.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_outputs(args.reference, args.out_dir, args.name)
    SVG_OUT.write_text(build_svg(), encoding="utf-8")
    render_png()
    metrics = make_qa_images()
    write_report(metrics)
    print(f"Wrote {SVG_OUT}")
    print(f"Wrote {PNG_OUT}")
    print(f"Wrote {SIDE_BY_SIDE}")
    print(f"Wrote {DIFF_OUT}")
    print(f"Wrote {REPORT}")
    print(metrics)


if __name__ == "__main__":
    main()
