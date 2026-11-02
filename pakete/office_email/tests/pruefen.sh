#!/usr/bin/env bash
# Alle Tests des Pakets lokal: Modul bauen, dann wie in der CI (tests/ci.sh).
#
#   pakete/office_email/tests/pruefen.sh
#
# Braucht: python3, node; WASI_SDK (sonst lädt werkzeuge/wasi-sdk.sh es).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
WURZEL="$(cd "$PAKET/../.." && pwd)"
export WASI_SDK="${WASI_SDK:-$("$WURZEL/werkzeuge/wasi-sdk.sh")}"
python3 "$WURZEL/werkzeuge/bauen.py" "$PAKET"
bash "$PAKET/tests/ci.sh"
