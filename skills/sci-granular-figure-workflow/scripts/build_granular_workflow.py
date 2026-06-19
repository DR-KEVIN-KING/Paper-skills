#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None
    ImageDraw = None
    ImageFont = None


SKILL_ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = SKILL_ROOT
OUT = WORK_ROOT / "granular_outputs"

DIRS = {
    "registry": OUT / "00_registry",
    "frames": OUT / "01_atomic_svg" / "frames",
    "visual": OUT / "01_atomic_svg" / "visual",
    "text": OUT / "01_atomic_svg" / "text",
    "formula": OUT / "01_atomic_svg" / "formula",
    "connectors": OUT / "01_atomic_svg" / "connectors",
    "layouts": OUT / "02_unit_layouts",
    "assembled": OUT / "03_assembled_preview_svg",
    "ppt_ready": OUT / "04_ppt_ready_preview_svg",
    "png": OUT / "05_png_preview",
    "sheets": OUT / "06_contact_sheets",
    "qa": OUT / "07_qa",
}

SVG_NS = "http://www.w3.org/2000/svg"


def configure_output_root(work_root: Path) -> None:
    global WORK_ROOT, OUT, DIRS
    WORK_ROOT = work_root.resolve()
    OUT = WORK_ROOT / "granular_outputs"
    DIRS = {
        "registry": OUT / "00_registry",
        "frames": OUT / "01_atomic_svg" / "frames",
        "visual": OUT / "01_atomic_svg" / "visual",
        "text": OUT / "01_atomic_svg" / "text",
        "formula": OUT / "01_atomic_svg" / "formula",
        "connectors": OUT / "01_atomic_svg" / "connectors",
        "layouts": OUT / "02_unit_layouts",
        "assembled": OUT / "03_assembled_preview_svg",
        "ppt_ready": OUT / "04_ppt_ready_preview_svg",
        "png": OUT / "05_png_preview",
        "sheets": OUT / "06_contact_sheets",
        "qa": OUT / "07_qa",
    }


def ensure_clean_dirs() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def marker_defs() -> str:
    return """<defs>
  <marker id="arrow-ink" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,3 L0,6 Z" fill="#111111"/></marker>
</defs>"""


def marker_for(stroke: str) -> str:
    return "url(#arrow-ink)"


def write_frame_svg(frame: dict) -> Path:
    w, h = float(frame["w"]), float(frame["h"])
    stroke = frame.get("stroke", "#386FAE")
    fill = frame.get("fill", "#FFFFFF")
    stroke_width = float(frame.get("stroke_width", 2.0))
    radius = float(frame.get("radius", 10))
    dash = frame.get("dash")
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    inset = stroke_width / 2
    body = (
        f'<rect x="{inset:.3f}" y="{inset:.3f}" width="{w - stroke_width:.3f}" height="{h - stroke_width:.3f}" '
        f'rx="{radius:.3f}" ry="{radius:.3f}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{stroke_width:.3f}"{dash_attr}/>'
    )
    path = DIRS["frames"] / f'{frame["id"]}.svg'
    path.write_text(f'<svg xmlns="{SVG_NS}" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n{body}\n</svg>\n', encoding="utf-8")
    return path


def write_connector_svg(conn: dict) -> Path:
    w, h = float(conn["w"]), float(conn["h"])
    stroke = conn.get("stroke", "#386FAE")
    stroke_width = float(conn.get("stroke_width", 2.0))
    dash = conn.get("dash")
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    body = (
        f'<line x1="{conn["x1"]}" y1="{conn["y1"]}" x2="{conn["x2"]}" y2="{conn["y2"]}" '
        f'stroke="{stroke}" stroke-width="{stroke_width:.3f}" stroke-linecap="round" '
        f'marker-end="{marker_for(stroke)}"{dash_attr}/>'
    )
    path = DIRS["connectors"] / f'{conn["id"]}.svg'
    path.write_text(
        f'<svg xmlns="{SVG_NS}" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n{marker_defs()}\n{body}\n</svg>\n',
        encoding="utf-8",
    )
    return path


def copy_atomic_assets(manifest: dict, qa: dict) -> dict[str, Path]:
    atom_paths: dict[str, Path] = {}
    kind_dir = {
        "visual": DIRS["visual"],
        "text": DIRS["text"],
        "formula": DIRS["formula"],
    }
    roots = manifest.get("library_roots", {})
    for atom in manifest.get("atomic_copies", []):
        source = Path(roots[atom["lib"]]) / atom["file"]
        target = kind_dir[atom["kind"]] / f'{atom["id"]}.svg'
        if not source.exists():
            qa["missing_assets"].append(str(source))
            continue
        shutil.copy2(source, target)
        atom_paths[atom["id"]] = target
    return atom_paths


def strip_svg_outer(svg_text: str) -> tuple[str, str]:
    text = re.sub(r"<\?xml[^>]*>\s*", "", svg_text, flags=re.I)
    text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", text, flags=re.I)
    match = re.search(r"<svg\b([^>]*)>(.*)</svg>\s*$", text, flags=re.I | re.S)
    if not match:
        raise ValueError("Invalid SVG")
    attrs = match.group(1)
    body = match.group(2)
    view_box_match = re.search(r'viewBox="([^"]+)"', attrs)
    if view_box_match:
        return view_box_match.group(1), body
    width_match = re.search(r'width="([0-9.]+)', attrs)
    height_match = re.search(r'height="([0-9.]+)', attrs)
    if width_match and height_match:
        return f'0 0 {width_match.group(1)} {height_match.group(1)}', body
    return "0 0 100 100", body


def embed_atom(path: Path, x: float, y: float, w: float, h: float) -> str:
    view_box, body = strip_svg_outer(path.read_text(encoding="utf-8", errors="ignore"))
    return (
        f'<svg x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" '
        f'viewBox="{view_box}" preserveAspectRatio="xMidYMid meet" overflow="visible">\n{body}\n</svg>'
    )


def build_units(manifest: dict, atom_paths: dict[str, Path], qa: dict) -> None:
    for unit in manifest.get("units", []):
        unit_id = unit["id"]
        canvas = unit["canvas"]
        w, h = float(canvas["w"]), float(canvas["h"])
        layout = {
            "id": unit_id,
            "canvas": canvas,
            "atoms": [],
            "rule": "This is a layout only. Atomic SVG files remain separate and editable."
        }
        chunks = [f'<svg xmlns="{SVG_NS}" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
        for item in unit.get("atoms", []):
            atom_id = item["atom"]
            path = atom_paths.get(atom_id)
            if path is None:
                qa["missing_atoms"].append({"unit": unit_id, "atom": atom_id})
                continue
            placement = {
                "atom": atom_id,
                "kind": item["kind"],
                "file": str(path.relative_to(OUT)),
                "x": item["x"],
                "y": item["y"],
                "w": item["w"],
                "h": item["h"]
            }
            layout["atoms"].append(placement)
            chunks.append(embed_atom(path, float(item["x"]), float(item["y"]), float(item["w"]), float(item["h"])))
        chunks.append("</svg>\n")
        assembled = "\n".join(chunks)
        (DIRS["layouts"] / f"{unit_id}.json").write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding="utf-8")
        assembled_path = DIRS["assembled"] / f"{unit_id}.svg"
        assembled_path.write_text(assembled, encoding="utf-8")
        shutil.copy2(assembled_path, DIRS["ppt_ready"] / f"{unit_id}.svg")


def render_svg(svg_path: Path, png_path: Path, width: int = 1400) -> bool:
    try:
        subprocess.run(
            ["rsvg-convert", "-w", str(width), "-o", str(png_path), str(svg_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def render_previews(qa: dict) -> None:
    for svg in sorted((OUT / "01_atomic_svg").rglob("*.svg")) + sorted(DIRS["assembled"].glob("*.svg")):
        rel = svg.relative_to(OUT).with_suffix("")
        png_name = "__".join(rel.parts) + ".png"
        if not render_svg(svg, DIRS["png"] / png_name, width=1600):
            qa["warnings"].append(f"Preview render failed: {svg}")


def make_contact_sheet(title: str, pattern: str, output: Path, cols: int = 3) -> None:
    if Image is None:
        return
    files = sorted(DIRS["png"].glob(pattern))
    if not files:
        return
    cell_w, cell_h, title_h = 540, 310, 54
    rows = (len(files) + cols - 1) // cols
    canvas = Image.new("RGB", (cell_w * cols, title_h + cell_h * rows), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
        label_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
    draw.text((22, 16), title, fill=(47, 58, 68), font=title_font)
    for idx, file in enumerate(files):
        row, col = divmod(idx, cols)
        x, y = col * cell_w, title_h + row * cell_h
        draw.rectangle((x + 10, y + 10, x + cell_w - 10, y + cell_h - 10), outline=(218, 226, 235), width=1)
        image = Image.open(file).convert("RGBA")
        image.thumbnail((cell_w - 48, cell_h - 78), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (cell_w - 30, cell_h - 70), (248, 250, 252, 255))
        bg.alpha_composite(image, ((bg.width - image.width) // 2, (bg.height - image.height) // 2))
        canvas.paste(bg.convert("RGB"), (x + 15, y + 16))
        draw.text((x + 18, y + cell_h - 38), file.stem.replace("__", " / ")[:66], fill=(54, 64, 74), font=label_font)
    canvas.save(output, quality=96)


def make_contact_sheets() -> None:
    make_contact_sheet("Atomic frames", "01_atomic_svg__frames__*.png", DIRS["sheets"] / "01_atomic_frames.png", cols=3)
    make_contact_sheet("Atomic visual assets", "01_atomic_svg__visual__*.png", DIRS["sheets"] / "02_atomic_visual.png", cols=3)
    make_contact_sheet("Atomic text and formulas", "01_atomic_svg__text__*.png", DIRS["sheets"] / "03_atomic_text.png", cols=3)
    make_contact_sheet("Atomic formulas", "01_atomic_svg__formula__*.png", DIRS["sheets"] / "04_atomic_formula.png", cols=3)
    make_contact_sheet("Atomic connectors", "01_atomic_svg__connectors__*.png", DIRS["sheets"] / "05_atomic_connectors.png", cols=3)
    make_contact_sheet("Assembled preview only", "03_assembled_preview_svg__*.png", DIRS["sheets"] / "06_assembled_preview.png", cols=2)


def write_registry(manifest: dict, atom_paths: dict[str, Path]) -> None:
    rows = []
    for atom_id, path in sorted(atom_paths.items()):
        kind = path.parent.name
        rows.append({"id": atom_id, "kind": kind, "file": str(path.relative_to(OUT))})
    with (DIRS["registry"] / "asset_registry.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "kind", "file"])
        writer.writeheader()
        writer.writerows(rows)
    (DIRS["registry"] / "asset_registry.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    (DIRS["registry"] / "workflow_policy.json").write_text(
        json.dumps(
            {
                "project": manifest.get("project"),
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "granularity_rule": "frame, visual, text, formula, and connector are separate atomic SVGs; assembled SVGs are preview only.",
                "ppt_recommendation": "Use atomic SVGs for final editable PPT. Use assembled preview SVG only for quick placement."
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def scan_text_residue() -> list[str]:
    offenders = []
    for svg in sorted((OUT / "01_atomic_svg").rglob("*.svg")):
        if re.search(r"<\s*(text|tspan)\b", svg.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(str(svg))
    return offenders


def zip_granular_outputs() -> Path:
    zip_path = WORK_ROOT / "SCI_granular_element_workflow_outputs.zip"
    if zip_path.exists():
        zip_path.unlink()
    subprocess.run(
        ["zip", "-r", str(zip_path), "granular_outputs"],
        cwd=WORK_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return zip_path


def main(argv: list[str]) -> int:
    manifest_path = Path(argv[1]) if len(argv) > 1 else SKILL_ROOT / "assets" / "examples" / "topology_framework_granular_v1.json"
    if not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()
    default_work_root = manifest_path.parent.parent if manifest_path.parent.name in {"manifest", "manifests"} else manifest_path.parent
    configure_output_root(default_work_root)
    manifest = read_manifest(manifest_path)
    ensure_clean_dirs()

    qa = {
        "project": manifest.get("project"),
        "manifest": str(manifest_path),
        "missing_assets": [],
        "missing_atoms": [],
        "warnings": [],
    }

    atom_paths = copy_atomic_assets(manifest, qa)
    for frame in manifest.get("frames", []):
        atom_paths[frame["id"]] = write_frame_svg(frame)
    for connector in manifest.get("connectors", []):
        atom_paths[connector["id"]] = write_connector_svg(connector)

    build_units(manifest, atom_paths, qa)
    render_previews(qa)
    make_contact_sheets()
    write_registry(manifest, atom_paths)

    qa["text_residue_in_atomic_svg"] = scan_text_residue()
    qa["counts"] = {
        "frames": len(list(DIRS["frames"].glob("*.svg"))),
        "visual": len(list(DIRS["visual"].glob("*.svg"))),
        "text": len(list(DIRS["text"].glob("*.svg"))),
        "formula": len(list(DIRS["formula"].glob("*.svg"))),
        "connectors": len(list(DIRS["connectors"].glob("*.svg"))),
        "unit_layouts": len(list(DIRS["layouts"].glob("*.json"))),
        "assembled_previews": len(list(DIRS["assembled"].glob("*.svg"))),
        "png_previews": len(list(DIRS["png"].glob("*.png"))),
    }
    (DIRS["qa"] / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = zip_granular_outputs()

    print(json.dumps({
        "skill_root": str(SKILL_ROOT),
        "work_root": str(WORK_ROOT),
        "granular_outputs": str(OUT),
        "zip": str(zip_path),
        "missing_assets": len(qa["missing_assets"]),
        "missing_atoms": len(qa["missing_atoms"]),
        "text_residue_in_atomic_svg": len(qa["text_residue_in_atomic_svg"]),
        "counts": qa["counts"],
    }, ensure_ascii=False, indent=2))
    return 0 if not qa["missing_assets"] and not qa["missing_atoms"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
