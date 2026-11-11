#!/usr/bin/env python3
"""Die Liste „was zählt“ steht zweimal: als Einstellung im Manifest (Texte, Vorauswahl) und in code/bereiche.h (Text →
Kennung des Kerns). Dieser Test hält beide gleich, dazu die Bereiche in code.rechte und in den Mappentypen.

    python3 tests/einstellungen_test.py
"""
import re
import sys
from pathlib import Path

import yaml

PAKET = Path(__file__).resolve().parent.parent
fehler: list[str] = []

code = (PAKET / 'code' / 'bereiche.h').read_text(encoding='utf-8')
# {"sicherung", "Sicherung", { {"Zeitplan", "sicherung.zeitplan", true}, … }}
bereiche: dict[str, dict] = {}
for m in re.finditer(r'\{"([a-z]+)", "([^"]+)", \{(.*?)\}\}(?:,|\n)', code, re.S):
    zeilen = re.findall(r'\{"([^"]+)", ("[^"]+"|AUSWAHL), (true|false)\}', m.group(3))
    bereiche[m.group(1)] = {'name': m.group(2), 'zeilen': [(t, k.strip('"'), v == 'true') for t, k, v in zeilen]}

manifest = yaml.safe_load((PAKET / 'manifest.yaml').read_text(encoding='utf-8'))
felder = {f['schluessel']: f for a in manifest['code']['einstellungen'] for f in a['felder']}
abschnitte = [a['abschnitt'] for a in manifest['code']['einstellungen']]

if list(bereiche) != manifest['code']['rechte']['einrichtung']:
    fehler.append(f'Bereiche in code/bereiche.h {list(bereiche)} ≠ code.rechte.einrichtung {manifest["code"]["rechte"]["einrichtung"]}')
if [b['name'] for b in bereiche.values()] != abschnitte:
    fehler.append(f'Namen der Bereiche ≠ Abschnitte der Einstellungen: {[b["name"] for b in bereiche.values()]} / {abschnitte}')
for s, b in bereiche.items():
    f = felder.get(f'zaehlt_{s}')
    if not f:
        fehler.append(f'Einstellung zaehlt_{s} fehlt im Manifest')
        continue
    texte = [t for t, _, _ in b['zeilen']]
    vor = [t for t, _, v in b['zeilen'] if v]
    if f.get('optionen') != texte:
        fehler.append(f'zaehlt_{s}: optionen im Manifest ≠ code/bereiche.h\n  {f.get("optionen")}\n  {texte}')
    if f.get('standard') != vor:
        fehler.append(f'zaehlt_{s}: standard im Manifest ≠ Vorauswahl in code/bereiche.h\n  {f.get("standard")}\n  {vor}')
    for _, k, _ in b['zeilen']:
        if k != 'AUSWAHL' and not k.startswith(s + '.'):
            fehler.append(f'{s}: Kennung „{k}“ gehört nicht zu diesem Bereich')

typen = yaml.safe_load((PAKET / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
namen = [b['name'] for b in bereiche.values()]
for t in typen:
    for f in t['felder']:
        if f['key'] == 'bereich' and f.get('optionen') != namen:
            fehler.append(f'{t["schluessel"]}.bereich: optionen ≠ Namen der Bereiche in code/bereiche.h')

if len(bereiche) != 9:
    fehler.append(f'code/bereiche.h: {len(bereiche)} Bereiche gelesen, erwartet 9 – Muster im Test anpassen?')
for x in fehler:
    print('✗', x)
print('Einstellungen und Code passen zusammen' if not fehler else f'{len(fehler)} Fehler')
sys.exit(1 if fehler else 0)
