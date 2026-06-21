---
name: svg-reconstruction-lab-workflow
description: Use when refining SCI/thesis academic figures in draw.io from image/iconfont/SVG assets, especially workflows that need editable vector diagrams, LaTeX-like formula SVG replacement, teacher-feedback iteration, high-resolution PNG/PDF export, or conversion into PPT-ready editable objects while preserving manual edits.
---

# SVG Reconstruction Lab Workflow

Use this skill for publication-style figure refinement where a draw.io file is the source of truth. The priority is not full regeneration; the priority is preserving the user's manual edits while improving formulas, arrows, icon balance, legend readability, colors, and export quality.

## Non-Negotiables

- Backup the `.drawio` file before every modification.
- Patch by stable `mxCell` IDs or narrow prefixes. Never regenerate the whole canvas when the user has hand-edited the figure.
- Keep all final figure text in English for SCI/thesis use unless the user explicitly asks otherwise.
- Render important formulas as SVG images with path-like LaTeX math; avoid cramped Unicode formula text.
- For long aggregation formulas, prefer an inline one-row SVG unless the user explicitly asks for a display-style stacked sum.
- Preserve semantic color roles: blue for server/broadcast/global, green for benign/accepted/upload, red for malicious/isolated/excluded, gray for neutral data/models.
- Export review PNGs after edits and visually inspect the result before reporting completion.

## Core Workflow

If the host Python lacks Matplotlib/PyYAML, create a project virtual environment instead of modifying system Python:

```bash
python3 -m venv .venv-skill-workflow
.venv-skill-workflow/bin/python -m pip install matplotlib pyyaml
```

1. Read the user's teacher comments and convert each bullet into an element-level edit: formula size, route point, box position, icon scale, legend text, color, or export.
2. Inspect the draw.io XML for relevant IDs with:

   ```bash
   .venv-skill-workflow/bin/python scripts/refine_drawio_figure.py inspect path/to/figure.drawio --contains module_5
   ```

3. Render or update formula SVGs with:

   ```bash
   .venv-skill-workflow/bin/python scripts/render_formula_svg.py \
     --tex '\theta^{t+1}=\Sigma_{i\in A^t}\,w_i^t\theta_i^{t+1}' \
     --out outputs/step5_inline.svg \
     --font-size 22 --color '#222222'
   ```

4. Replace only the target formula/image cell and geometry:

   ```bash
   .venv-skill-workflow/bin/python scripts/refine_drawio_figure.py replace-image-svg figure.drawio \
     --id module_5_formula_l1 --svg outputs/step5_inline.svg \
     --x 1307 --y 272 --width 168 --height 30
   ```

5. Use targeted geometry/route edits for arrows and frames. See `references/workflow.md` for the exact SCI figure checklist and common Fig. 3-1 IDs.
6. Export review images:

   ```bash
   .venv-skill-workflow/bin/python scripts/refine_drawio_figure.py export-png figure.drawio \
     --out outputs/figure_review.png --scale 3
   ```

## Quality Bar

- Formulas remain readable after the figure is scaled to manuscript width.
- Upload and broadcast arrows are visually separated: blue downward broadcast, green/red upward uploads.
- Accepted Set flows only into robust aggregation; Isolated Set flows only into Excluded Updates.
- Legends use the same icons, colors, and line styles as the main diagram.
- Footer privacy statements and lock icons remain readable after export.
- All changes are reversible through timestamped backups.

## Output Policy

Keep the edited `.drawio` as the source file, plus exported `.png`/`.pdf` as review or submission artifacts. When committing this skill, stage only this skill folder and intentionally removed older skill files; leave unrelated thesis outputs alone.
