#!/usr/bin/env bash
# Baut code/modul.wasm (die CI ruft das über werkzeuge/bauen.py auf; WASI_SDK zeigt auf das WASI-SDK, BAU auf einen
# Arbeitsordner außerhalb des Pakets). Keine fremden Bibliotheken. Danach – wenn ein C++-Compiler da ist – die Tests der
# Logik nativ (tests/kba_test.cpp).
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -std=c++17 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor \
  "$CODE/kba.cpp" -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
if command -v c++ >/dev/null 2>&1; then
  c++ -std=c++17 -O2 -Wall -Werror -I "$CODE" "$CODE/../tests/kba_test.cpp" -o "$BAU/kba_test"
  "$BAU/kba_test" "$CODE/../tests" >"$BAU/kba_test.log" || { cat "$BAU/kba_test.log"; exit 1; }
  echo "  Abruf beim KBA: $(grep -c '^ok' "$BAU/kba_test.log") Prüfungen bestanden"
fi
