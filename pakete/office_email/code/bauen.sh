#!/usr/bin/env bash
# Baut code/modul.wasm: Text aus Office-Dateien und E-Mails herauslösen. Einzige fremde Bibliothek ist zlib (Entpacken
# der ZIP-Archive von .docx/.xlsx/.pptx/.odt …), aus der Quelle auf festem Commit, Hash geprüft.
#
# Die CI ruft das über werkzeuge/bauen.py auf: WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner
# außerhalb des Pakets (Quellen und Zwischenstände; bleibt zwischen Läufen erhalten).
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
# Den Mail-Zerleger (mail.h, cfb.h, zeichen.h) teilt das Paket mit PDF/A: gemeinsam/mail/ im Repository (#143).
GEMEINSAM="$(cd "$CODE/../../../gemeinsam/mail" && pwd)"

ZLIB=51b7f2abdade71cd9bb0e7a373ef2610ec6f9daf       # 1.3.1
PREFIX="$BAU/prefix"

# Ein Repository auf genau einem Commit (flach, nur dieser Stand); prüft den Commit-Hash.
hole() {
  local ordner=$1 url=$2 commit=$3
  if [ "$(git -C "$BAU/$ordner" rev-parse HEAD 2>/dev/null)" != "$commit" ]; then
    rm -rf "${BAU:?}/$ordner"
    git init -q "$BAU/$ordner"
    git -C "$BAU/$ordner" fetch -q --depth 1 "$url" "$commit"
    git -C "$BAU/$ordner" -c advice.detachedHead=false checkout -q FETCH_HEAD
    local ist
    ist=$(git -C "$BAU/$ordner" rev-parse HEAD)
    if [ "$ist" != "$commit" ]; then
      echo "$ordner: $url ist $ist, erwartet $commit" >&2
      exit 1
    fi
  fi
}
mkdir -p "$PREFIX/lib" "$PREFIX/include"

# zlib: nur Entpacken (inflate), ohne gz*-Dateifunktionen.
if [ ! -f "$PREFIX/stand-zlib" ] || [ "$(cat "$PREFIX/stand-zlib")" != "$ZLIB" ]; then
  hole zlib https://github.com/madler/zlib "$ZLIB"
  rm -rf "$BAU/zlib-o" && mkdir -p "$BAU/zlib-o"
  for f in adler32 crc32 inffast inflate inftrees zutil; do
    "$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -c "$BAU/zlib/$f.c" -o "$BAU/zlib-o/$f.o"
  done
  rm -f "$PREFIX/lib/libz.a"
  "$WASI_SDK/bin/llvm-ar" rcs "$PREFIX/lib/libz.a" "$BAU"/zlib-o/*.o
  cp "$BAU/zlib/zlib.h" "$BAU/zlib/zconf.h" "$PREFIX/include/"
  echo "$ZLIB" > "$PREFIX/stand-zlib"
fi

# Das Modul (DMS-Paket-ABI 1).
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Wextra -Werror -fno-exceptions -mexec-model=reactor \
  -I "$PREFIX/include" -I "$GEMEINSAM" "$CODE/office_email.cpp" "$PREFIX/lib/libz.a" \
  -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
