#!/usr/bin/env bash
# Baut code/modul.wasm aus dem Quellcode. Die CI ruft das über werkzeuge/bauen.py auf:
#   WASI_SDK  Pfad des WASI-SDK (Clang für WebAssembly)
#   BAU       Arbeitsordner außerhalb des Pakets (für Bibliotheken und Zwischenstände)
# Beispiel für C; für Rust z. B.: cargo build --release --target wasm32-wasip1 (Link-Argument --import-memory).
set -euo pipefail
cd "$(dirname "$0")"
"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -Wall \
  -mexec-model=reactor -Wl,--import-memory -Wl,--strip-all \
  -o modul.wasm *.c
