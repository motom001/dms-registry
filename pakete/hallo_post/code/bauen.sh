#!/usr/bin/env bash
# Baut code/modul.wasm (die CI ruft das über werkzeuge/bauen.py auf; WASI_SDK zeigt auf das WASI-SDK).
set -euo pipefail
cd "$(dirname "$0")"
"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -Wall -Werror \
  -mexec-model=reactor -Wl,--import-memory -Wl,--strip-all \
  -o modul.wasm hallo.c
