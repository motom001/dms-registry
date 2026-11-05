#!/usr/bin/env python3
"""
Sprachpakete gegen Ablago prüfen (Ablago #731, Registry #116): Abdeckung je Sprache und was nicht passt.

    python3 werkzeuge/sprachen.py --ablago ../dms                     # alle Sprachpakete gegen einen Ablago-Checkout
    python3 werkzeuge/sprachen.py --ablago ../dms pakete/sprache_fr   # ein Sprachpaket
    python3 werkzeuge/sprachen.py --ablago ../dms --fehlend pakete/sprache_fr   # dazu: fehlende Texte (Englisch)

--ablago nennt einen Checkout von motom001/dms (es genügt shared/src/sprachen/). Die CI nimmt die neueste
veröffentlichte Version (.github/workflows/pruefen.yml) und schreibt die Abdeckung in die Zusammenfassung des Laufs.

Gleiche Regeln wie Ablago beim Installieren (shared/src/sprachpaket.ts):

- Fehler (Ablago lehnt das Paket ab): spitze Klammern, wo der deutsche Text keine hat (HTML), Steuerzeichen,
  kein Text, mehr als 4000 Zeichen.
- Hinweis (Ablago übergeht den Text, an seiner Stelle erscheint Englisch): Bereich oder Schlüssel gibt es nicht,
  Platzhalter, die der deutsche Text nicht hat. Das passiert, wenn sich Ablago weiterentwickelt – kein Grund, eine
  CI für andere Änderungen rot zu machen.

Abdeckung: Anteil der deutschen Schlüssel (Mehrzahlformen zählen einmal), die das Paket übersetzt – abgerundet,
100 % heißt vollständig. Ablago zeigt dieselbe Zahl unter Werkbank → Sprachen.
"""
import json, os, re, sys
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parent.parent
MEHRZAHL = re.compile(r'_(zero|one|two|few|many|other)$')
PLATZHALTER = re.compile(r'\{([A-Za-z0-9_]+)\}')
KLAMMERN = re.compile(r'[<>]')
STEUERZEICHEN = re.compile('[\x00-\x08\x0b-\x1f\x7f\u2028\u2029]')
SPRACHTEXT_MAX = 4000


def ohne_mehrzahl(k: str) -> str:
    return MEHRZAHL.sub('', k)


def platzhalter(text: str) -> set[str]:
    return set(PLATZHALTER.findall(text))


def lies_sprache(ordner: Path) -> dict[str, dict[str, str]]:
    """Alle Bereiche eines Ordners mit <bereich>.json."""
    return {p.stem: json.loads(p.read_text(encoding='utf-8')) for p in sorted(ordner.glob('*.json'))}


def formen(datei: dict, grund: str) -> list[str]:
    return [v for k, v in datei.items() if k == grund or ohne_mehrzahl(k) == grund]


def vergleiche(de: dict, texte: dict) -> dict:
    """Wie pruefeSprachtexte in Ablago: fehler, hinweise, übernommene Texte (Bereich → Schlüssel → Text)."""
    fehler: list[str] = []
    hinweise: list[str] = []
    gut: dict[str, dict[str, str]] = {}
    for bereich, datei in texte.items():
        soll = de.get(bereich)
        if soll is None:
            hinweise.append(f'texte/{bereich}.json: den Bereich gibt es in Ablago nicht')
            continue
        for k, v in (datei or {}).items():
            wo = f'texte/{bereich}.json: „{k}“'
            if not isinstance(v, str):
                fehler.append(f'{wo}: kein Text')
                continue
            if not v.strip():
                continue
            if len(v) > SPRACHTEXT_MAX:
                fehler.append(f'{wo}: länger als {SPRACHTEXT_MAX} Zeichen')
                continue
            if STEUERZEICHEN.search(v):
                fehler.append(f'{wo}: enthält Steuerzeichen')
                continue
            grund = ohne_mehrzahl(k)
            alle = formen(soll, grund) if grund != k else ([soll[k]] if k in soll else [])
            if not alle or (grund != k and f'{grund}_other' not in soll):
                hinweise.append(f'{wo}: den Schlüssel gibt es in Ablago nicht')
                continue
            if KLAMMERN.search(v) and not any(KLAMMERN.search(x) for x in alle):
                fehler.append(f'{wo}: spitze Klammern, wo der deutsche Text keine hat (HTML)')
                continue
            erlaubt = set().union(*(platzhalter(x) for x in alle))
            fremd = platzhalter(v) - erlaubt
            if fremd:
                hinweise.append(f'{wo}: Platzhalter {", ".join("{" + p + "}" for p in sorted(fremd))} gibt es im Deutschen nicht')
                continue
            gut.setdefault(bereich, {})[k] = v
    return {'fehler': fehler, 'hinweise': hinweise, 'texte': gut}


def abdeckung(de: dict, texte: dict) -> tuple[int, int, int]:
    vorhanden = gesamt = 0
    for bereich, datei in de.items():
        da = {ohne_mehrzahl(k) for k, v in (texte.get(bereich) or {}).items() if isinstance(v, str) and v.strip()}
        for g in {ohne_mehrzahl(k) for k in datei}:
            gesamt += 1
            vorhanden += g in da
    return vorhanden, gesamt, (vorhanden * 100 // gesamt if gesamt else 0)


def fehlend(de: dict, en: dict, texte: dict) -> list[str]:
    zeilen = []
    for bereich, datei in de.items():
        da = {ohne_mehrzahl(k) for k in (texte.get(bereich) or {})}
        for k in datei:
            if ohne_mehrzahl(k) not in da:
                zeilen.append(f'{bereich}.{k}\t{(en.get(bereich) or {}).get(k, datei[k])}')
    return zeilen


def sprachpakete(args: list[str]) -> list[Path]:
    if args:
        return [Path(a).resolve() for a in args]
    return sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir() and 'sprache' in (yaml.safe_load((p / 'manifest.yaml').read_text(encoding='utf-8')) or {}))


def main():
    args = sys.argv[1:]
    if '--ablago' not in args:
        print(__doc__)
        sys.exit(2)
    i = args.index('--ablago')
    ablago = Path(args[i + 1]).resolve()
    args = args[:i] + args[i + 2:]
    mit_fehlend = '--fehlend' in args
    args = [a for a in args if a != '--fehlend']
    de = lies_sprache(ablago / 'shared/src/sprachen/de')
    en = lies_sprache(ablago / 'shared/src/sprachen/en')
    version = json.loads((ablago / 'package.json').read_text(encoding='utf-8')).get('version', '?') if (ablago / 'package.json').exists() else '?'
    zeilen = [f'### Sprachpakete gegen Ablago {version}', '', '| Paket | Sprache | gemacht für | Abdeckung | Hinweise |', '|---|---|---|---|---|']
    gesamt_fehler = 0
    for ordner in sprachpakete(args):
        m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8')) or {}
        s = m.get('sprache') or {}
        texte = lies_sprache(ordner / 'texte')
        r = vergleiche(de, texte)
        vorhanden, gesamt, prozent = abdeckung(de, r['texte'])
        name = ordner.relative_to(WURZEL).as_posix() if ordner.is_relative_to(WURZEL) else ordner.name
        print(f'{"✗" if r["fehler"] else "✓"} {name}: {s.get("kennung")} – Übersetzung {prozent} % vollständig ({vorhanden} von {gesamt}), gemacht für Ablago {s.get("ablago")}')
        for f in r['fehler']:
            print(f'    {f}')
            if 'GITHUB_ACTIONS' in os.environ:
                print(f'::error file={name}/manifest.yaml,title={name}::{f}')
        for h in r['hinweise'][:20]:
            print(f'    Hinweis: {h}')
        if len(r['hinweise']) > 20:
            print(f'    Hinweis: … und {len(r["hinweise"]) - 20} weitere')
        if mit_fehlend:
            for z in fehlend(de, en, r['texte']):
                print(f'    fehlt: {z}')
        gesamt_fehler += len(r['fehler'])
        zeilen.append(f'| {m.get("id")} | {s.get("kennung")} | {s.get("ablago")} | {prozent} % ({vorhanden}/{gesamt}) | {len(r["hinweise"])} |')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write('\n'.join(zeilen) + '\n')
    sys.exit(1 if gesamt_fehler else 0)


if __name__ == '__main__':
    main()
