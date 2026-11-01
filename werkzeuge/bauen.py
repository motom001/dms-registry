#!/usr/bin/env python3
"""
Baut den Code von Paketen zu WebAssembly – in der CI aus dem Quellcode, nie aus eingecheckten .wasm-Dateien.

    python3 werkzeuge/bauen.py pakete/mein_paket ...       # bestimmte Pakete
    python3 werkzeuge/bauen.py --alle                       # alle Pakete mit Code
    python3 werkzeuge/bauen.py --geaendert origin/main      # nur Pakete, die sich gegenüber dem Stand geändert haben
    python3 werkzeuge/bauen.py --unveroeffentlicht <site>   # nur Versionen, die noch nicht im Katalog stehen

Je Paket läuft code/bauen.sh im Paketordner mit
    WASI_SDK   Pfad des WASI-SDK (werkzeuge/wasi-sdk.sh lädt es, falls nicht gesetzt)
    BAU        eigener Arbeitsordner außerhalb des Pakets (für Quellen von Bibliotheken, Zwischenstände)
und muss code/modul.wasm erzeugen; Daten für das Modul legt es nach code/daten/. Beides entsteht nur beim Bau
und gehört nicht ins Repository (.gitignore). Danach prüft das Werkzeug das Modul gegen die DMS-Paket-ABI.
"""
import json, os, subprocess, sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wasm  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent


def mit_code() -> list[Path]:
    return [p for p in sorted((WURZEL / 'pakete').iterdir()) if p.is_dir() and (p / 'code' / 'bauen.sh').exists()]


def geaendert(ref: str) -> list[Path]:
    r = subprocess.run(['git', 'diff', '--name-only', f'{ref}...HEAD', '--', 'pakete/', 'werkzeuge/bauen.py', 'werkzeuge/wasi-sdk.sh'],
                       cwd=WURZEL, capture_output=True, text=True, check=True)
    namen = r.stdout.split()
    if any(n.startswith('werkzeuge/') for n in namen):
        return mit_code()
    betroffen = {n.split('/')[1] for n in namen if n.startswith('pakete/')}
    return [p for p in mit_code() if p.name in betroffen]


def unveroeffentlicht(site: Path) -> list[Path]:
    katalog = site / 'katalog.json'
    bekannt = set()
    if katalog.exists():
        for p in json.loads(katalog.read_text(encoding='utf-8')).get('pakete', []):
            bekannt |= {(p['id'], v['version']) for v in p.get('versionen', [])}
    out = []
    for p in mit_code():
        m = yaml.safe_load((p / 'manifest.yaml').read_text(encoding='utf-8'))
        if (m['id'], m['version']) not in bekannt:
            out.append(p)
    return out


def sdk() -> str:
    if os.environ.get('WASI_SDK'):
        return os.environ['WASI_SDK']
    return subprocess.run([str(WURZEL / 'werkzeuge' / 'wasi-sdk.sh')], capture_output=True, text=True, check=True).stdout.strip()


def baue(ordner: Path, wasi: str) -> list[str]:
    bau = Path(os.environ.get('BAU_WURZEL', Path.home() / '.cache' / 'dms-registry' / 'bau')) / ordner.name
    bau.mkdir(parents=True, exist_ok=True)
    modul = ordner / 'code' / 'modul.wasm'
    modul.unlink(missing_ok=True)
    env = {**os.environ, 'WASI_SDK': wasi, 'BAU': str(bau)}
    r = subprocess.run(['bash', 'code/bauen.sh'], cwd=ordner, env=env)
    if r.returncode != 0:
        return [f'code/bauen.sh endet mit {r.returncode}']
    if not modul.exists():
        return ['code/bauen.sh hat kein code/modul.wasm erzeugt']
    fehler = wasm.pruefe(modul.read_bytes())
    if not fehler:
        print(f'  code/modul.wasm: {modul.stat().st_size / 1048576:.1f} MB')
    return fehler


def main():
    args = sys.argv[1:]
    if args[:1] == ['--alle']:
        pakete = mit_code()
    elif args[:1] == ['--geaendert']:
        pakete = geaendert(args[1])
    elif args[:1] == ['--unveroeffentlicht']:
        pakete = unveroeffentlicht(Path(args[1]))
    else:
        pakete = [Path(a).resolve() for a in args]
    if not pakete:
        print('Nichts zu bauen.')
        return
    wasi = sdk()
    gesamt = 0
    for p in pakete:
        print(f'▸ {p.relative_to(WURZEL).as_posix()}', flush=True)
        f = baue(p, wasi)
        for x in f:
            print(f'  ✗ {x}')
        gesamt += len(f)
    sys.exit(1 if gesamt else 0)


if __name__ == '__main__':
    main()
