#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Paket mit dem echten Modell gebaut hat (code/modul.wasm, code/daten/).
set -euo pipefail
PAKET="$(cd "$(dirname "$0")/.." && pwd)"
node "$PAKET/tests/modul_test.mjs" "$PAKET/code/daten"
