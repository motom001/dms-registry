#!/usr/bin/env bash
# Tests des gebauten Moduls in der CI (werkzeuge/bauen.py hat code/modul.wasm schon gebaut): Testdateien mit Pillow
# erzeugen, das Modul mit einer Nachbildung des DMS laufen lassen, die Archivfassungen prüfen (Seiten, Wörter an ihrer
# Stelle, qpdf) und mit veraPDF auf PDF/A-2b.
# Braucht: python3 mit Pillow (wird bei Bedarf installiert), node, Poppler (pdftoppm, pdftotext, pdfinfo), qpdf, Java.
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
python3 -c 'import PIL' 2>/dev/null || pip install --quiet pillow
if ! command -v pdftoppm >/dev/null || ! command -v qpdf >/dev/null; then sudo apt-get install -y -qq poppler-utils qpdf >/dev/null; fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/beispiele.py" erzeuge "$TMP"
node "$PAKET/tests/modul_test.mjs" "$TMP"
python3 -B "$PAKET/tests/beispiele.py" vergleiche "$TMP"
bash "$PAKET/tests/verapdf.sh" "$TMP"/*.pdfa.pdf
