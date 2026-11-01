#!/usr/bin/env bash
# Alle Tests des Pakets: Modul bauen (mit Test des Barcode-Lesers), Beispiel-PDFs erzeugen, das Modul mit einer
# Nachbildung des DMS laufen lassen und prüfen, ob vorlage/trennblatt.pdf zum Skript passt.
#
#   pakete/trennblatt/tests/pruefen.sh
#
# Braucht: cc, python3, node, pdftoppm und pdfinfo (Poppler); WASI_SDK (sonst lädt werkzeuge/wasi-sdk.sh es).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
WURZEL="$(cd "$PAKET/../.." && pwd)"
export WASI_SDK="${WASI_SDK:-$("$WURZEL/werkzeuge/wasi-sdk.sh")}"
python3 "$WURZEL/werkzeuge/bauen.py" "$PAKET"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/beispiel.py" "$TMP" >/dev/null
node "$PAKET/tests/modul_test.mjs" "$TMP"

python3 -B "$PAKET/vorlage/trennblatt.py" "$TMP/trennblatt.pdf" >/dev/null
if ! cmp -s "$TMP/trennblatt.pdf" "$PAKET/vorlage/trennblatt.pdf"; then
  echo "✗ vorlage/trennblatt.pdf passt nicht zu vorlage/trennblatt.py – neu erzeugen: python3 vorlage/trennblatt.py"
  exit 1
fi
echo "✓ vorlage/trennblatt.pdf ist aktuell"
