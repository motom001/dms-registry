#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat (die Berechnung selbst prüft code/bauen.sh nativ).
set -euo pipefail
node "$(cd "$(dirname "$0")" && pwd)/modul_test.mjs"
