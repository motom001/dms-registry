#!/usr/bin/env bash
# Baut code/modul.wasm (die CI ruft das über werkzeuge/bauen.py auf; WASI_SDK zeigt auf das WASI-SDK).
# Keine fremden Bibliotheken: Die Erkennung leerer Seiten teilt das Paket mit „Trennblatt“ – gemeinsam/leerseite/.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
GEMEINSAM="$(cd "$CODE/../../../gemeinsam/leerseite" && pwd)"

"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor -I "$GEMEINSAM" \
  "$CODE/leerseiten.cpp" \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
