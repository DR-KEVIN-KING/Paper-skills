# High-Fidelity SVG Reconstruction Workflow

This workflow is for recreating academic schematic figures from a bitmap reference as editable SVG. It favors semantic rebuilding over automated vector tracing.

## 1. Reference Setup

- Save the provided image as `reference.png` in a dedicated project folder.
- Record width, height, and aspect ratio.
- Use the original canvas size for the SVG `viewBox`.
- Create a first blank SVG with only the title and major dashed regions to verify scale.

## 2. Semantic Decomposition

Map the reference into named visual groups before drawing:

- `background`: white canvas, outer dashed frames, section dividers.
- `title`: main title and any global caption.
- `server_layer`: side label, server icon, top process cards.
- `process_cards`: card frames, step numbers, icons, formula strips.
- `connectors`: solid/dashed arrows, upload/broadcast labels, accepted/isolated routes.
- `client_layer`: client training boxes, graph/database/arrow motifs, local training labels.
- `data_layer`: vehicles, wireless marks, databases, trajectory graph boxes.
- `privacy_note`: lock, footer message, bottom rule.

Use this layer map as the review checklist. If a region is wrong, patch only the relevant group.

## 3. Drawing Strategy

- Build icons from SVG primitives: `rect`, `circle`, `line`, `path`, `polygon`.
- Use reusable helper functions for repeated motifs: cards, graphs, heat grids, memory bars, cylinders, cars, local graph boxes, people sets.
- Keep line widths and fills centralized in constants.
- Prefer slightly conservative saturation; academic figures usually look more polished when helper frames and dashed routes are quiet.
- Use named output versions such as `v1`, `v2`, `v3` only when a human review happened between runs.

## 4. Formula Rendering

Use Matplotlib with:

```python
matplotlib.use("svg")
rcParams.update({
    "svg.fonttype": "path",
    "mathtext.fontset": "stix",
    "font.family": "STIXGeneral",
})
```

Render each formula as a tiny SVG, extract the `<g id="figure_1">` fragment, prefix IDs, then inline it inside the final SVG. This gives LaTeX-like glyphs and prevents missing-font issues in PNG/PDF/PPT exports.

For labels such as `Upload: Delta_1^t, z_1^t`, split ordinary words and math paths when clarity matters. Give subscripts and superscripts enough width so they do not visually collide.

## 5. QA Outputs

Every reconstruction pass should produce:

- editable SVG
- PNG render from SVG
- side-by-side sheet: reference vs reconstruction
- enhanced diff image
- ROI sheet for top modules, flow lines, right legend, footer, or other critical areas
- Markdown report with mean RGB delta, changed-pixel percentage, and SSIM when available

Pixel metrics guide iteration but do not replace visual review. A semantic SVG rebuilt from primitives will never perfectly match anti-aliased raster edges, so inspect formula legibility, alignment, and relative visual weight.

## 6. Feedback Iteration Order

Apply feedback in this priority order:

1. Text and formula readability.
2. Arrow direction, anchor points, and routing.
3. Major block alignment and spacing.
4. Icon scale and stroke weight.
5. Matrix/heatmap color levels.
6. Dashed frame weight and saturation.
7. Bottom labels, footer notes, and tiny spacing.

For teacher comments, convert each bullet into a concrete script edit: coordinate change, scale factor, stroke width, color constant, font size, or ROI crop adjustment.

## 7. Finalization

- Keep the source Python script with the final SVG so future edits are deterministic.
- Only run SVGO or other optimizers after visual lock, and preserve useful group IDs.
- Export PNG/TIFF/PDF after the SVG is approved.
- If the user wants PPT editing, split the final SVG into logical groups in a later pass; do not sacrifice reconstruction fidelity during the first SVG pass.
