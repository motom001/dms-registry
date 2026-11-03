#!/usr/bin/env bash
# Test des gebauten Moduls in der CI (werkzeuge/bauen.py hat code/modul.wasm und code/daten/ schon gebaut): zwei
# erfundene Scanseiten mit Pillow, das Modul mit einer Nachbildung des DMS, Text und Wortpositionen prüfen.
# Braucht: python3 mit Pillow (wird bei Bedarf installiert), node.
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
python3 -c 'import PIL' 2>/dev/null || pip install --quiet pillow
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/beispiele.py" "$TMP"
node "$PAKET/tests/modul_test.mjs" "$TMP"
