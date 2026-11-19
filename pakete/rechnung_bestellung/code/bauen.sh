#!/usr/bin/env bash
# Baut code/modul.wasm (die CI ruft das über werkzeuge/bauen.py auf; WASI_SDK zeigt auf das WASI-SDK, BAU auf einen
# Arbeitsordner außerhalb des Pakets). Keine fremden Bibliotheken. Danach – wenn ein C++-Compiler da ist – die
# Tests der Berechnung nativ (tests/rechnung_test.cpp).
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -std=c++17 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor \
  "$CODE/rechnungen.cpp" -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
if command -v c++ >/dev/null 2>&1; then
  c++ -std=c++17 -O2 -Wall -Werror -I "$CODE" "$CODE/../tests/rechnung_test.cpp" -o "$BAU/rechnungen_test"
  "$BAU/rechnungen_test" >"$BAU/rechnungen_test.log" || { cat "$BAU/rechnungen_test.log"; exit 1; }
  echo "  Rechnungen: $(grep -c '^ok' "$BAU/rechnungen_test.log") Prüfungen bestanden"
fi
