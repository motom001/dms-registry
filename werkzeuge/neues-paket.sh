#!/usr/bin/env bash
# Legt ein neues Paket aus der Vorlage an.
#   werkzeuge/neues-paket.sh <id> "<Name>"      z. B. werkzeuge/neues-paket.sh haushalt "Haushalt"
set -euo pipefail
ID="${1:?Paket-Id angeben (Kleinbuchstaben, Ziffern, _)}"
NAME="${2:?Namen angeben, z. B. \"Haushalt\"}"
[[ "$ID" =~ ^[a-z][a-z0-9_]{1,39}$ ]] || { echo "Ungültige Id „$ID“: Kleinbuchstaben, Ziffern, _, beginnt mit einem Buchstaben, max. 40 Zeichen (über 20 erst ab Ablago 0.229.0). Ergänzungen mit Punkt (<paket>.<zusatz>) legst du von Hand an (REGELN.md, „Ergänzungen“)."; exit 1; }
cd "$(dirname "$0")/.."
ZIEL="pakete/$ID"
[ -e "$ZIEL" ] && { echo "$ZIEL gibt es schon."; exit 1; }
# Eine Id nur einmal (Registry #173): früher vergeben → ablehnen, sonst in werkzeuge/ids.txt eintragen.
grep -qx "$ID" werkzeuge/ids.txt && { echo "Die Id „$ID“ war schon vergeben (werkzeuge/ids.txt) – bitte eine eigene wählen."; exit 1; }
cp -r vorlage "$ZIEL"
sed -i "s/^id: vorlage$/id: $ID/; s/^name: Vorlage$/name: $NAME/" "$ZIEL/manifest.yaml"
sed -i "1s/.*/# $NAME/" "$ZIEL/README.md"
sed -i "s/<Jahr>/$(date +%Y)/" "$ZIEL/LICENSE"
echo "$ID" >> werkzeuge/ids.txt
echo "Angelegt: $ZIEL (Id in werkzeuge/ids.txt eingetragen)"
echo "Jetzt ausfüllen: manifest.yaml (autor, beschreibung), README.md, LICENSE (<Name>), inhalt/, tests/erwartung.yaml"
echo "Prüfen:  python3 werkzeuge/pruefen.py $ZIEL"
