#!/usr/bin/env python3
"""
Sammeldatei: mehrere Pakete aus dem Katalog in einer Datei – für ein DMS ohne Internet (motom001/dms#461).

    python3 werkzeuge/sammeldatei.py <katalogordner> <ziel.zip> [--dms 0.107.1] <id> [<id> …]
    python3 werkzeuge/sammeldatei.py --pruefen <datei.zip> [--katalog <katalog.json>]

Die Katalog-Webseite (sammeldatei.html) stellt dieselbe Datei im Browser zusammen; dieses Skript ist die
Referenz dafür und prüft eine Sammeldatei genau so, wie das DMS sie prüft.

Aufbau (Schema: schema/sammeldatei.schema.json):

    sammeldatei.json              Verzeichnis: je Paket Id, Version, Archiv, SHA-256, Größe, gewählt/Abhängigkeit
    LIESMICH.txt                  kurze Anleitung (optional)
    pakete/<id>-<version>.zip     das Archiv aus dem Katalog, Byte für Byte unverändert

Auswahl: je Paket die neueste Version, deren „dms“ zur angegebenen DMS-Version passt (ohne --dms: die neueste);
Abhängigkeiten kommen mit (neueste Version, die zum Bereich und zur DMS-Version passt). Jedes Archiv wird vor dem
Einpacken gegen die Prüfsumme in katalog.json geprüft.

Braucht: pip install jsonschema
"""
import hashlib, io, json, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

WURZEL = Path(__file__).resolve().parent.parent
VERZEICHNIS, LIESMICH = 'sammeldatei.json', 'LIESMICH.txt'
REPO = 'https://github.com/motom001/dms-registry'
KATALOG_URL = 'https://raw.githubusercontent.com/motom001/dms-registry/gh-pages/katalog.json'
# Grenzen wie im DMS (server/src/pakete.ts).
PAKETE_MAX, ARCHIV_MAX, DATEI_MAX = 50, 10 * 1024 * 1024, 64 * 1024 * 1024
BEREICH = re.compile(r'^(>=|>|=|\^|~)?(\d+\.\d+\.\d+)( <(\d+\.\d+\.\d+))?$')
ARCHIVNAME = re.compile(r'^pakete/([a-z][a-z0-9_]{1,19})-(\d+\.\d+\.\d+)\.zip$')

LIESMICH_TEXT = '''Sammeldatei für das DMS
=======================

Diese Datei enthält mehrere Pakete aus dem Paketkatalog des DMS-Projekts
(https://motom001.github.io/dms-registry/) – für ein DMS ohne Internet.

So installierst du sie:
  Werkbank → Pakete → „Ohne Internet …“ → Sammeldatei wählen
  (oder im Einrichtungsassistenten, Schritt „Pakete dazuholen“).

Das DMS prüft vorher jedes Paket gegen die Prüfsumme in sammeldatei.json und
installiert dann Paket für Paket; Rechte von Paketen mit Code bestätigst du einzeln.
Entpacken musst du nichts.
'''


def teile(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split('.'))


def passt(version: str, bereich: str) -> bool:
    """Wie passt() im DMS (shared/src/pakete.ts)."""
    m = BEREICH.match(bereich.strip())
    if not m:
        return False
    op, basis, ober = m.group(1) or '=', m.group(2), m.group(4)
    v, b = teile(version), teile(basis)
    if op == '>=':
        ok = v >= b
    elif op == '>':
        ok = v > b
    elif op == '^':
        ok = v >= b and (v < (b[0] + 1, 0, 0) if b[0] > 0 else v < (0, b[1] + 1, 0))
    elif op == '~':
        ok = v >= b and v < (b[0], b[1] + 1, 0)
    else:
        ok = v == b
    return ok and (not ober or v < teile(ober))


def dms_passt(dms: str | None, bereich: str) -> bool:
    return not dms or passt(dms, bereich)


def auswahl(katalog: dict, ids: list[str], dms: str | None) -> list[dict]:
    """Gewählte Pakete samt Abhängigkeiten, Abhängigkeiten zuerst. Wirft ValueError, wenn etwas nicht passt."""
    pakete = {p['id']: p for p in katalog['pakete']}
    plan: dict[str, dict] = {}

    def nimm(pid: str, bereich: str | None, von: str | None):
        if pid in plan:
            if not von:
                plan[pid]['gewaehlt'] = True
            elif bereich and not passt(plan[pid]['version'], bereich):
                raise ValueError(f'{von} braucht {pid} {bereich}, gewählt ist {plan[pid]["version"]}')
            return
        if pid not in pakete:
            raise ValueError(f'{pid} gibt es im Katalog nicht' + (f' (gebraucht von {von})' if von else ''))
        kandidaten = sorted(pakete[pid]['versionen'], key=lambda v: teile(v['version']), reverse=True)
        v = next((v for v in kandidaten if (not bereich or passt(v['version'], bereich)) and dms_passt(dms, v['dms'])), None)
        if not v:
            bedingungen = [f'zu {bereich}' if bereich else '', f'zu DMS {dms}' if dms else '']
            raise ValueError(f'{pid}: keine Version passt ' + ' und '.join(b for b in bedingungen if b))
        plan[pid] = {'id': pid, 'name': pakete[pid].get('name', pid), 'gewaehlt': not von, 'v': v, 'version': v['version']}
        for a, b in (v.get('abhaengigkeiten') or {}).items():
            nimm(a, b, pid)

    for pid in ids:
        nimm(pid, None, None)
    erg, fertig, unterwegs = [], set(), set()

    def besuche(pid: str):
        if pid in fertig:
            return
        if pid in unterwegs:
            raise ValueError('Die Abhängigkeiten bilden einen Kreis')
        unterwegs.add(pid)
        for a in plan[pid]['v'].get('abhaengigkeiten') or {}:
            if a in plan:
                besuche(a)
        unterwegs.discard(pid)
        fertig.add(pid)
        erg.append(plan[pid])

    for pid in plan:
        besuche(pid)
    return erg


def erzeuge(katalogordner: Path, ids: list[str], dms: str | None, jetzt: str | None = None) -> bytes:
    """Sammeldatei aus einem gebauten Katalog (katalog.json und archive/)."""
    katalog = json.loads((katalogordner / 'katalog.json').read_text(encoding='utf-8'))
    liste = auswahl(katalog, ids, dms)
    if len(liste) > PAKETE_MAX:
        raise ValueError(f'Höchstens {PAKETE_MAX} Pakete je Sammeldatei')
    eintraege, archive = [], {}
    for p in liste:
        v = p['v']
        daten = (katalogordner / v['archiv']).read_bytes()
        if hashlib.sha256(daten).hexdigest() != v['sha256'] or len(daten) != v['groesse']:
            raise ValueError(f'{v["archiv"]}: Prüfsumme bzw. Größe passt nicht zu katalog.json')
        name = f'pakete/{p["id"]}-{p["version"]}.zip'
        archive[name] = daten
        eintraege.append({'id': p['id'], 'version': p['version'], 'name': p['name'], 'archiv': name, 'sha256': v['sha256'], 'groesse': v['groesse'], 'gewaehlt': p['gewaehlt']})
    verzeichnis = {
        'format': 1, 'art': 'dms-sammeldatei',
        'erstellt': jetzt or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        'quelle': katalog.get('quelle') or REPO, 'katalog': KATALOG_URL, 'dms': dms, 'pakete': eintraege,
    }
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, 'w') as z:
        z.writestr(zipfile.ZipInfo(VERZEICHNIS, (1980, 1, 1, 0, 0, 0)), json.dumps(verzeichnis, ensure_ascii=False, indent=2) + '\n', compress_type=zipfile.ZIP_DEFLATED)
        z.writestr(zipfile.ZipInfo(LIESMICH, (1980, 1, 1, 0, 0, 0)), LIESMICH_TEXT, compress_type=zipfile.ZIP_DEFLATED)
        # Archive sind schon komprimiert: gespeichert, Byte für Byte wie im Katalog.
        for name, daten in archive.items():
            z.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), daten, compress_type=zipfile.ZIP_STORED)
    return puffer.getvalue()


def pruefe(daten: bytes, katalog: dict | None = None) -> list[str]:
    """Prüft eine Sammeldatei wie das DMS: Verzeichnis, nur erwartete Dateien, Größe und SHA-256 je Archiv, optional gegen katalog.json."""
    if len(daten) > DATEI_MAX:
        return [f'Die Datei ist größer als {DATEI_MAX // 1048576} MB']
    try:
        z = zipfile.ZipFile(io.BytesIO(daten))
    except zipfile.BadZipFile:
        return ['Kein gültiges ZIP']
    infos = [i for i in z.infolist() if not i.is_dir()]
    if len(infos) > PAKETE_MAX + 2:
        return [f'Mehr als {PAKETE_MAX + 2} Dateien']
    namen = [i.filename for i in infos]
    if len(set(namen)) != len(namen):
        return ['Eine Datei steht zweimal im Archiv']
    if VERZEICHNIS not in namen:
        return [f'{VERZEICHNIS} fehlt']
    for i in infos:
        grenze = 1024 * 1024 if not i.filename.startswith('pakete/') else ARCHIV_MAX
        if i.file_size > grenze:
            return [f'{i.filename}: zu groß']
        if i.flag_bits & 1:
            return [f'{i.filename}: verschlüsselt']
    try:
        vz = json.loads(z.read(VERZEICHNIS).decode('utf-8'))
    except ValueError:
        return [f'{VERZEICHNIS} ist kein gültiges JSON']
    schema = json.loads((WURZEL / 'schema/sammeldatei.schema.json').read_text(encoding='utf-8'))
    fehler = [f"{VERZEICHNIS}: {'/'.join(map(str, e.absolute_path)) or '(oben)'}: {e.message}" for e in Draft202012Validator(schema).iter_errors(vz)]
    if fehler:
        return fehler
    ids = [p['id'] for p in vz['pakete']]
    if len(set(ids)) != len(ids):
        fehler.append('Ein Paket steht zweimal im Verzeichnis')
    erwartet = {VERZEICHNIS, LIESMICH} | {p['archiv'] for p in vz['pakete']}
    fehler += [f'{n}: steht nicht im Verzeichnis' for n in namen if n not in erwartet]
    versionen = {(p['id'], v['version']): v for p in (katalog or {}).get('pakete', []) for v in p['versionen']}
    for p in vz['pakete']:
        m = ARCHIVNAME.match(p['archiv'])
        if not m or (m.group(1), m.group(2)) != (p['id'], p['version']):
            fehler.append(f'{p["archiv"]}: Name passt nicht zu {p["id"]} {p["version"]}')
            continue
        if p['archiv'] not in namen:
            fehler.append(f'{p["archiv"]} fehlt')
            continue
        a = z.read(p['archiv'])
        if len(a) != p['groesse'] or hashlib.sha256(a).hexdigest() != p['sha256']:
            fehler.append(f'{p["id"]} {p["version"]}: Größe bzw. Prüfsumme passt nicht zum Verzeichnis')
        kv = versionen.get((p['id'], p['version']))
        if katalog is not None and kv and kv['sha256'] != p['sha256']:
            fehler.append(f'{p["id"]} {p["version"]}: Prüfsumme passt nicht zum Katalog')
        if katalog is not None and not kv:
            fehler.append(f'{p["id"]} {p["version"]}: nicht im Katalog')
    return fehler


def main():
    args = sys.argv[1:]
    if args[:1] == ['--pruefen'] and len(args) in (2, 4):
        katalog = json.loads(Path(args[3]).read_text(encoding='utf-8')) if len(args) == 4 and args[2] == '--katalog' else None
        fehler = pruefe(Path(args[1]).read_bytes(), katalog)
        for f in fehler:
            print(f'✗ {f}')
        if not fehler:
            vz = json.loads(zipfile.ZipFile(args[1]).read(VERZEICHNIS))
            print('✓ Sammeldatei in Ordnung: ' + ', '.join(f'{p["id"]} {p["version"]}' for p in vz['pakete']) + (' (gegen katalog.json geprüft)' if katalog else ''))
        sys.exit(1 if fehler else 0)
    dms = None
    if '--dms' in args:
        i = args.index('--dms')
        dms, args = args[i + 1], args[:i] + args[i + 2:]
    if len(args) < 3:
        print(__doc__)
        sys.exit(2)
    try:
        daten = erzeuge(Path(args[0]), args[2:], dms)
    except ValueError as e:
        print(f'✗ {e}')
        sys.exit(1)
    Path(args[1]).write_bytes(daten)
    print(f'{args[1]}: {len(daten)} Bytes, SHA-256 {hashlib.sha256(daten).hexdigest()}')


if __name__ == '__main__':
    main()
