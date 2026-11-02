#!/usr/bin/env bash
# Alle Tests des Pakets ohne Netz: Modul bauen und mit einer Nachbildung des DMS und des KI-Dienstes prüfen.
#
#   pakete/ki_assistent/tests/pruefen.sh
#
# Braucht: node; WASI_SDK (sonst lädt werkzeuge/wasi-sdk.sh es).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
WURZEL="$(cd "$PAKET/../.." && pwd)"
export WASI_SDK="${WASI_SDK:-$("$WURZEL/werkzeuge/wasi-sdk.sh")}"
bash "$PAKET/code/bauen.sh"
node "$PAKET/tests/modul_test.mjs"
