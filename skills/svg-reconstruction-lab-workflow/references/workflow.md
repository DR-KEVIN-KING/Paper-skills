# Draw.io SCI Figure Refinement Workflow

This reference captures the workflow used for the topology-explainable robust federated trajectory prediction framework figure.

## 1. Source Of Truth

- Treat the `.drawio` file as the source of truth after the user has manually adjusted it.
- Do not rebuild from a bitmap when the user asks to refine an existing draw.io version.
- Always create a backup beside the source:

  `Fig3_1_framework_iconfont_draft.before_<label>_<timestamp>.drawio`

## 2. Safe Edit Order

1. Inspect relevant IDs and geometry.
2. Backup the source file.
3. Render formula SVGs if formulas are involved.
4. Patch one narrow group at a time.
5. Export PNG at 3x scale or higher.
6. Inspect the whole image and at least one crop around changed regions.

## 3. Formula Standards

Use Matplotlib mathtext with STIX fonts:

```python
rcParams.update({
    "svg.fonttype": "path",
    "mathtext.fontset": "stix",
    "font.family": "STIXGeneral",
})
```

Recommended formulas for the framework figure:

- Step 1: `\Delta_i^t, e_i^t \rightarrow S_i^t, D_i^t`
- Step 2: `Q_i^t \rightarrow \sigma_i^t`
- Step 3: `\alpha_i^t, H_i^t`
- Step 4: `H_i^t, R_i^t \rightarrow A^t, I^t`
- Step 5 inline aggregation: `\theta^{t+1}=\Sigma_{i\in A^t}\,w_i^t\theta_i^{t+1}`
- Step 6: `\theta^{t+1}`

For Step 5, avoid the default display-style `\sum` when space is tight because it creates a tall stacked formula. Use inline `\Sigma_{i\in A^t}` or a single-row SVG unless the user asks for a display equation.

## 4. Common Fig. 3-1 Draw.io IDs

Formula and module IDs:

- `module_1_formula`, `module_2_formula`, `module_3_formula`, `module_4_formula`
- `module_5_formula_box`, `module_5_formula_l1`, `module_5_formula_l2`
- `module_6_formula`

Server-side routes:

- `step4_to_accepted`
- `step4_to_isolated`
- `accepted_to_agg`
- `isolated_to_excluded`
- `broadcast_line`
- `broadcast_down_1`, `broadcast_down_2`, `broadcast_down_3`
- `upload_1`, `upload_2`, `upload_m`

Key text and groups:

- `accepted_text`, `isolated_text`
- `excluded_box`, `excluded_text`, `excluded_icon`, `excluded_x`
- `client_1_data_local_graph_text`, `client_2_data_local_graph_text`, `malicious_data_local_graph_text`
- `legend_matrix`, `privacy_icon`, `privacy_text`

## 5. Teacher-Comment Mapping

- "Formula is ugly / too small": rerender formula SVG, then replace the existing formula image cell and tune geometry.
- "Arrow lines are stiff": use draw.io curved connectors only where they improve flow; use orthogonal connectors for audit branches.
- "Broadcast and upload are mixed": move upload source/target points left/right so they do not share an x-coordinate with broadcast arrows.
- "Isolated Set appears to enter aggregation": delete or reroute any red line into Step 5; keep only `Isolated Set -> Excluded Updates`.
- "Colors are too bright": reduce saturation, keep semantic color roles, and deepen only main labels/flows for readability.
- "Legend is too small": enlarge text and ensure legend icons match main diagram semantics.
- "Local interaction graph is unreadable": make the label two lines: `Local interaction<br>graph`.

## 6. Export Commands

Prefer draw.io CLI:

```bash
drawio -x -f png -s 3 -o figure_review.png figure.drawio
drawio -x -f pdf -o figure_review.pdf figure.drawio
```

If the CLI is missing, locate the app:

```bash
ls -d /Applications/draw.io.app /Applications/Draw.io.app 2>/dev/null
```

Use the PNG for teacher review, keep the `.drawio` for continued editing, and export PDF/SVG/PPT assets only after the teacher approves the layout.
