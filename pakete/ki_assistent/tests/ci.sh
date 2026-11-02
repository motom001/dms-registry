#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat: Ablauf mit einer Nachbildung des DMS und
# eines OpenAI-kompatiblen Dienstes (Antwort Stück für Stück, Fehler, Verbindung testen).
set -euo pipefail
node "$(cd "$(dirname "$0")" && pwd)/modul_test.mjs"
