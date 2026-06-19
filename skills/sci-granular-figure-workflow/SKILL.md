---
name: sci-granular-figure-workflow
description: Build publication-grade SCI schematic figures from granular SVG atoms. Use when creating or rebuilding academic workflow/framework figures for papers, theses, posters, or PPTs where frames, text labels, formulas, icons, connectors, and grouped previews must remain separate editable SVG files with layout manifests and QA reports.
---

# SCI Granular Figure Workflow

Use this skill to create or rebuild SCI-style schematic figures as **atomic SVG assets plus layout metadata**, rather than as one flattened image.

## Core Rule

Keep every visually independent component as its own SVG:

- Frames and region boxes are `frame` atoms.
- Text labels are `text` atoms.
- Math expressions are `formula` atoms.
- Icons, graphs, matrices, vehicles, servers, shields, databases, and similar drawings are `visual` atoms.
- Arrows, flow lines, dashed links, and routing marks are `connector` atoms.

Only combine elements into one SVG when they are genuinely one inseparable drawing and will not need independent adjustment. Read `references/granularity-rules.md` when the user asks for very detailed splitting, PPT editing, or journal-grade source preservation.

## Workflow

1. Define or locate source SVG libraries for `visual`, `text_outlined`, and `formula_outlined`.
2. Copy `assets/templates/figure_manifest_template.json` or adapt `assets/examples/topology_framework_granular_v1.json`.
3. Fill the manifest:
   - `atomic_copies`: list every independent visual/text/formula atom.
   - `frames`: define every independent box or dashed region.
   - `connectors`: define every independent arrow or line.
   - `units`: define layout-only assemblies by atom id and coordinates.
4. Run:

```bash
python3 scripts/build_granular_workflow.py path/to/manifest.json
```

5. Inspect:
   - `granular_outputs/01_atomic_svg/` for independent atoms.
   - `granular_outputs/02_unit_layouts/` for editable placement metadata.
   - `granular_outputs/03_assembled_preview_svg/` only as visual previews.
   - `granular_outputs/06_contact_sheets/` for quick review.
   - `granular_outputs/07_qa/qa_report.json` for missing assets, missing atoms, text residue, and counts.

## Output Policy

Treat `03_assembled_preview_svg` and `04_ppt_ready_preview_svg` as convenience previews, not as the only source of truth. For final PPT precision, insert atoms from `01_atomic_svg` and use the matching JSON in `02_unit_layouts` to align them.

## Quality Checks

Before handing results to the user:

- Confirm `missing_assets` and `missing_atoms` are empty in the QA report.
- Confirm `text_residue_in_atomic_svg` is empty when outlined text/formulas are expected.
- Render contact sheets and visually check that frames, text, formulas, icons, and connectors are not merged incorrectly.
- Keep generated outputs scoped to a project folder; avoid overwriting the user's original figure assets.

## Bundled Resources

- `scripts/build_granular_workflow.py`: deterministic builder for atom SVGs, layouts, previews, contact sheets, QA, and zip output.
- `references/granularity-rules.md`: hard splitting rules.
- `assets/templates/figure_manifest_template.json`: starter manifest.
- `assets/examples/topology_framework_granular_v1.json`: working example from a topology-explainable federated trajectory prediction framework figure.
