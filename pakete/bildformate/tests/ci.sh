#!/usr/bin/env bash
# Tests des gebauten Moduls in der CI (werkzeuge/bauen.py hat code/modul.wasm schon gebaut): Testbilder mit Pillow
# erzeugen, das Modul mit einer Nachbildung des DMS laufen lassen, die Fassungen mit den Bildern vergleichen.
# Braucht: python3 mit Pillow (wird bei Bedarf installiert), node, pdfimages und pdfinfo (Poppler).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
python3 -c 'import PIL' 2>/dev/null || pip install --quiet pillow
if ! command -v pdfimages >/dev/null; then sudo apt-get install -y -qq poppler-utils >/dev/null; fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/beispiele.py" erzeuge "$TMP"
node "$PAKET/tests/modul_test.mjs" "$TMP"
python3 -B "$PAKET/tests/beispiele.py" vergleiche "$TMP"
