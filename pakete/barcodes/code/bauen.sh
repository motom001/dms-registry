#!/usr/bin/env bash
# Baut code/modul.wasm: Codes lesen mit zxing-cpp (QR, Aztec, Data Matrix, PDF417, EAN/UPC, Code 39/93/128, ITF …)
# und vCards in Vorschläge für „Aus Dokument ausfüllen“ übersetzen.
#
# Die CI ruft das über werkzeuge/bauen.py auf: BAU zeigt auf einen Arbeitsordner außerhalb des Pakets (Quellen und
# Bau von zxing-cpp; bleibt zwischen Läufen erhalten). Das WASI-SDK aus WASI_SDK (Version 25) reicht hier nicht:
# zxing-cpp wirft intern Ausnahmen und fängt sie selbst – das kann erst WASI-SDK 33 (Wasm-Ausnahmen mit libunwind).
# Das Skript holt sich Version 33 über werkzeuge/wasi-sdk.sh (feste Prüfsumme).
# zxing-cpp (Apache-2.0, darin libzueci unter BSD-3-Clause) kommt vom Original auf GitHub, fest auf den Commit des
# Tags v2.3.0; nach dem Holen prüft das Skript den Commit-Hash. Lizenztexte: code/lizenzen/.
set -euo pipefail
: "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
WURZEL="$(cd "$CODE/../../.." && pwd)"
SDK="$(WASI_SDK_VERSION=33 "$WURZEL/werkzeuge/wasi-sdk.sh")"
ZXING=d6068bcebeb8fd9f0d35a99b00d202be86a14dbe   # zxing-cpp v2.3.0
QUELLE=https://github.com/zxing-cpp/zxing-cpp
EH=(-fwasm-exceptions -mllvm -wasm-use-legacy-eh=false)

if [ "$(git -C "$BAU/zxing-cpp" rev-parse HEAD 2>/dev/null)" != "$ZXING" ]; then
  rm -rf "${BAU:?}/zxing-cpp" "${BAU:?}/zxing-bau"
  git init -q "$BAU/zxing-cpp"
  git -C "$BAU/zxing-cpp" fetch -q --depth 1 "$QUELLE" "$ZXING"
  git -C "$BAU/zxing-cpp" -c advice.detachedHead=false checkout -q FETCH_HEAD
  ist=$(git -C "$BAU/zxing-cpp" rev-parse HEAD)
  [ "$ist" = "$ZXING" ] || { echo "zxing-cpp: $ist, erwartet $ZXING" >&2; exit 1; }
fi

# Nur die Leser, keine Schreiber, Beispiele oder Tests; als statische Bibliothek.
if [ ! -f "$BAU/zxing-bau/core/libZXing.a" ]; then
  cmake -S "$BAU/zxing-cpp" -B "$BAU/zxing-bau" -DCMAKE_TOOLCHAIN_FILE="$SDK/share/cmake/wasi-sdk-p1.cmake" \
    -DWASI_SDK_PREFIX="$SDK" -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DZXING_READERS=ON -DZXING_WRITERS=OFF \
    -DZXING_EXAMPLES=OFF -DZXING_BLACKBOX_TESTS=OFF -DZXING_UNIT_TESTS=OFF -DZXING_PYTHON_MODULE=OFF -DZXING_C_API=OFF \
    -DCMAKE_CXX_FLAGS="${EH[*]}" -DCMAKE_C_FLAGS="-fwasm-exceptions" > /dev/null
  cmake --build "$BAU/zxing-bau" -j "$(nproc)" > /dev/null
fi

"$SDK/bin/clang++" --target=wasm32-wasip1 -std=c++20 -O2 -Wall -Werror "${EH[@]}" -mexec-model=reactor \
  -I "$BAU/zxing-cpp/core/src" "$CODE/barcodes.cpp" "$BAU/zxing-bau/core/libZXing.a" -fwasm-exceptions -lunwind \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
