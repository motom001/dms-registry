#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Paket mit dem echten Modell gebaut hat (code/modul.wasm und
# code/daten/): Tokenizer und Ablauf mit dem kleinen Testmodell, dann das echte Modell – Ähnlichkeit auf Deutsch
# und Englisch, Laufzeit, Speicher.
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/kleines_modell.py" "$TMP/modell"
python3 -B "$PAKET/code/umwandeln.py" "$TMP/modell" "$TMP/daten" 32
node "$PAKET/tests/modul_test.mjs" klein "$TMP/daten"
node "$PAKET/tests/modul_test.mjs" echt "$PAKET/code/daten"
