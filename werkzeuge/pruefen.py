#!/usr/bin/env python3
"""
Prüft Pakete nach den Regeln der Registry (REGELN.md).

    python3 werkzeuge/pruefen.py                    # alle Pakete unter pakete/ und die Vorlage
    python3 werkzeuge/pruefen.py pakete/haushalt    # ein Paket
    python3 werkzeuge/pruefen.py --basis origin/main pakete/haushalt   # zusätzlich: Version erhöht?

Braucht: pip install pyyaml jsonschema
"""
import json, re, subprocess, sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

WURZEL = Path(__file__).resolve().parent.parent
SCHEMA_MANIFEST = json.loads((WURZEL / 'schema/manifest.schema.json').read_text())
SCHEMA_INHALT = json.loads((WURZEL / 'schema/inhalt.schema.json').read_text())
PFLICHT = ['manifest.yaml', 'README.md', 'LICENSE', 'CHANGELOG.md', 'tests']
VERBOTEN = re.compile(r'\.(wasm|so|dll|dylib|exe|jar|class|bin|o|a|pyc|node)$', re.I)
MAX_GROESSE = 2 * 1024 * 1024  # je Datei; Bilder fürs README gern kleiner


def inhalt_validator(art: str) -> Draft202012Validator:
    schema = {'$schema': SCHEMA_INHALT['$schema'], '$defs': SCHEMA_INHALT['$defs'], **SCHEMA_INHALT[art]}
    return Draft202012Validator(schema)


def lies_yaml(pfad: Path, fehler: list[str]):
    try:
        return yaml.safe_load(pfad.read_text(encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        fehler.append(f'{pfad.name}: kein gültiges YAML ({e})')
        return None


def schema_fehler(validator: Draft202012Validator, daten, datei: str) -> list[str]:
    return [f"{datei}: {'/'.join(map(str, e.absolute_path)) or '(oben)'}: {e.message}" for e in validator.iter_errors(daten)]


def version_von(git_ref: str, manifest: Path) -> str | None:
    rel = manifest.relative_to(WURZEL).as_posix()
    try:
        alt = subprocess.run(['git', 'show', f'{git_ref}:{rel}'], cwd=WURZEL, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None  # neues Paket
    return (yaml.safe_load(alt) or {}).get('version')


def geaendert(git_ref: str, ordner: Path) -> bool:
    rel = ordner.relative_to(WURZEL).as_posix()
    r = subprocess.run(['git', 'diff', '--quiet', git_ref, '--', rel], cwd=WURZEL)
    return r.returncode != 0


def pruefe(ordner: Path, basis: str | None) -> list[str]:
    fehler: list[str] = []
    vorlage = ordner.name == 'vorlage'

    for name in PFLICHT:
        if not (ordner / name).exists():
            fehler.append(f'{name} fehlt')
    for datei in ordner.rglob('*'):
        if datei.is_file():
            if VERBOTEN.search(datei.name):
                fehler.append(f'{datei.relative_to(ordner)}: fertige Programmdateien sind nicht erlaubt (REGELN.md)')
            if datei.stat().st_size > MAX_GROESSE:
                fehler.append(f'{datei.relative_to(ordner)}: größer als 2 MB')

    m_pfad = ordner / 'manifest.yaml'
    if not m_pfad.exists():
        return fehler
    m = lies_yaml(m_pfad, fehler)
    if not isinstance(m, dict):
        return fehler + ['manifest.yaml: leer oder kein Objekt']
    fehler += schema_fehler(Draft202012Validator(SCHEMA_MANIFEST), m, 'manifest.yaml')
    if not vorlage and m.get('id') != ordner.name:
        fehler.append(f"manifest.yaml: id „{m.get('id')}“ muss wie der Ordner heißen („{ordner.name}“)")

    # Lizenztext passt grob zur Kennung.
    lizenz = (ordner / 'LICENSE').read_text(encoding='utf-8', errors='replace') if (ordner / 'LICENSE').exists() else ''
    kennung = str(m.get('lizenz', ''))
    merkmale = {'MIT': 'MIT License', 'Apache-2.0': 'Apache License', 'BSD-2-Clause': 'Redistribution and use',
                'BSD-3-Clause': 'Redistribution and use', 'MPL-2.0': 'Mozilla Public License', 'LGPL-3.0-or-later': 'GNU LESSER GENERAL PUBLIC LICENSE',
                'GPL-3.0-or-later': 'GNU GENERAL PUBLIC LICENSE', 'AGPL-3.0-or-later': 'GNU AFFERO GENERAL PUBLIC LICENSE', 'CC0-1.0': 'CC0'}
    if kennung in merkmale and merkmale[kennung].lower() not in lizenz.lower():
        fehler.append(f'LICENSE: passt nicht zur Lizenz „{kennung}“ aus manifest.yaml')
    if not vorlage and ('<Jahr>' in lizenz or '<Name>' in lizenz):
        fehler.append('LICENSE: <Jahr> und <Name> ausfüllen')
    if kennung == 'CC0-1.0' and 'code' in m:
        fehler.append('CC0-1.0 nur für Pakete ohne Code')

    # Changelog nennt die aktuelle Version.
    version = str(m.get('version', ''))
    if (ordner / 'CHANGELOG.md').exists() and not re.search(rf'^##\s+{re.escape(version)}\b', (ordner / 'CHANGELOG.md').read_text(encoding='utf-8'), re.M):
        fehler.append(f'CHANGELOG.md: kein Abschnitt „## {version}“')

    # Inhalte gegen das Schema; lokale Schlüssel eindeutig; Verweise auflösbar.
    inhalte = m.get('inhalt') or {}
    geladen: dict[str, list] = {}
    for art in ('mappentypen', 'sichten', 'beispiele'):
        if art not in inhalte:
            continue
        pfad = ordner / str(inhalte[art])
        if not pfad.exists():
            fehler.append(f'inhalt.{art}: Datei {inhalte[art]} fehlt')
            continue
        daten = lies_yaml(pfad, fehler) or []
        fehler += schema_fehler(inhalt_validator(art), daten, str(inhalte[art]))
        geladen[art] = daten if isinstance(daten, list) else []

    typen = {t.get('schluessel') for t in geladen.get('mappentypen', []) if isinstance(t, dict)}
    abh = set((m.get('abhaengigkeiten') or {}).keys())

    def verweis_ok(v: str, wo: str):
        if ':' in v:
            paket = v.split(':', 1)[0]
            if paket != m.get('id') and paket not in abh:
                fehler.append(f'{wo}: „{v}“ verweist auf Paket „{paket}“, das nicht unter abhaengigkeiten steht')
        elif v not in typen:
            fehler.append(f'{wo}: Mappentyp „{v}“ gibt es in diesem Paket nicht')

    gesehen: set[str] = set()
    for t in geladen.get('mappentypen', []):
        if not isinstance(t, dict):
            continue
        s = t.get('schluessel')
        if s in gesehen:
            fehler.append(f'mappentypen: Schlüssel „{s}“ doppelt')
        gesehen.add(s)
        if len(f"{m.get('id')}_{s}") > 40:
            fehler.append(f'mappentypen: „{m.get("id")}_{s}“ ist länger als 40 Zeichen')
        felder = {f.get('key') for f in t.get('felder', []) if isinstance(f, dict)}
        for f in t.get('felder', []):
            if isinstance(f, dict) and f.get('ziel'):
                verweis_ok(f['ziel'], f'mappentypen/{s}/{f.get("key")}')
        auf_registern: list[str] = []
        for r in t.get('register', []):
            if not isinstance(r, dict):
                continue
            for k in r.get('felder', []) or []:
                if k not in felder:
                    fehler.append(f'mappentypen/{s}: Register „{r.get("key")}“ nennt unbekanntes Feld „{k}“')
                auf_registern.append(k)
            for q in r.get('quellen', []) or []:
                verweis_ok(q.get('typ', ''), f'mappentypen/{s}/register/{r.get("key")}')
        ohne = felder - set(auf_registern)
        if ohne:
            fehler.append(f'mappentypen/{s}: Felder auf keinem Feldregister: {", ".join(sorted(ohne))}')
        doppelt = {k for k in auf_registern if auf_registern.count(k) > 1}
        if doppelt:
            fehler.append(f'mappentypen/{s}: Felder auf mehreren Registern: {", ".join(sorted(doppelt))}')
        for k in t.get('trefferliste', []) or []:
            if k not in felder and not k.startswith('_'):
                fehler.append(f'mappentypen/{s}: Trefferliste nennt unbekanntes Feld „{k}“')

    sichten = {s.get('schluessel') for s in geladen.get('sichten', []) if isinstance(s, dict)}
    for s in geladen.get('sichten', []):
        if not isinstance(s, dict):
            continue
        if s.get('eltern') and s['eltern'] not in sichten:
            fehler.append(f'sichten/{s.get("schluessel")}: Elternsicht „{s["eltern"]}“ fehlt')
        for t in s.get('typen', []) or []:
            verweis_ok(t, f'sichten/{s.get("schluessel")}')
    for b in geladen.get('beispiele', []):
        if isinstance(b, dict) and b.get('typ'):
            verweis_ok(b['typ'], 'beispiele')

    # tests/erwartung.yaml stimmt mit dem Inhalt überein.
    erw_pfad = ordner / 'tests' / 'erwartung.yaml'
    if erw_pfad.exists():
        erw = lies_yaml(erw_pfad, fehler) or {}
        if set(erw.get('mappentypen', [])) != typen:
            fehler.append('tests/erwartung.yaml: mappentypen passen nicht zu inhalt/')
        if set(erw.get('sichten', [])) != sichten:
            fehler.append('tests/erwartung.yaml: sichten passen nicht zu inhalt/')
        if 'beispiele' in erw and erw['beispiele'] != len(geladen.get('beispiele', [])):
            fehler.append('tests/erwartung.yaml: Anzahl beispiele passt nicht')
    elif not vorlage:
        fehler.append('tests/erwartung.yaml fehlt')

    if 'code' in m:
        quelle = ordner / str(m['code'].get('quelle', ''))
        if not quelle.is_dir() or not any(p.is_file() and p.name != 'README.md' for p in quelle.rglob('*')):
            fehler.append('code.quelle: kein Quellcode gefunden')

    if basis and not vorlage and geaendert(basis, ordner):
        alt = version_von(basis, m_pfad)
        if alt is not None and alt == version:
            fehler.append(f'version: Paket geändert, aber Version {version} nicht erhöht')
    return fehler


def main():
    args = sys.argv[1:]
    basis = None
    if args[:1] == ['--basis']:
        basis, args = args[1], args[2:]
    ordner = [Path(a).resolve() for a in args] or [WURZEL / 'vorlage', *sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir())]
    gesamt = 0
    for o in ordner:
        f = pruefe(o, basis)
        name = o.relative_to(WURZEL).as_posix()
        if f:
            gesamt += len(f)
            print(f'✗ {name}')
            for x in f:
                print(f'    {x}')
                if 'GITHUB_ACTIONS' in __import__('os').environ:
                    print(f'::error file={name}/manifest.yaml,title={name}::{x}')
        else:
            print(f'✓ {name}')
    sys.exit(1 if gesamt else 0)


if __name__ == '__main__':
    main()
