#!/bin/sh
set -eu

usage() {
  echo "Usage: $0 INPUT_DIR_OR_SVG [--out OUTPUT_DIR]" >&2
  exit 2
}

if [ "$#" -lt 1 ]; then
  usage
fi

INPUT="$1"
shift

OUT=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --out)
      shift
      [ "$#" -gt 0 ] || usage
      OUT="$1"
      shift
      ;;
    *)
      usage
      ;;
  esac
done

if [ -z "$OUT" ]; then
  if [ -d "$INPUT" ]; then
    OUT="${INPUT}_outlined"
  else
    PARENT="$(dirname "$INPUT")"
    OUT="${PARENT}_outlined"
  fi
fi

mkdir -p "$OUT"

COUNT=0
if [ -d "$INPUT" ]; then
  for SVG in "$INPUT"/*.svg; do
    [ -e "$SVG" ] || continue
    BASE="$(basename "$SVG")"
    echo "outline: $BASE"
    inkscape "$SVG" --export-text-to-path --export-plain-svg --export-filename="$OUT/$BASE"
    COUNT=$((COUNT + 1))
  done
elif [ -f "$INPUT" ]; then
  BASE="$(basename "$INPUT")"
  echo "outline: $BASE"
  inkscape "$INPUT" --export-text-to-path --export-plain-svg --export-filename="$OUT/$BASE"
  COUNT=1
else
  echo "Input not found: $INPUT" >&2
  exit 2
fi

echo "Converted $COUNT SVG file(s) into $OUT"
