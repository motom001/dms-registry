#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat: Aktionen dms:codes und dms:erkennen mit einer
# Nachbildung des DMS und Seitenbildern aus den Matrizen in tests/codes/ (QR, Aztec, Data Matrix, PDF417, EAN-13,
# Code 128, ITF; vCard 2.1/3.0/4.0, gedreht, verrauscht, präpariert; Link, GiroCode).
set -euo pipefail
node "$(cd "$(dirname "$0")" && pwd)/modul_test.mjs"
