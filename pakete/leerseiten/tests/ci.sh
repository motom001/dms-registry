#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat: künstliche Scans (leer, Lochung, Bleistift,
# Stempel, durchscheinende Schrift, Staub) erzeugen und das Modul mit einer Nachbildung von Ablago prüfen.
# Braucht: python3, node, Poppler (pdftoppm, pdfinfo; wird bei Bedarf installiert).
set -euo pipefail
if ! command -v pdftoppm >/dev/null || ! command -v pdfinfo >/dev/null; then sudo apt-get install -y -qq poppler-utils >/dev/null; fi
HIER="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$HIER/scans.py" "$TMP" >/dev/null
node "$HIER/modul_test.mjs" "$TMP"
