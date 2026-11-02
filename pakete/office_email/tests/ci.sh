#!/usr/bin/env bash
# Tests des gebauten Moduls in der CI (werkzeuge/bauen.py hat code/modul.wasm schon gebaut): Testdateien mit der
# Python-Standardbibliothek erzeugen und das Modul mit einer Nachbildung des DMS laufen lassen.
# Braucht: python3, node.
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/beispiele.py" "$TMP"
node "$PAKET/tests/modul_test.mjs" "$TMP"
