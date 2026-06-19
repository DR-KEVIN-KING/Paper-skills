#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def check_inkscape() -> str:
    result = run(["inkscape", "--version"])
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        if result.returncode in {134, -6}:
            raise RuntimeError(
                f"Inkscape exits with code {result.returncode} in the current environment. "
                "On this Mac this means Codex sandbox cannot launch the Homebrew Inkscape app wrapper. "
                "Run this script with escalated/outside-sandbox permissions."
            )
        raise RuntimeError(f"Inkscape is not usable. Exit code {result.returncode}. {detail}")
    return (result.stdout or result.stderr).strip()


def collect_svg_inputs(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for item in inputs:
        if item.is_dir():
            files.extend(sorted(item.glob("*.svg")))
        elif item.is_file() and item.suffix.lower() == ".svg":
            files.append(item)
        else:
            raise FileNotFoundError(f"Not an SVG file or directory: {item}")
    return sorted(dict.fromkeys(path.resolve() for path in files))


def default_output_dir(path: Path) -> Path:
    if path.is_dir():
        return path.with_name(path.name + "_outlined")
    return path.parent.with_name(path.parent.name + "_outlined")


def convert_one(svg: Path, output_dir: Path) -> tuple[Path, str | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / svg.name
    cmd = [
        "inkscape",
        str(svg),
        "--export-text-to-path",
        "--export-plain-svg",
        f"--export-filename={out}",
    ]
    result = run(cmd)
    if result.returncode != 0:
        return out, (result.stderr or result.stdout or f"exit {result.returncode}").strip()
    return out, None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Convert SVG text to paths using Inkscape.")
    parser.add_argument("inputs", nargs="+", type=Path, help="SVG files or directories containing SVG files.")
    parser.add_argument("--out", type=Path, default=None, help="Output directory. Defaults to <input_dir>_outlined.")
    args = parser.parse_args(argv)

    try:
        version = check_inkscape()
        files = collect_svg_inputs(args.inputs)
        if not files:
            print("No SVG files found.", file=sys.stderr)
            return 2
        output_dir = args.out or default_output_dir(args.inputs[0])
        errors: list[tuple[Path, str]] = []
        for svg in files:
            out, error = convert_one(svg, output_dir)
            if error:
                errors.append((svg, error))
            else:
                print(f"outlined: {svg.name} -> {out}")
        if errors:
            print(f"\n{len(errors)} conversion(s) failed:", file=sys.stderr)
            for svg, error in errors:
                print(f"- {svg}: {error}", file=sys.stderr)
            return 1
        print(f"\nInkscape OK: {version}")
        print(f"Converted {len(files)} SVG file(s) into {output_dir}")
        return 0
    except Exception as exc:
        print(f"outline_svg_text_with_inkscape failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
