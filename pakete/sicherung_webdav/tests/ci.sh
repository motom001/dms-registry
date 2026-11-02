#!/usr/bin/env bash
# Tests in der CI, nachdem werkzeuge/bauen.py das Modul gebaut hat: Ablauf mit einer Nachbildung des DMS und eines
# WebDAV-Servers (Nextcloud-Chunking, Content-Range, Dateiablage, Abbruch und Wiederholung, falsche Prüfsumme).
set -euo pipefail
node "$(cd "$(dirname "$0")" && pwd)/modul_test.mjs"
