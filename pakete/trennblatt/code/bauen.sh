#!/usr/bin/env bash
# Baut code/modul.wasm (die CI ruft das über werkzeuge/bauen.py auf; WASI_SDK zeigt auf das WASI-SDK).
# Keine fremden Bibliotheken: Der Barcode-Leser steht in code/barcode.c.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
BAU="${BAU:-$(mktemp -d)}"

"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -Wall -Werror -c "$CODE/barcode.c" -o "$BAU/barcode.o"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor \
  "$CODE/trennblatt.cpp" "$BAU/barcode.o" \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

# Test des Barcode-Lesers (künstliche, schiefe und verrauschte Scans) – nativ, wenn ein C-Compiler da ist.
if command -v cc >/dev/null 2>&1; then
  cc -O2 -Wall -Werror -I "$CODE" "$CODE/../tests/barcode_test.c" "$CODE/barcode.c" -lm -o "$BAU/barcode_test"
  "$BAU/barcode_test" >"$BAU/barcode_test.log" || { cat "$BAU/barcode_test.log"; exit 1; }
  echo "  Barcode-Leser: $(grep -c '^✓' "$BAU/barcode_test.log") Prüfungen bestanden"
fi
