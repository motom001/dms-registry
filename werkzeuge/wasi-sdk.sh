#!/usr/bin/env bash
# Lädt das WASI-SDK (Clang für WebAssembly) in einer festen Version und prüft die Prüfsumme.
#
#   werkzeuge/wasi-sdk.sh [zielordner]     # Standard: ~/.cache/dms-registry
#
# Gibt den Pfad des SDK aus (für WASI_SDK=…). Nur Linux x86_64 (wie die CI).
set -euo pipefail
VERSION=25
DATEI="wasi-sdk-${VERSION}.0-x86_64-linux"
SHA256=52640dde13599bf127a95499e61d6d640256119456d1af8897ab6725bcf3d89c
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
