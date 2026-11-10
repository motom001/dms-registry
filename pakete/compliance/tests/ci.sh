#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat (Vergleich und Prüfwert prüft code/bauen.sh nativ).
set -euo pipefail
hier="$(cd "$(dirname "$0")" && pwd)"
python3 "$hier/einstellungen_test.py"
node "$hier/modul_test.mjs"
