#!/usr/bin/env python3
"""
Baut den Katalog der Registry: je Paket ein Archiv <id>-<version>.zip und katalog.json.

    python3 werkzeuge/katalog.py <ausgabe>              # Ausgabeordner = bisheriger Stand (z. B. gh-pages)
    python3 werkzeuge/katalog.py --probe <ausgabe>      # nur prüfen, nichts schreiben

Im Ausgabeordner liegen danach:

    katalog.json                    alle Pakete mit allen Versionen (Format: schema/katalog.schema.json)
    archive/<id>-<version>.zip      genau die Dateien des Paketordners, ohne Unterordner davor

Ältere Versionen bleiben erhalten. Ein Archiv mit gleicher Id und Version ändert sich nie: Ist der Inhalt
eines Pakets anders als im veröffentlichten Archiv, die Version aber gleich, bricht das Skript ab.

Braucht: pip install pyyaml jsonschema
"""
import hashlib, io, json, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

WURZEL = Path(__file__).resolve().parent.parent
REPO = 'https://github.com/motom001/dms-registry'
FORMAT = 1
ZEIT = (1980, 1, 1, 0, 0, 0)


def dateien(ordner: Path) -> dict[str, bytes]:
    """Alle Dateien eines Paketordners, Pfade relativ und mit / getrennt."""
    return {p.relative_to(ordner).as_posix(): p.read_bytes() for p in sorted(ordner.rglob('*')) if p.is_file()}


def archiv(inhalt: dict[str, bytes]) -> bytes:
    """ZIP mit festen Zeitstempeln und Rechten, sortiert – gleicher Inhalt, gleiche Datei."""
    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, 'w') as z:
        for name in sorted(inhalt):
            info = zipfile.ZipInfo(name, date_time=ZEIT)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            z.writestr(info, inhalt[name], compresslevel=9)
    return puffer.getvalue()


def inhalt_von(daten: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(daten)) as z:
        return {n: z.read(n) for n in z.namelist() if not n.endswith('/')}


def lies(ordner: Path, rel: str | None):
    if not rel:
        return []
    p = ordner / rel
    return (yaml.safe_load(p.read_text(encoding='utf-8')) or []) if p.exists() else []


def eintrag(ordner: Path, m: dict, archivname: str, daten: bytes, veroeffentlicht: str) -> dict:
    inhalt = m.get('inhalt') or {}
    typen = lies(ordner, inhalt.get('mappentypen'))
    sichten = lies(ordner, inhalt.get('sichten'))
    beispiele = lies(ordner, inhalt.get('beispiele'))
    pid = m['id']
    return {
        'version': m['version'],
        'dms': m['dms'],
        'abhaengigkeiten': m.get('abhaengigkeiten') or {},
        'inhalt': {
            'mappentypen': [{'schluessel': t['schluessel'], 'name': t['name']} for t in typen],
            'sichten': [{'schluessel': s['schluessel'], 'name': s['name']} for s in sichten],
            'beispiele': len(beispiele),
        },
        'code': 'code' in m,
        'archiv': f'archive/{archivname}',
        'sha256': hashlib.sha256(daten).hexdigest(),
        'groesse': len(daten),
        'veroeffentlicht': veroeffentlicht,
        'quelle': f'{REPO}/tree/main/pakete/{pid}',
        'readme': f'{REPO}/blob/main/pakete/{pid}/README.md',
        'changelog': f'{REPO}/blob/main/pakete/{pid}/CHANGELOG.md',
    }


def versionsschluessel(v: str):
    return tuple(int(x) for x in v.split('.'))


def baue(ausgabe: Path, probe: bool) -> list[str]:
    fehler: list[str] = []
    alt_pfad = ausgabe / 'katalog.json'
    alt = json.loads(alt_pfad.read_text(encoding='utf-8')) if alt_pfad.exists() else {'pakete': []}
    pakete = {p['id']: p for p in alt.get('pakete', [])}
    jetzt = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    neu: list[tuple[str, bytes]] = []

    for ordner in sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir()):
        m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8'))
        pid, version = m['id'], m['version']
        name = f'{pid}-{version}.zip'
        inhalt = dateien(ordner)
        vorhanden = ausgabe / 'archive' / name
        p = pakete.setdefault(pid, {'id': pid, 'versionen': []})
        bekannt = next((v for v in p['versionen'] if v['version'] == version), None)
        if vorhanden.exists():
            daten = vorhanden.read_bytes()
            if inhalt_von(daten) != inhalt:
                fehler.append(f'{pid}: Inhalt geändert, aber Version {version} ist schon veröffentlicht – Version erhöhen')
                continue
        else:
            daten = archiv(inhalt)
            neu.append((name, daten))
        v = eintrag(ordner, m, name, daten, bekannt['veroeffentlicht'] if bekannt else jetzt)
        p['versionen'] = sorted([x for x in p['versionen'] if x['version'] != version] + [v], key=lambda x: versionsschluessel(x['version']), reverse=True)
        # Angaben des Pakets aus der neuesten Version.
        if p['versionen'][0]['version'] == version:
            p.update({'name': m['name'], 'beschreibung': m['beschreibung'], 'autor': m['autor'], 'lizenz': m['lizenz'], 'aktuell': version})

    katalog = {
        'format': FORMAT,
        'erstellt': jetzt,
        'quelle': REPO,
        # Platz für eine Signatur in einer späteren Stufe.
        'signatur': None,
        'pakete': sorted(pakete.values(), key=lambda p: p['id']),
    }
    schema = json.loads((WURZEL / 'schema/katalog.schema.json').read_text(encoding='utf-8'))
    fehler += [f"katalog.json: {'/'.join(map(str, e.absolute_path)) or '(oben)'}: {e.message}" for e in Draft202012Validator(schema).iter_errors(katalog)]
    if fehler or probe:
        return fehler
    (ausgabe / 'archive').mkdir(parents=True, exist_ok=True)
    for name, daten in neu:
        (ausgabe / 'archive' / name).write_bytes(daten)
    alt_pfad.write_text(json.dumps(katalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(katalog["pakete"])} Pakete, {len(neu)} neue Archive: {", ".join(n for n, _ in neu) or "–"}')
    return []


def main():
    args = sys.argv[1:]
    probe = args[:1] == ['--probe']
    if probe:
        args = args[1:]
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    ausgabe = Path(args[0]).resolve()
    ausgabe.mkdir(parents=True, exist_ok=True)
    fehler = baue(ausgabe, probe)
    for f in fehler:
        print(f'✗ {f}')
    if not fehler and probe:
        print('✓ Katalog lässt sich bauen')
    sys.exit(1 if fehler else 0)


if __name__ == '__main__':
    main()
