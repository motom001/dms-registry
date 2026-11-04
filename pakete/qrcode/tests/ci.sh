#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat: Aktion dms:erkennen mit einer Nachbildung des DMS
# und Seitenbildern aus den QR-Matrizen in tests/qr/ (vCard 2.1/3.0/4.0, gedreht, verrauscht, präpariert; Link, GiroCode).
set -euo pipefail
node "$(cd "$(dirname "$0")" && pwd)/modul_test.mjs"
