#!/usr/bin/env bash
# Alle Tests des Pakets ohne Netz: Modul bauen mit dem kleinen Testmodell (tests/kleines_modell.py), Tokenizer und
# Ablauf prüfen, Laufzeit mit einem Zufallsmodell in voller Größe messen.
#
#   pakete/ki_aehnlich/tests/pruefen.sh
#
# Braucht: python3, node; WASI_SDK (sonst lädt werkzeuge/wasi-sdk.sh es). Das echte Modell prüft tests/ci.sh.
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
WURZEL="$(cd "$PAKET/../.." && pwd)"
export WASI_SDK="${WASI_SDK:-$("$WURZEL/werkzeuge/wasi-sdk.sh")}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
python3 -B "$PAKET/tests/kleines_modell.py" "$TMP/modell"
KI_MODELL_ORDNER="$TMP/modell" KI_DIM=32 BAU="$TMP/bau" bash "$PAKET/code/bauen.sh"
node "$PAKET/tests/modul_test.mjs" klein "$PAKET/code/daten"
node "$PAKET/tests/modul_test.mjs" gross "$PAKET/code/daten"
