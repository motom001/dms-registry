#!/usr/bin/env bash
# Baut code/modul.wasm (mit SIMD) und legt das Modell nach code/daten/ (die CI ruft das über werkzeuge/bauen.py auf).
#
# WASI_SDK zeigt auf das WASI-SDK, BAU auf einen Arbeitsordner außerhalb des Pakets (bleibt zwischen Läufen).
# Das Modell kommt von Hugging Face, festgelegt auf einen Commit; große Dateien gegen die SHA-256 aus ihrem
# Git-LFS-Zeiger geprüft. umwandeln.py braucht numpy, safetensors und tokenizers – in einer eigenen Umgebung unter
# $BAU, installiert aus code/requirements.txt mit Prüfsummen. Ohne Netz: KI_MODELL_ORDNER zeigt auf einen Ordner mit
# model.safetensors und tokenizer.json, KI_PYTHON auf ein Python mit diesen Paketen.
set -euo pipefail
: "${WASI_SDK:?WASI_SDK fehlt}"
CODE="$(cd "$(dirname "$0")" && pwd)"
BAU="${BAU:-$(mktemp -d)}"
REPO=https://huggingface.co/intfloat/multilingual-e5-small
COMMIT=614241f622f53c4eeff9890bdc4f31cfecc418b3

"$WASI_SDK/bin/clang++" --target=wasm32-wasip1 -O3 -msimd128 -Wall -Werror -fno-exceptions -mexec-model=reactor \
  "$CODE/e5.cpp" -Wl,--import-memory -Wl,--strip-all -o "$CODE/modul.wasm"

python="${KI_PYTHON:-}"
if [ -z "$python" ]; then
  if [ ! -x "$BAU/venv/bin/python" ] || ! cmp -s "$CODE/requirements.txt" "$BAU/venv/requirements.txt"; then
    rm -rf "${BAU:?}/venv"
    python3 -m venv "$BAU/venv"
    "$BAU/venv/bin/pip" install --quiet --require-hashes --only-binary :all: -r "$CODE/requirements.txt"
    cp "$CODE/requirements.txt" "$BAU/venv/requirements.txt"
  fi
  python="$BAU/venv/bin/python"
fi

quelle="${KI_MODELL_ORDNER:-}"
stand="$COMMIT/$(cat "$CODE/umwandeln.py" "$CODE/requirements.txt" | sha256sum | cut -c1-16)"
if [ -z "$quelle" ]; then
  quelle="$BAU/modell"
  if [ "$(cat "$BAU/daten/stand" 2>/dev/null)" != "$stand" ]; then
    rm -rf "${BAU:?}/modell"
    mkdir -p "$quelle"
    for datei in model.safetensors tokenizer.json; do
      ziel="$quelle/$datei"
      curl -fsSL --retry 3 -o "$ziel" "$REPO/raw/$COMMIT/$datei"
      if head -c 40 "$ziel" | grep -q '^version https://git-lfs'; then
        sha=$(sed -n 's/^oid sha256:\([0-9a-f]\{64\}\)$/\1/p' "$ziel")
        curl -fsSL --retry 3 -o "$ziel" "$REPO/resolve/$COMMIT/$datei"
        echo "$sha  $ziel" | sha256sum -c --quiet -
      fi
      echo "  $datei: sha256 $(sha256sum "$ziel" | cut -c1-64)"
    done
    rm -rf "${BAU:?}/daten"
    "$python" -B "$CODE/umwandeln.py" "$quelle" "$BAU/daten"
    echo "$stand" > "$BAU/daten/stand"
    rm -rf "${BAU:?}/modell"  # 470 MB – umgewandelt bleibt nur das Nötige (≈ 84 MB) im Cache
  fi
else
  rm -rf "${BAU:?}/daten"
  "$python" -B "$CODE/umwandeln.py" "$quelle" "$BAU/daten"
fi
mkdir -p "$CODE/daten"
cp "$BAU/daten/modell.dat" "$BAU/daten/vokabular.dat" "$BAU/daten/normal.dat" "$CODE/daten/"
