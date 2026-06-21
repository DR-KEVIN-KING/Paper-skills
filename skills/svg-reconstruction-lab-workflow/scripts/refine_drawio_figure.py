#!/usr/bin/env python3
"""ID-based draw.io figure refinement helpers.

The script intentionally performs narrow XML edits. It is designed for academic
figures where users have already hand-tuned the layout and only specific cells
should be changed.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET


def load(path: Path) -> ET.ElementTree:
    return ET.parse(path)


def save(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def backup(path: Path, label: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = path.with_name(f"{path.stem}.before_{label}_{stamp}{path.suffix}")
    shutil.copy2(path, dst)
    return dst


def cell(root: ET.Element, cell_id: str) -> ET.Element:
    found = root.find(f".//mxCell[@id='{cell_id}']")
    if found is None:
        raise SystemExit(f"missing mxCell id={cell_id}")
    return found


def geometry(el: ET.Element) -> ET.Element:
    g = el.find("mxGeometry")
    if g is None:
        raise SystemExit(f"missing mxGeometry in id={el.get('id')}")
    return g


def fmt(value: float | str) -> str:
    if isinstance(value, str):
        return value
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def set_geometry(root: ET.Element, cell_id: str, **values: float | str | None) -> None:
    g = geometry(cell(root, cell_id))
    for key, value in values.items():
        if value is not None:
            g.set(key, fmt(value))


def style_set(el: ET.Element, **pairs: str) -> None:
    style = el.get("style") or ""
    order: list[str] = []
    data: dict[str, str] = {}
    for part in style.split(";"):
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        if key not in data:
            order.append(key)
        data[key] = value
    for key, value in pairs.items():
        if key not in data:
            order.append(key)
        data[key] = value
    el.set("style", ";".join(f"{key}={data[key]}" for key in order) + ";")


def set_edge_points(root: ET.Element, cell_id: str, source: tuple[float, float] | None, target: tuple[float, float] | None) -> None:
    g = geometry(cell(root, cell_id))
    for point in g.findall("mxPoint"):
        role = point.get("as")
        xy = source if role == "sourcePoint" else target if role == "targetPoint" else None
        if xy is not None:
            point.set("x", fmt(xy[0]))
            point.set("y", fmt(xy[1]))


def svg_data_uri(svg_path: Path) -> str:
    raw = svg_path.read_text(encoding="utf-8")
    return "data:image/svg+xml," + quote(raw, safe="")


def replace_image_svg(root: ET.Element, cell_id: str, svg_path: Path, args: argparse.Namespace) -> None:
    el = cell(root, cell_id)
    style_set(
        el,
        shape="image",
        html="1",
        imageAspect="1",
        aspect="fixed",
        editableCssRules=".*",
        image=svg_data_uri(svg_path),
    )
    set_geometry(root, cell_id, x=args.x, y=args.y, width=args.width, height=args.height)


def inspect(path: Path, contains: str | None) -> None:
    root = load(path).getroot()
    for el in root.iter("mxCell"):
        cell_id = el.get("id") or ""
        value = (el.get("value") or "").replace("\n", " ")
        if contains and contains not in cell_id and contains not in value:
            continue
        g = el.find("mxGeometry")
        geo = dict(g.attrib) if g is not None else {}
        print(f"{cell_id}\tvalue={value[:90]}\tgeometry={geo}")


def export_png(drawio_path: Path, out: Path, scale: float) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["drawio", "-x", "-f", "png", "-s", str(scale), "-o", str(out), str(drawio_path)],
        check=True,
    )
    print(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = sub.add_parser("inspect")
    p_inspect.add_argument("drawio", type=Path)
    p_inspect.add_argument("--contains")

    p_backup = sub.add_parser("backup")
    p_backup.add_argument("drawio", type=Path)
    p_backup.add_argument("--label", default="manual_edit")

    p_replace = sub.add_parser("replace-image-svg")
    p_replace.add_argument("drawio", type=Path)
    p_replace.add_argument("--id", required=True)
    p_replace.add_argument("--svg", required=True, type=Path)
    p_replace.add_argument("--x", type=float)
    p_replace.add_argument("--y", type=float)
    p_replace.add_argument("--width", type=float)
    p_replace.add_argument("--height", type=float)
    p_replace.add_argument("--backup-label", default="replace_svg")

    p_geom = sub.add_parser("set-geometry")
    p_geom.add_argument("drawio", type=Path)
    p_geom.add_argument("--id", required=True)
    p_geom.add_argument("--x", type=float)
    p_geom.add_argument("--y", type=float)
    p_geom.add_argument("--width", type=float)
    p_geom.add_argument("--height", type=float)
    p_geom.add_argument("--backup-label", default="geometry")

    p_hide = sub.add_parser("hide-cell")
    p_hide.add_argument("drawio", type=Path)
    p_hide.add_argument("--id", required=True)
    p_hide.add_argument("--backup-label", default="hide")

    p_edge = sub.add_parser("set-edge-points")
    p_edge.add_argument("drawio", type=Path)
    p_edge.add_argument("--id", required=True)
    p_edge.add_argument("--source-x", type=float)
    p_edge.add_argument("--source-y", type=float)
    p_edge.add_argument("--target-x", type=float)
    p_edge.add_argument("--target-y", type=float)
    p_edge.add_argument("--backup-label", default="edge_points")

    p_export = sub.add_parser("export-png")
    p_export.add_argument("drawio", type=Path)
    p_export.add_argument("--out", required=True, type=Path)
    p_export.add_argument("--scale", type=float, default=3)

    args = parser.parse_args()
    path = getattr(args, "drawio", None)

    if args.cmd == "inspect":
        inspect(args.drawio, args.contains)
        return 0

    if args.cmd == "backup":
        print(backup(args.drawio, args.label))
        return 0

    if args.cmd == "export-png":
        export_png(args.drawio, args.out, args.scale)
        return 0

    assert path is not None
    print(f"backup={backup(path, args.backup_label)}")
    tree = load(path)
    root = tree.getroot()

    if args.cmd == "replace-image-svg":
        replace_image_svg(root, args.id, args.svg, args)
    elif args.cmd == "set-geometry":
        set_geometry(root, args.id, x=args.x, y=args.y, width=args.width, height=args.height)
    elif args.cmd == "hide-cell":
        style_set(cell(root, args.id), opacity="0")
        set_geometry(root, args.id, width=1, height=1)
    elif args.cmd == "set-edge-points":
        source = (args.source_x, args.source_y) if args.source_x is not None and args.source_y is not None else None
        target = (args.target_x, args.target_y) if args.target_x is not None and args.target_y is not None else None
        set_edge_points(root, args.id, source, target)

    save(tree, path)
    print(f"updated={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
