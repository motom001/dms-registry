#!/usr/bin/env python3
"""
Baut den Katalog der Registry: je Paket ein Archiv <id>-<version>.zip und katalog.json.

    python3 werkzeuge/katalog.py <ausgabe>              # Ausgabeordner = bisheriger Stand (z. B. gh-pages)
    python3 werkzeuge/katalog.py --probe <ausgabe>      # nur prüfen, nichts schreiben
    python3 werkzeuge/katalog.py --ohne-bau <ausgabe>   # Probe-Katalog, Pakete mit Code ohne gebautes Modul

Pakete mit Code (code/bauen.sh) baut vorher werkzeuge/bauen.py; ohne code/modul.wasm gibt es kein Archiv.

Im Ausgabeordner liegen danach:

    katalog.json                    alle Pakete mit allen Versionen (Format: schema/katalog.schema.json)
                                    – signiert danach werkzeuge/signieren.py (katalog.sig)
    archive/<id>-<version>.zip      genau die Dateien des Paketordners, ohne Unterordner davor – neue Archive;
                                    auf GitHub Pages bleiben die Versionen nach SPIEGEL_VERSIONEN (#133)

Jede Version liegt als Datei an einem GitHub-Release (Tag <id>-v<version>, #156): Dorthin zeigt `archiv`, von dort
lädt Ablago, und GitHub zählt die Downloads. `spiegel` nennt die Kopie auf GitHub Pages, aus der die Sammeldatei im
Browser zusammengestellt wird (Release-Downloads erlauben keinen Abruf aus dem Browser). Releases anlegen, Downloads
zählen und Pages ausdünnen macht danach werkzeuge/releases.py.

Ältere Versionen bleiben erhalten. Ein Archiv mit gleicher Id und Version ändert sich nie: Ist der Inhalt
eines Pakets anders als im veröffentlichten Archiv, die Version aber gleich, bricht das Skript ab. Liegt das Archiv
nicht mehr auf Pages, holt das Skript es dafür vom Release.

Braucht: pip install pyyaml jsonschema
"""
import hashlib, io, json, sys, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vorlagen import kategorien_von, lies_kategorien, symbol_von  # noqa: E402
from jsonschema import Draft202012Validator

WURZEL = Path(__file__).resolve().parent.parent
REPO = 'https://github.com/motom001/dms-registry'
FORMAT = 1
ZEIT = (1980, 1, 1, 0, 0, 0)
# Nur zum Ausprobieren (Webseite): Pakete mit Code auch ohne gebautes Modul.
OHNE_BAU = False


# Releases (#156): eine je Paketversion, die Datei heißt wie das Archiv.
RELEASES = f'{REPO}/releases/download'
# Wie viele Versionen je Paket als Spiegel auf GitHub Pages bleiben – für die Sammeldatei im Browser (#133,
# Entscheidung Thomas 10.11.2026 16:54: nur die aktuelle). werkzeuge/releases.py ausduennen entfernt die übrigen;
# alle Versionen bleiben am Release und im Katalog. None = alle.
SPIEGEL_VERSIONEN: int | None = 1


def tag(pid: str, version: str) -> str:
    return f'{pid}-v{version}'


def release_url(pid: str, version: str) -> str:
    return f'{RELEASES}/{tag(pid, version)}/{pid}-{version}.zip'


def spiegeln(versionen: list[dict]) -> set[str]:
    """Versionen (neueste zuerst), deren Archiv auf GitHub Pages bleibt."""
    return {v['version'] for v in (versionen if SPIEGEL_VERSIONEN is None else versionen[:SPIEGEL_VERSIONEN])}


def hole(url: str) -> bytes:
    """Ein veröffentlichtes Archiv laden (Release, folgt der Weiterleitung von GitHub)."""
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'dms-registry-katalog'}), timeout=120) as a:
        return a.read(PAKET_MAX + 1)


# Die eine Größengrenze für Pakete, wie im DMS (PAKET_MAX, DMS #644) und in pruefen.py/sammeldatei.py.
PAKET_MAX = 128 * 1024 * 1024


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


def ohne_erzeugtes(inhalt: dict[str, bytes]) -> dict[str, bytes]:
    """Ohne das, was beim Bau entsteht (code/modul.wasm, code/daten/): Ob sich ein Paket geändert hat, entscheidet der Quellcode."""
    return {n: d for n, d in inhalt.items() if n != 'code/modul.wasm' and not n.startswith('code/daten/')}


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
            # Beispiel-Dokumente (motom001/dms#878, Registry #137): nur, wenn es welche gibt.
            **({'beispieldokumente': n} if (n := sum(len(b.get('dokumente') or []) for b in beispiele if isinstance(b, dict))) else {}),
        },
        'code': 'code' in m,
        'archiv': release_url(pid, m['version']),
        'sha256': hashlib.sha256(daten).hexdigest(),
        'groesse': len(daten),
        'veroeffentlicht': veroeffentlicht,
        'quelle': f'{REPO}/tree/main/pakete/{pid}',
        'readme': f'{REPO}/blob/main/pakete/{pid}/README.md',
        'changelog': f'{REPO}/blob/main/pakete/{pid}/CHANGELOG.md',
        # Ergänzung eines anderen Pakets (motom001/dms#405), im Katalog immer als Objekt.
        **({'ergaenzt': ergaenzt_von(m)} if m.get('ergaenzt') else {}),
        # Sprachpaket (motom001/dms#731): Ablago und die Katalog-Webseite zeigen „Maschinell übersetzt …“ bzw. „Geprüft von …“.
        **({'sprache': sprache_von(m)} if isinstance(m.get('sprache'), dict) else {}),
    }


def sprache_von(m: dict) -> dict:
    """sprache aus dem Manifest für den Katalog: kennung, maschinell, ablago, geprueft_von (falls da)."""
    s = m['sprache']
    return {'kennung': s['kennung'], 'maschinell': bool(s['maschinell']), 'ablago': str(s['ablago']),
            **({'geprueft_von': str(s['geprueft_von'])} if s.get('geprueft_von') else {})}


def ergaenzt_von(m: dict) -> dict:
    """ergaenzt aus dem Manifest als { paket, gruppe? } – Kurzform „ergaenzt: texterkennung“ eingeschlossen."""
    e = m['ergaenzt']
    return {'paket': e} if isinstance(e, str) else {k: e[k] for k in ('paket', 'gruppe') if k in e}


def versionsschluessel(v: str):
    return tuple(int(x) for x in v.split('.'))


def baue(ausgabe: Path, probe: bool) -> list[str]:
    fehler: list[str] = []
    alt_pfad = ausgabe / 'katalog.json'
    alt = json.loads(alt_pfad.read_text(encoding='utf-8')) if alt_pfad.exists() else {'pakete': []}
    pakete = {p['id']: p for p in alt.get('pakete', [])}
    jetzt = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    neu: list[tuple[str, bytes]] = []
    manifeste: dict[str, dict] = {}  # Manifest der neuesten Version je Paket (für Kategorien und Symbol)

    for ordner in sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir()):
        m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8'))
        pid, version = m['id'], m['version']
        name = f'{pid}-{version}.zip'
        inhalt = dateien(ordner)
        vorhanden = ausgabe / 'archive' / name
        p = pakete.setdefault(pid, {'id': pid, 'versionen': []})
        bekannt = next((v for v in p['versionen'] if v['version'] == version), None)
        if vorhanden.exists() or bekannt:
            if vorhanden.exists():
                daten = vorhanden.read_bytes()
            else:
                # Nicht mehr auf Pages (#133): vom Release holen und gegen den Katalog prüfen.
                try:
                    daten = hole(bekannt['archiv'] if bekannt['archiv'].startswith('https://') else release_url(pid, version))
                except Exception as x:  # noqa: BLE001
                    fehler.append(f'{pid}: Version {version} ist veröffentlicht, das Archiv lässt sich aber nicht laden ({x})')
                    continue
                if hashlib.sha256(daten).hexdigest() != bekannt['sha256']:
                    fehler.append(f'{pid}: Archiv {version} am Release passt nicht zur Prüfsumme im Katalog')
                    continue
            if ohne_erzeugtes(inhalt_von(daten)) != ohne_erzeugtes(inhalt):
                fehler.append(f'{pid}: Inhalt geändert, aber Version {version} ist schon veröffentlicht – Version erhöhen')
                continue
        else:
            if (ordner / 'code' / 'bauen.sh').exists() and 'code/modul.wasm' not in inhalt and not probe and not OHNE_BAU:
                fehler.append(f'{pid}: code/modul.wasm fehlt – vorher bauen (python3 werkzeuge/bauen.py --unveroeffentlicht <ausgabe>)')
                continue
            daten = archiv(inhalt)
            if len(daten) > PAKET_MAX:
                fehler.append(f'{pid}: Archiv {len(daten) / 1048576:.1f} MB – höchstens {PAKET_MAX // 1048576} MB je Paket (DMS #644)')
                continue
            neu.append((name, daten))
        v = eintrag(ordner, m, name, daten, bekannt['veroeffentlicht'] if bekannt else jetzt)
        if bekannt and 'downloads' in bekannt:
            v['downloads'] = bekannt['downloads']
        p['versionen'] = sorted([x for x in p['versionen'] if x['version'] != version] + [v], key=lambda x: versionsschluessel(x['version']), reverse=True)
        # Angaben des Pakets aus der neuesten Version.
        if p['versionen'][0]['version'] == version:
            p.update({'name': m['name'], 'beschreibung': m['beschreibung'], 'autor': m['autor'], 'lizenz': m['lizenz'], 'aktuell': version})
            manifeste[pid] = m
    # Kategorien (#84) und Symbol (#98): aus dem Manifest der neuesten Version, sonst aus werkzeuge/kategorien.yaml
    # (Übergang, bis die Pakete die Felder mit ihrer nächsten Version mitbringen). Das DMS ignoriert die Felder.
    kat = lies_kategorien()
    for pid, p in pakete.items():
        m = manifeste.get(pid)
        werte = {'kategorien': kategorien_von(pid, kat, m)}
        werte['symbol'], werte['kuerzel'] = symbol_von(pid, kat, m)
        if not werte['symbol']:
            werte['kuerzel'] = None
        for feld, wert in werte.items():
            if wert:
                p[feld] = wert
            else:
                p.pop(feld, None)

    # Alle Versionen (auch ältere ohne Paketordner) laden vom Release; die letzten bleiben als Spiegel auf Pages.
    for pid, p in pakete.items():
        behalten = spiegeln(p['versionen'])
        for v in p['versionen']:
            v['archiv'] = release_url(pid, v['version'])
            if v['version'] in behalten:
                v['spiegel'] = f'archive/{pid}-{v["version"]}.zip'
            else:
                v.pop('spiegel', None)

    # Eine Id nur einmal (Registry #173): Jede Id im Katalog steht in werkzeuge/ids.txt.
    ids_pfad = WURZEL / 'werkzeuge' / 'ids.txt'
    if ids_pfad.exists():
        bekannt_ids = {z.strip() for z in ids_pfad.read_text(encoding='utf-8').splitlines() if z.strip() and not z.startswith('#')}
        for pid in sorted(set(pakete) - bekannt_ids):
            fehler.append(f'{pid}: fehlt in werkzeuge/ids.txt – jede veröffentlichte Id gehört dorthin (Registry #173)')

    katalog = {
        'format': FORMAT,
        'erstellt': jetzt,
        'quelle': REPO,
        # Die Signatur steht getrennt in katalog.sig (werkzeuge/signieren.py, #74), damit ältere DMS-Versionen
        # diesen Katalog unverändert lesen; das Feld bleibt null.
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
    global OHNE_BAU
    if args[:1] == ['--ohne-bau']:
        OHNE_BAU, args = True, args[1:]
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
