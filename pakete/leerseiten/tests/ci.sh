#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat: künstliche Scans (leer, Lochung, Bleistift,
# Stempel, durchscheinende Schrift, Staub) erzeugen und das Modul mit einer Nachbildung von Ablago prüfen.
set -euo pipefail
HIER="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$HIER/scans.py" "$TMP" >/dev/null
node "$HIER/modul_test.mjs" "$TMP"
