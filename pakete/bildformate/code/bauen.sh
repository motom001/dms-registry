#!/usr/bin/env bash
# Baut code/modul.wasm: Bildformate lesen (libtiff, libwebp, stb_image) und als PDF, PNG oder JPEG schreiben
# (libjpeg-turbo, zlib, stb_image_write).
#
# Die CI ruft das über werkzeuge/bauen.py auf: WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner
# außerhalb des Pakets (Quellen und Zwischenstände der Bibliotheken; bleibt zwischen Läufen erhalten).
# Alle Quellen sind auf feste Commits festgelegt; nach dem Holen prüft hole() den Commit-Hash.
#
# libtiff kommt vom Original (gitlab.com/libtiff/libtiff). Wo gitlab.com nicht erreichbar ist, geht für lokale
# Bauten der GitHub-Spiegel mit demselben Commit:
#   LIBTIFF_QUELLE=https://github.com/libsdl-org/libtiff WASI_SDK=… python3 werkzeuge/bauen.py pakete/bildformate
# Die CI setzt LIBTIFF_QUELLE nicht und baut damit immer vom Original.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"

ZLIB=51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf       # 1.3.1
JPEG=4e151a4ad91001b3aa8c2ece2205c15f487ce320       # libjpeg-turbo 3.1.2
TIFF=5fe20d0e9aba49a6a350ed533459d1505203838f       # libtiff 4.7.1 (Tag v4.7.1)
WEBP=a4d7a715337ded4451fec90ff8ce79728e04126c       # libwebp 1.5.0
STB=d14d46f6b44456eb88beac58cba833a4135d4c89        # stb (stb_image 2.30, stb_image_write 1.16)
LIBTIFF_QUELLE="${LIBTIFF_QUELLE:-https://gitlab.com/libtiff/libtiff.git}"

TOOLCHAIN="$WASI_SDK/share/cmake/wasi-sdk.cmake"
WASI_FLAGS="-D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS -D_WASI_EMULATED_MMAN"
PREFIX="$BAU/prefix"
JOBS=$(nproc 2>/dev/null || echo 2)

# Ein Repository auf genau einem Commit (flach, nur dieser Stand). Mit viertem Argument holt es diesen Tag
# statt des Commits – der Tag muss dann auf genau diesen Commit zeigen.
hole() {
  local ordner=$1 url=$2 commit=$3 ref=${4:-$3}
  if [ "$(git -C "$BAU/$ordner" rev-parse HEAD 2>/dev/null)" != "$commit" ] || [ "$(cat "$BAU/$ordner.quelle" 2>/dev/null)" != "$url" ]; then
    rm -rf "${BAU:?}/$ordner" "$BAU/$ordner.quelle"
    git init -q "$BAU/$ordner"
    git -C "$BAU/$ordner" fetch -q --depth 1 "$url" "$ref"
    git -C "$BAU/$ordner" -c advice.detachedHead=false checkout -q FETCH_HEAD
    local ist
    ist=$(git -C "$BAU/$ordner" rev-parse HEAD)
    if [ "$ist" != "$commit" ]; then
      echo "$ordner: $url $ref ist $ist, erwartet $commit" >&2
      exit 1
    fi
    echo "$url" > "$BAU/$ordner.quelle"
  fi
}
# Schon gebaut (gleicher Commit)?
fertig() { [ -f "$PREFIX/stand-$1" ] && [ "$(cat "$PREFIX/stand-$1")" = "$2" ]; }
cmake_wasi() {
  local quelle=$1 ziel=$2; shift 2
  rm -rf "$ziel"
  cmake -S "$quelle" -B "$ziel" -G Ninja -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" -DBUILD_SHARED_LIBS=OFF -DCMAKE_C_FLAGS="$WASI_FLAGS" "$@" >/dev/null
  cmake --build "$ziel" -j "$JOBS" >/dev/null
  cmake --install "$ziel" >/dev/null
}
mkdir -p "$PREFIX/lib" "$PREFIX/include"

# zlib (nur die Bibliothek, ohne gz*-Dateifunktionen): Deflate in TIFF, PNG und PDF.
if ! fertig zlib "$ZLIB"; then
  hole zlib https://github.com/madler/zlib "$ZLIB"
  rm -rf "$BAU/zlib-o" && mkdir -p "$BAU/zlib-o"
  for f in adler32 compress crc32 deflate infback inffast inflate inftrees trees uncompr zutil; do
    "$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -c "$BAU/zlib/$f.c" -o "$BAU/zlib-o/$f.o"
  done
  rm -f "$PREFIX/lib/libz.a"
  "$WASI_SDK/bin/llvm-ar" rcs "$PREFIX/lib/libz.a" "$BAU"/zlib-o/*.o
  cp "$BAU/zlib/zlib.h" "$BAU/zlib/zconf.h" "$PREFIX/include/"
  echo "$ZLIB" > "$PREFIX/stand-zlib"
fi

# libjpeg-turbo (ohne SIMD, ohne TurboJPEG-Schnittstelle): JPEG in TIFF lesen, JPEG schreiben.
if ! fertig jpeg "$JPEG"; then
  hole jpeg https://github.com/libjpeg-turbo/libjpeg-turbo "$JPEG"
  cmake_wasi "$BAU/jpeg" "$BAU/jpeg-build" -DENABLE_SHARED=OFF -DENABLE_STATIC=ON -DWITH_SIMD=OFF -DWITH_TURBOJPEG=OFF \
    -DWITH_TOOLS=OFF -DWITH_TESTS=OFF -DCMAKE_SYSTEM_PROCESSOR=wasm32
  echo "$JPEG" > "$PREFIX/stand-jpeg"
fi

# libtiff (Deflate/LZW/PackBits/CCITT G3+G4/JPEG; ohne Werkzeuge, Tests und weitere Bibliotheken).
# Der Stand merkt sich auch die Quelle: Eine im Cache vom Spiegel gebaute libtiff baut die CI neu vom Original.
if ! fertig tiff "$TIFF $LIBTIFF_QUELLE"; then
  echo "  libtiff aus $LIBTIFF_QUELLE"
  hole tiff "$LIBTIFF_QUELLE" "$TIFF" refs/tags/v4.7.1
  # setjmp/longjmp gibt es in WASI nicht: code/stub/setjmp.h (Fehler in libjpeg beenden den Aufruf).
  WASI_FLAGS="$WASI_FLAGS -I$CODE/stub" cmake_wasi "$BAU/tiff" "$BAU/tiff-build" -Dtiff-tools=OFF -Dtiff-tests=OFF -Dtiff-contrib=OFF -Dtiff-docs=OFF \
    -Dcxx=OFF -Dzlib=ON -Djpeg=ON -Dold-jpeg=OFF -Dwebp=OFF -Dlzma=OFF -Dzstd=OFF -Djbig=OFF -Dlerc=OFF -Dlibdeflate=OFF \
    -Dpixarlog=OFF \
    -DZLIB_INCLUDE_DIR="$PREFIX/include" -DZLIB_LIBRARY="$PREFIX/lib/libz.a" \
    -DJPEG_INCLUDE_DIR="$PREFIX/include" -DJPEG_LIBRARY="$PREFIX/lib/libjpeg.a"
  echo "$TIFF $LIBTIFF_QUELLE" > "$PREFIX/stand-tiff"
fi

# libwebp (nur Lesen; ohne SIMD und Threads).
if ! fertig webp "$WEBP"; then
  hole webp https://github.com/webmproject/libwebp "$WEBP"
  cmake_wasi "$BAU/webp" "$BAU/webp-build" -DWEBP_BUILD_ANIM_UTILS=OFF -DWEBP_BUILD_CWEBP=OFF -DWEBP_BUILD_DWEBP=OFF \
    -DWEBP_BUILD_GIF2WEBP=OFF -DWEBP_BUILD_IMG2WEBP=OFF -DWEBP_BUILD_VWEBP=OFF -DWEBP_BUILD_WEBPINFO=OFF -DWEBP_BUILD_WEBPMUX=OFF \
    -DWEBP_BUILD_EXTRAS=OFF -DWEBP_BUILD_LIBWEBPMUX=OFF -DWEBP_ENABLE_SIMD=OFF -DWEBP_USE_THREAD=OFF -DWEBP_NEAR_LOSSLESS=OFF
  echo "$WEBP" > "$PREFIX/stand-webp"
fi

# stb_image (GIF, BMP lesen) und stb_image_write (PNG schreiben): nur zwei Kopfdateien.
hole stb https://github.com/nothings/stb "$STB"

# Das Modul (DMS-Paket-ABI 1).
"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -c "$CODE/wasi-compat.c" -o "$BAU/wasi-compat.o"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor $WASI_FLAGS \
  -I "$PREFIX/include" -I "$BAU/stb" \
  "$CODE/bildformate.cpp" "$BAU/wasi-compat.o" \
  "$PREFIX/lib/libtiff.a" "$PREFIX/lib/libwebp.a" "$PREFIX/lib/libsharpyuv.a" "$PREFIX/lib/libjpeg.a" "$PREFIX/lib/libz.a" \
  -lwasi-emulated-signal -lwasi-emulated-process-clocks -lwasi-emulated-mman \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

# Test der PDF-Ausgabe und der Bildwahl (code/ausgabe.h) – nativ, wenn ein C++-Compiler da ist.
if command -v c++ >/dev/null 2>&1; then
  c++ -std=c++17 -O2 -Wall -Werror -I "$CODE" "$CODE/../tests/ausgabe_test.cpp" -o "$BAU/ausgabe_test"
  "$BAU/ausgabe_test" >"$BAU/ausgabe_test.log" || { cat "$BAU/ausgabe_test.log"; exit 1; }
  echo "  PDF-Ausgabe: $(grep -c '^ok' "$BAU/ausgabe_test.log") Prüfungen bestanden"
fi
