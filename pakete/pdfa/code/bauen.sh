#!/usr/bin/env bash
# Baut code/modul.wasm (PDF/A-2b schreiben: zlib, libjpeg-turbo, stb_image) und legt das ICC-Profil (sRGB), die
# Schrift der Textebene (GlyphLessFont) und die Schrift für E-Mails (Noto Sans, vier Schnitte) nach code/daten/.
# Den Mail-Zerleger teilt das Paket mit „Office und E-Mail“: gemeinsam/mail/ im Repository (#143).
#
# Die CI ruft das über werkzeuge/bauen.py auf: WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner
# außerhalb des Pakets (Quellen und Zwischenstände der Bibliotheken; bleibt zwischen Läufen erhalten).
# Alle Quellen sind auf feste Commits festgelegt; nach dem Holen prüft hole() den Commit, die Daten zusätzlich SHA-256.
# Bibliotheken und Commits wie im Paket Bildformate.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
GEMEINSAM="$(cd "$CODE/../../../gemeinsam/mail" && pwd)"
VERSION="$(sed -n 's/^version: *//p' "$CODE/../manifest.yaml")"

ZLIB=51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf       # 1.3.1
JPEG=4e151a4ad91001b3aa8c2ece2205c15f487ce320       # libjpeg-turbo 3.1.2
STB=d14d46f6b44456eb88beac58cba833a4135d4c89        # stb (stb_image 2.30)
TESSERACT=3b7c70e34dea179549ed3e995872e2e019eb8477  # 5.5.1 – nur tessdata/pdf.ttf (GlyphLessFont, Apache-2.0)
ICC=bdd84663061bc4ae95ca70decff54f581e27f702        # saucecontrol/Compact-ICC-Profiles – profiles/sRGB-v2-magic.icc (CC0-1.0)
NOTO=86ce02c0fe7890f5936c5dffb26fca0797d1be64       # notofonts/notofonts.github.io – Noto Sans 2.x, unhinted TTF (SIL OFL 1.1)
NOTO_SHA256="f3961a9cde016d41a4879aecda1474d3a36d6bf54fa0e4643de029cc2248b0e8 noto-sans.ttf NotoSans-Regular.ttf
87cb2d84472a7d66da659ee47b6cdb9552326e8c128245231f191b6ac72529d9 noto-sans-fett.ttf NotoSans-Bold.ttf
678288f868807d4d64a6f3b51466871d117d915780381ce9d0ed4b3bcbd06d37 noto-sans-kursiv.ttf NotoSans-Italic.ttf
3d367743f371f28671d2764e911a53d7c20ec9b6aa8791d059e7090389fc52a5 noto-sans-fettkursiv.ttf NotoSans-BoldItalic.ttf"
SCHRIFT_SHA256=c7845420925a23d88ed830a63957b8af85a66a8daf8d9fc90e843673b2ef1a59
ICC_SHA256=af4efe28f6d311799865f325ba39184a2e978b113ca74124d60af7de22b105f4

TOOLCHAIN="$WASI_SDK/share/cmake/wasi-sdk.cmake"
WASI_FLAGS="-D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS -D_WASI_EMULATED_MMAN"
PREFIX="$BAU/prefix"
JOBS=$(nproc 2>/dev/null || echo 2)

# Ein Repository auf genau einem Commit (flach, nur dieser Stand).
hole() {
  local ordner=$1 url=$2 commit=$3
  if [ "$(git -C "$BAU/$ordner" rev-parse HEAD 2>/dev/null)" != "$commit" ]; then
    rm -rf "${BAU:?}/$ordner"
    git init -q "$BAU/$ordner"
    git -C "$BAU/$ordner" fetch -q --depth 1 "$url" "$commit"
    git -C "$BAU/$ordner" -c advice.detachedHead=false checkout -q FETCH_HEAD
    local ist
    ist=$(git -C "$BAU/$ordner" rev-parse HEAD)
    if [ "$ist" != "$commit" ]; then echo "$ordner: $url ist $ist, erwartet $commit" >&2; exit 1; fi
  fi
}
# Nur einzelne Dateien eines Repositorys (Teilklon ohne Inhalte, dann gezielt auschecken).
hole_dateien() {
  local ordner=$1 url=$2 commit=$3; shift 3
  if [ "$(git -C "$BAU/$ordner" rev-parse HEAD 2>/dev/null)" != "$commit" ] || ! (cd "$BAU/$ordner" && ls "$@" >/dev/null 2>&1); then
    rm -rf "${BAU:?}/$ordner"
    git init -q "$BAU/$ordner"
    git -C "$BAU/$ordner" fetch -q --depth 1 --filter=blob:none "$url" "$commit"
    git -C "$BAU/$ordner" -c advice.detachedHead=false checkout -q FETCH_HEAD -- "$@"
    git -C "$BAU/$ordner" update-ref HEAD FETCH_HEAD
  fi
}
fertig() { [ -f "$PREFIX/stand-$1" ] && [ "$(cat "$PREFIX/stand-$1")" = "$2" ]; }
mkdir -p "$PREFIX/lib" "$PREFIX/include"

# zlib (nur die Bibliothek): Flate für Bilder, Inhalte, Schrift und Profil.
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

# libjpeg-turbo (ohne SIMD, ohne TurboJPEG-Schnittstelle): Seitenbilder als JPEG schreiben.
if ! fertig jpeg "$JPEG"; then
  hole jpeg https://github.com/libjpeg-turbo/libjpeg-turbo "$JPEG"
  rm -rf "$BAU/jpeg-build"
  cmake -S "$BAU/jpeg" -B "$BAU/jpeg-build" -G Ninja -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN" -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" -DBUILD_SHARED_LIBS=OFF -DCMAKE_C_FLAGS="$WASI_FLAGS" \
    -DENABLE_SHARED=OFF -DENABLE_STATIC=ON -DWITH_SIMD=OFF -DWITH_TURBOJPEG=OFF -DWITH_TOOLS=OFF -DWITH_TESTS=OFF \
    -DCMAKE_SYSTEM_PROCESSOR=wasm32 >/dev/null
  cmake --build "$BAU/jpeg-build" -j "$JOBS" >/dev/null
  cmake --install "$BAU/jpeg-build" >/dev/null
  echo "$JPEG" > "$PREFIX/stand-jpeg"
fi

# stb_image (PNG und – nur für CMYK und Co. – JPEG lesen): eine Kopfdatei.
hole stb https://github.com/nothings/stb "$STB"

# Daten: Schrift der Textebene und sRGB-Profil für den OutputIntent.
hole_dateien tesseract https://github.com/tesseract-ocr/tesseract "$TESSERACT" tessdata/pdf.ttf
hole_dateien icc https://github.com/saucecontrol/Compact-ICC-Profiles "$ICC" profiles/sRGB-v2-magic.icc
hole_dateien noto https://github.com/notofonts/notofonts.github.io "$NOTO" \
  $(echo "$NOTO_SHA256" | awk '{print "fonts/NotoSans/unhinted/ttf/" $3}')
mkdir -p "$CODE/daten"
cp "$BAU/tesseract/tessdata/pdf.ttf" "$CODE/daten/glyphless.ttf"
cp "$BAU/icc/profiles/sRGB-v2-magic.icc" "$CODE/daten/srgb.icc"
echo "$SCHRIFT_SHA256  $CODE/daten/glyphless.ttf
$ICC_SHA256  $CODE/daten/srgb.icc" | sha256sum -c --quiet -
echo "$NOTO_SHA256" | while read -r sha ziel quelle; do
  cp "$BAU/noto/fonts/NotoSans/unhinted/ttf/$quelle" "$CODE/daten/$ziel"
  echo "$sha  $CODE/daten/$ziel" | sha256sum -c --quiet -
done

# Das Modul (DMS-Paket-ABI 1).
"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -c "$CODE/wasi-compat.c" -o "$BAU/wasi-compat.o"
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor $WASI_FLAGS \
  -DPAKET_VERSION="\"$VERSION\"" -I "$PREFIX/include" -I "$BAU/stb" -I "$GEMEINSAM" \
  "$CODE/pdfa.cpp" "$BAU/wasi-compat.o" "$PREFIX/lib/libjpeg.a" "$PREFIX/lib/libz.a" \
  -lwasi-emulated-signal -lwasi-emulated-process-clocks -lwasi-emulated-mman \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

# Test des PDF-Schreibers (code/pdfa.h) – nativ, wenn ein C++-Compiler und zlib da sind.
if command -v c++ >/dev/null 2>&1 && echo '#include <zlib.h>' | c++ -x c++ -fsyntax-only - 2>/dev/null; then
  c++ -std=c++17 -O2 -Wall -Werror -I "$CODE" -I "$GEMEINSAM" "$CODE/../tests/pdfa_test.cpp" -lz -o "$BAU/pdfa_test"
  "$BAU/pdfa_test" "$CODE/daten" >"$BAU/pdfa_test.log" || { cat "$BAU/pdfa_test.log"; exit 1; }
  echo "  PDF-Schreiber: $(grep -c '^ok' "$BAU/pdfa_test.log") Prüfungen bestanden"
fi
