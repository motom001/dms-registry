#!/usr/bin/env bash
# Baut code/modul.wasm: QR-Codes lesen (quirc) und vCards in Vorschläge für „Aus Dokument ausfüllen“ übersetzen.
#
# Die CI ruft das über werkzeuge/bauen.py auf: WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner
# außerhalb des Pakets (Quellen von quirc; bleibt zwischen Läufen erhalten).
# quirc (ISC-Lizenz, Daniel Beer) kommt vom Original auf GitHub, fest auf den Commit des Tags v1.2; nach dem Holen
# prüft das Skript den Commit-Hash. Lizenztext: code/lizenzen/quirc.txt.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
QUIRC=542848dd6b9b0eaa9587bbf25b9bc67bd8a71fca   # quirc v1.2
QUELLE=https://github.com/dlbeer/quirc

if [ "$(git -C "$BAU/quirc" rev-parse HEAD 2>/dev/null)" != "$QUIRC" ]; then
  rm -rf "${BAU:?}/quirc"
  git init -q "$BAU/quirc"
  git -C "$BAU/quirc" fetch -q --depth 1 "$QUELLE" "$QUIRC"
  git -C "$BAU/quirc" -c advice.detachedHead=false checkout -q FETCH_HEAD
  ist=$(git -C "$BAU/quirc" rev-parse HEAD)
  [ "$ist" = "$QUIRC" ] || { echo "quirc: $ist, erwartet $QUIRC" >&2; exit 1; }
fi

Q="$BAU/quirc/lib"
# Mehr Regionen als die Vorgabe (254): Fotos mit Text und große QR-Codes (lange vCards) haben weit mehr
# zusammenhängende Flächen; sonst findet quirc die Ecken gar nicht. Kostet 2 statt 1 Byte je Bildpunkt.
DEF=-DQUIRC_MAX_REGIONS=65534
for f in decode identify quirc version_db; do
  "$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 $DEF -c "$Q/$f.c" -o "$BAU/quirc-$f.o"
done
"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor $DEF -I "$Q" \
  "$CODE/qrcode.cpp" "$BAU"/quirc-*.o -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"
