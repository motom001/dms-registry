#!/usr/bin/env bash
# Baut code/modul.wasm (ein Modul, das nichts tut) und legt die Sprachdaten nach code/daten/.
# Muster für weitere Sprachen: SPRACHE und SHA256 ändern, Ordner und Manifest entsprechend (texterkennung_<sprache>).
# Die CI ruft das über werkzeuge/bauen.py auf: WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}" "${BAU:?BAU fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"

SPRACHE=tur
TESSDATA=87416418657359cb625c412a48b6e1d6d41c29bd   # tessdata_fast, derselbe Stand wie im Paket Texterkennung
SHA256=7393381111e1152420fc4092cb44eef4237580d21b92bf30d7d221aad192c6b7

"$WASI_SDK/bin/clang" --target=wasm32-wasip1 -O2 -Wall -Werror -mexec-model=reactor \
  "$CODE/zusatz.c" -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

# Nur die eine Datei laden (Teilklon ohne Inhalte, dann gezielt auschecken), Prüfsumme fest.
if [ "$(git -C "$BAU/tessdata" rev-parse HEAD 2>/dev/null)" != "$TESSDATA" ] || [ ! -f "$BAU/tessdata/$SPRACHE.traineddata" ]; then
  rm -rf "${BAU:?}/tessdata"
  git init -q "$BAU/tessdata"
  git -C "$BAU/tessdata" fetch -q --depth 1 --filter=blob:none https://github.com/tesseract-ocr/tessdata_fast "$TESSDATA"
  git -C "$BAU/tessdata" -c advice.detachedHead=false checkout -q FETCH_HEAD -- "$SPRACHE.traineddata"
  git -C "$BAU/tessdata" update-ref HEAD FETCH_HEAD
fi
mkdir -p "$CODE/daten"
cp "$BAU/tessdata/$SPRACHE.traineddata" "$CODE/daten/"
echo "$SHA256  $CODE/daten/$SPRACHE.traineddata" | sha256sum -c --quiet -
