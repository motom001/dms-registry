#!/usr/bin/env bash
# Baut code/modul.wasm (Tesseract + Leptonica als WebAssembly) und legt die Sprachdaten nach code/daten/.
#
# Die CI ruft das über werkzeuge/bauen.py auf: WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner
# außerhalb des Pakets (Quellen und Zwischenstände der Bibliotheken; bleibt zwischen Läufen erhalten).
# Alle Quellen sind auf feste Commits festgelegt, die Sprachdaten zusätzlich auf SHA-256.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"

LEPTONICA=63aef18d98432b8582a1565e241f7bd2ee9cc8d9   # 1.85.0
TESSERACT=3b7c70e34dea179549ed3e995872e2e019eb8477   # 5.5.1
TESSDATA=87416418657359cb625c412a48b6e1d6d41c29bd    # tessdata_fast
DEU_SHA256=19d219bbb6672c869d20a9636c6816a81eb9a71796cb93ebe0cb1530e2cdb22d
ENG_SHA256=7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2

TOOLCHAIN="$WASI_SDK/share/cmake/wasi-sdk.cmake"
WASI_FLAGS="-D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS -D_WASI_EMULATED_MMAN"
JOBS=$(nproc 2>/dev/null || echo 2)

# Ein Repository auf genau einem Commit (flach, nur dieser Stand).
hole() {
  local ordner=$1 url=$2 commit=$3
  if [ "$(git -C "$BAU/$ordner" rev-parse HEAD 2>/dev/null)" != "$commit" ]; then
    rm -rf "${BAU:?}/$ordner"
    git init -q "$BAU/$ordner"
    git -C "$BAU/$ordner" fetch -q --depth 1 "$url" "$commit"
    git -C "$BAU/$ordner" -c advice.detachedHead=false checkout -q FETCH_HEAD
  fi
}

# Leptonica (ohne Bildformat-Bibliotheken: Bilder kommen als Graustufen-Rohdaten vom DMS).
if [ ! -f "$BAU/prefix/stand-leptonica" ] || [ "$(cat "$BAU/prefix/stand-leptonica")" != "$LEPTONICA" ]; then
  hole leptonica https://github.com/DanBloomberg/leptonica "$LEPTONICA"
  rm -rf "$BAU/lep-build" "$BAU/prefix"
  cmake -S "$BAU/leptonica" -B "$BAU/lep-build" -G Ninja -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$BAU/prefix" -DBUILD_PROG=OFF -DBUILD_SHARED_LIBS=OFF -DSW_BUILD=OFF \
    -DENABLE_GIF=OFF -DENABLE_JPEG=OFF -DENABLE_OPENJPEG=OFF -DENABLE_PNG=OFF -DENABLE_TIFF=OFF -DENABLE_WEBP=OFF -DENABLE_ZLIB=OFF \
    -DCMAKE_C_FLAGS="$WASI_FLAGS -Wno-implicit-function-declaration" >/dev/null
  cmake --build "$BAU/lep-build" -j "$JOBS" >/dev/null
  cmake --install "$BAU/lep-build" >/dev/null
  echo "$LEPTONICA" > "$BAU/prefix/stand-leptonica"
fi

# Tesseract (nur die Bibliothek; ohne Threads, Netz, Archive, TIFF, ohne x86-Befehlssätze).
if [ ! -f "$BAU/tess-build/libtesseract.a" ] || [ "$(cat "$BAU/tess-build/stand" 2>/dev/null)" != "$TESSERACT" ]; then
  hole tesseract https://github.com/tesseract-ocr/tesseract "$TESSERACT"
  rm -rf "$BAU/tess-build"
  cmake -S "$BAU/tesseract" -B "$BAU/tess-build" -G Ninja -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_SHARED_LIBS=OFF -DBUILD_TESTS=OFF -DBUILD_TRAINING_TOOLS=OFF -DDISABLE_ARCHIVE=ON -DDISABLE_CURL=ON -DDISABLE_TIFF=ON \
    -DENABLE_LTO=OFF -DENABLE_NATIVE=OFF -DGRAPHICS_DISABLED=ON -DOPENMP_BUILD=OFF -DUSE_SYSTEM_ICU=OFF \
    -DHAVE_AVX=OFF -DHAVE_AVX2=OFF -DHAVE_FMA=OFF -DHAVE_SSE4_1=OFF -DLEPT_TIFF_RESULT=1 \
    -DLeptonica_DIR="$BAU/prefix/lib/cmake/leptonica" \
    -DCMAKE_CXX_FLAGS="$WASI_FLAGS -include $CODE/wasi-thread-shim.h -I$CODE/stub" >/dev/null
  cmake --build "$BAU/tess-build" --target libtesseract -j "$JOBS" >/dev/null
  echo "$TESSERACT" > "$BAU/tess-build/stand"
fi

# Das Modul (DMS-Paket-ABI 1).
"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -c "$CODE/wasi-compat.c" -o "$BAU/wasi-compat.o"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -fno-exceptions -mexec-model=reactor \
  -include "$CODE/wasi-thread-shim.h" -I "$BAU/tesseract/include" -I "$BAU/tess-build/include" -I "$BAU/prefix/include" \
  "$CODE/texterkennung.cpp" "$BAU/wasi-compat.o" "$BAU/tess-build/libtesseract.a" "$BAU/prefix/lib/libleptonica.a" \
  -lwasi-emulated-signal -lwasi-emulated-process-clocks -lwasi-emulated-mman \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

# Sprachdaten (tessdata_fast, Apache-2.0).
# Nur die zwei Dateien laden, nicht das ganze Repository (Teilklon ohne Inhalte, dann gezielt auschecken).
if [ "$(git -C "$BAU/tessdata" rev-parse HEAD 2>/dev/null)" != "$TESSDATA" ] || [ ! -f "$BAU/tessdata/eng.traineddata" ]; then
  rm -rf "${BAU:?}/tessdata"
  git init -q "$BAU/tessdata"
  git -C "$BAU/tessdata" fetch -q --depth 1 --filter=blob:none https://github.com/tesseract-ocr/tessdata_fast "$TESSDATA"
  git -C "$BAU/tessdata" -c advice.detachedHead=false checkout -q FETCH_HEAD -- deu.traineddata eng.traineddata
  git -C "$BAU/tessdata" update-ref HEAD FETCH_HEAD
fi
mkdir -p "$CODE/daten"
cp "$BAU/tessdata/deu.traineddata" "$BAU/tessdata/eng.traineddata" "$CODE/daten/"
echo "$DEU_SHA256  $CODE/daten/deu.traineddata
$ENG_SHA256  $CODE/daten/eng.traineddata" | sha256sum -c --quiet -
