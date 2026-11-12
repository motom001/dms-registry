#!/usr/bin/env bash
# Alle Tests des Pakets: Modul bauen, künstliche Scans erzeugen (tests/scans.py) und das Modul mit einer Nachbildung
# von Ablago laufen lassen – je Empfindlichkeit, Kanal und Stand der Post.
#
#   pakete/leerseiten/tests/pruefen.sh
#
# Braucht: python3, node, pdftoppm und pdfinfo (Poppler); WASI_SDK (sonst lädt werkzeuge/wasi-sdk.sh es).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
WURZEL="$(cd "$PAKET/../.." && pwd)"
export WASI_SDK="${WASI_SDK:-$("$WURZEL/werkzeuge/wasi-sdk.sh")}"
python3 "$WURZEL/werkzeuge/bauen.py" "$PAKET"
"$PAKET/tests/ci.sh"
