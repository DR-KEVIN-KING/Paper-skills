#!/usr/bin/env python3
"""Render a LaTeX-like math expression to a standalone SVG.

The output is suitable for embedding into draw.io image cells. It favors STIX
math glyphs and deterministic SVG output over editable text, which prevents
font drift in PowerPoint/PDF exports.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("svg")
from matplotlib import rcParams
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure


def render_formula(tex: str, out: Path, font_size: float, color: str, pad: float) -> None:
    rcParams.update(
        {
            "svg.fonttype": "path",
            "mathtext.fontset": "stix",
            "font.family": "STIXGeneral",
        }
    )

    fig = Figure(figsize=(0.01, 0.01), dpi=100)
    fig.patch.set_alpha(0)
    FigureCanvasSVG(fig)
    fig.text(0, 0, f"${tex}$", fontsize=font_size, color=color, ha="left", va="baseline")

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out,
        format="svg",
        transparent=True,
        bbox_inches="tight",
        pad_inches=pad,
        metadata={"Date": None},
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex", required=True, help="Mathtext expression without surrounding dollar signs.")
    parser.add_argument("--out", required=True, type=Path, help="Output SVG path.")
    parser.add_argument("--font-size", type=float, default=22.0)
    parser.add_argument("--color", default="#222222")
    parser.add_argument("--pad", type=float, default=0.01)
    args = parser.parse_args()

    render_formula(args.tex, args.out, args.font_size, args.color, args.pad)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
