#!/usr/bin/env bash
# Baut code/modul.wasm (die CI ruft das über werkzeuge/bauen.py auf; WASI_SDK zeigt auf das WASI-SDK, BAU auf einen
# Arbeitsordner außerhalb des Pakets). Keine fremden Bibliotheken. Danach – wenn ein C++-Compiler da ist – die
# Tests der Logik nativ (tests/stand_test.cpp).
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -std=c++17 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor \
  "$CODE/compliance.cpp" -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
if command -v c++ >/dev/null 2>&1; then
  c++ -std=c++17 -O2 -Wall -Werror -I "$CODE" "$CODE/../tests/stand_test.cpp" -o "$BAU/compliance_test"
  "$BAU/compliance_test" >"$BAU/compliance_test.log" || { cat "$BAU/compliance_test.log"; exit 1; }
  echo "  Logik: $(grep -c '^ok' "$BAU/compliance_test.log") Prüfungen bestanden"
fi
