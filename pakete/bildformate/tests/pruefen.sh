#!/usr/bin/env bash
# Alle Tests des Pakets lokal: Modul bauen (mit dem nativen Test der PDF-Ausgabe), dann wie in der CI (tests/ci.sh).
#
#   pakete/bildformate/tests/pruefen.sh
#
# Braucht: c++, cmake, ninja, python3 mit Pillow, node, Poppler; WASI_SDK (sonst lädt werkzeuge/wasi-sdk.sh es).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
WURZEL="$(cd "$PAKET/../.." && pwd)"
export WASI_SDK="${WASI_SDK:-$("$WURZEL/werkzeuge/wasi-sdk.sh")}"
python3 "$WURZEL/werkzeuge/bauen.py" "$PAKET"
bash "$PAKET/tests/ci.sh"
