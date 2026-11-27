#!/usr/bin/env bash
# Lädt das WASI-SDK (Clang für WebAssembly) in einer festen Version und prüft die Prüfsumme.
#
#   werkzeuge/wasi-sdk.sh [zielordner]     # Standard: ~/.cache/dms-registry
#   WASI_SDK_VERSION=33 werkzeuge/wasi-sdk.sh   # andere Version (nur die unten genannten)
#
# Gibt den Pfad des SDK aus (für WASI_SDK=…). Nur Linux x86_64 (wie die CI).
# Alle Pakete bauen mit Version 25. Barcodes (#294) braucht 33: zxing-cpp wirft intern Ausnahmen, und erst ab 33 kann
# das SDK C++-Ausnahmen (Wasm-Ausnahmen, libunwind) – sein code/bauen.sh holt sich die Version selbst.
set -euo pipefail
VERSION="${WASI_SDK_VERSION:-25}"
case "$VERSION" in
  25) SHA256=52640dde13599bf127a95499e61d6d640256119456d1af8897ab6725bcf3d89c ;;
  33) SHA256=0ba8b5bfaeb2adf3f29bab5841d76cf5318ab8e1642ea195f88baba1abd47bce ;;
  *) echo "WASI-SDK $VERSION ist nicht freigegeben (bekannt: 25, 33)" >&2; exit 1 ;;
esac
DATEI="wasi-sdk-${VERSION}.0-x86_64-linux"
ZIEL="${1:-${XDG_CACHE_HOME:-$HOME/.cache}/dms-registry}"
mkdir -p "$ZIEL"
if [ ! -x "$ZIEL/$DATEI/bin/clang" ]; then
  tmp=$(mktemp)
  curl -fsSL --retry 3 -o "$tmp" "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-${VERSION}/${DATEI}.tar.gz"
  echo "$SHA256  $tmp" | sha256sum -c --quiet - >&2
  tar -xzf "$tmp" -C "$ZIEL"
  rm -f "$tmp"
fi
echo "$ZIEL/$DATEI"
