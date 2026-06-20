---
name: svg-reconstruction-lab-workflow
description: "Use when rebuilding a reference figure as high-fidelity editable SVG: academic schematic screenshots, paper framework diagrams, PPT figures, formulas that need LaTeX-like rendering, pixel/ROI QA sheets, or teacher-feedback visual refinement."
---

# SVG Reconstruction Lab Workflow

Use this skill when the user wants a reference image recreated as a clean, editable SVG rather than traced or flattened. The goal is maximum visual fidelity while preserving vector primitives, math formulas, named layers, and repeatable QA outputs.

## When To Use

- A teacher/reference image is provided and the user asks to make a nearly identical SVG.
- Formulas must look like LaTeX, not cramped Unicode text.
- The figure needs iterative visual tuning: arrows, spacing, icon weight, color saturation, dashed frames, and small labels.
- The user wants a reusable workflow for future figures, not just one exported PNG.

## Core Workflow

1. Copy the reference image into a project folder and keep its native canvas size.
2. Decompose the figure into semantic layers: outer frames, title, modules/cards, icons, formulas, connectors, client/data rows, legends, and notes.
3. Rebuild with explicit SVG primitives. Avoid raster tracing unless a bitmap texture is intentionally required.
4. Render formulas with Matplotlib mathtext/LaTeX-like glyphs as inline SVG path groups.
5. Render the SVG to PNG with `rsvg-convert`.
6. Generate side-by-side, enhanced diff, ROI crop sheets, and a short QA report.
7. Apply feedback in priority order: formula clarity, arrow alignment, module spacing, icon proportions, color/line weight, then tiny label polish.

Read `references/workflow.md` before a serious reconstruction pass. Use `scripts/reconstruct_topology_framework_svg.py` as the proven starting script from the topology federated trajectory framework trial.

## Tooling

Preferred Python environment:

```bash
python3 -m venv .venv-svg-reconstruction
. .venv-svg-reconstruction/bin/activate
python -m pip install pillow matplotlib numpy scipy scikit-image
```

On macOS, install a renderer if needed:

```bash
brew install librsvg
```

Run the bundled example script:

```bash
python scripts/reconstruct_topology_framework_svg.py \
  --reference path/to/reference.png \
  --out-dir outputs/svg_reconstruction_trial \
  --name framework_reconstruction
```

The script writes editable SVG, rendered PNG, side-by-side comparison, enhanced diff, ROI sheet, and `qa_report.md`.

## Quality Bar

- Preserve the original canvas ratio and first match large layout blocks before tiny details.
- Use path-rendered formulas for important math labels; reserve native text for ordinary labels that remain editable.
- Prefer visual primitives for icons: graph nodes, matrix cells, cylinders, cars, arrows, gears, magnifiers, shields, and people.
- Keep colors slightly restrained unless the reference is saturated.
- For every teacher comment, update the script, regenerate all QA outputs, and inspect local crops before handing over.

## Output Policy

Do not overwrite the reference. Keep generated files in a dated output folder. If committing the skill, stage only the skill folder and intentionally removed older skill files; leave unrelated project artifacts alone.
