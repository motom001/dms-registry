#!/usr/bin/env bash
# Baut code/modul.wasm und legt das Modell nach code/daten/ (die CI ruft das über werkzeuge/bauen.py auf).
#
# WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner außerhalb des Pakets (bleibt zwischen Läufen).
# Das Modell kommt von Hugging Face, festgelegt auf einen Commit (in jeder Adresse). Für große Dateien liefert
# /raw/ den Git-LFS-Zeiger mit der SHA-256 der Datei; die Datei selbst (über /resolve/) muss dazu passen.
# Sind MODELL_SHA256 bzw. TOKENIZER_SHA256 gesetzt, prüft der Bau zusätzlich gegen diese festen Werte; bauen.sh
# gibt beide Prüfsummen aus. Ohne Netz: KI_MODELL_ORDNER zeigt auf einen Ordner mit model.safetensors und
# tokenizer.json (z. B. für Tests).
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
BAU="${BAU:-$(mktemp -d)}"

REPO=https://huggingface.co/sentence-transformers/static-similarity-mrl-multilingual-v1
COMMIT=65015369ff9ec8966e9144a321d8e7d5e34215dc
MODELL_SHA256=""     # nach dem ersten Bau aus der Ausgabe eintragen
TOKENIZER_SHA256=""
DIM="${KI_DIM:-256}"  # Tests mit dem kleinen Modell: KI_DIM=32

"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O2 -Wall -Werror -fno-exceptions -mexec-model=reactor \
  "$CODE/aehnlich.cpp" -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

# Modell holen (einmal je Commit) und umwandeln.
quelle="${KI_MODELL_ORDNER:-}"
stand="$COMMIT/$DIM/$(sha256sum "$CODE/umwandeln.py" | cut -c1-16)"
if [ -z "$quelle" ]; then
  quelle="$BAU/modell"
  if [ "$(cat "$BAU/daten/stand" 2>/dev/null)" != "$stand" ]; then
    rm -rf "${BAU:?}/modell"
    mkdir -p "$quelle"
    for datei in 0_StaticEmbedding/model.safetensors 0_StaticEmbedding/tokenizer.json; do
      ziel="$quelle/$(basename "$datei")"
      curl -fsSL --retry 3 -o "$ziel" "$REPO/raw/$COMMIT/$datei"
      # Git-LFS-Zeiger: große Datei holen und gegen die Prüfsumme im Zeiger prüfen.
      if head -c 40 "$ziel" | grep -q '^version https://git-lfs'; then
        sha=$(sed -n 's/^oid sha256:\([0-9a-f]\{64\}\)$/\1/p' "$ziel")
        curl -fsSL --retry 3 -o "$ziel" "$REPO/resolve/$COMMIT/$datei"
        echo "$sha  $ziel" | sha256sum -c --quiet -
      fi
      ist=$(sha256sum "$ziel" | cut -c1-64)
      soll=$([ "$(basename "$datei")" = model.safetensors ] && echo "$MODELL_SHA256" || echo "$TOKENIZER_SHA256")
      if [ -n "$soll" ] && [ "$soll" != "$ist" ]; then echo "$datei: Prüfsumme $ist statt $soll" >&2; exit 1; fi
      echo "  $datei: sha256 $ist"
    done
    rm -rf "${BAU:?}/daten"
    python3 -B "$CODE/umwandeln.py" "$quelle" "$BAU/daten" "$DIM"
    echo "$stand" > "$BAU/daten/stand"
    rm -rf "${BAU:?}/modell"  # 433 MB – umgewandelt bleibt nur das Nötige (≈ 28 MB) im Cache
  fi
else
  rm -rf "${BAU:?}/daten"
  python3 -B "$CODE/umwandeln.py" "$quelle" "$BAU/daten" "$DIM"
fi
mkdir -p "$CODE/daten"
cp "$BAU/daten/modell.dat" "$BAU/daten/vokabular.txt" "$BAU/daten/zeichen.dat" "$CODE/daten/"
