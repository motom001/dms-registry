#!/usr/bin/env python3
"""Kategorien und Symbole der Pakete, Issue-Vorlage „Fehler oder Wunsch zu einem Paket“ (#84, #86, #98).

    python3 werkzeuge/vorlagen.py            Vorlage .github/ISSUE_TEMPLATE/paket-meldung.yml neu schreiben
    python3 werkzeuge/vorlagen.py --pruefen  nur prüfen (CI): Kategorien und Symbole stimmig, Vorlage aktuell

Die Auswahlliste der Vorlage entsteht aus pakete/*/manifest.yaml, damit sie nie veraltet.
Kategorien (feste Liste, je Paket 1–2) und Symbole (Lucide, werkzeuge/symbole/) setzt der Autor im
Manifest (`kategorien`, `symbol`, `kuerzel`); für Pakete ohne diese Felder gilt die Zuordnung in
werkzeuge/kategorien.yaml. Das Manifest gewinnt.
"""
import functools
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parent.parent
KATEGORIEN = WURZEL / 'werkzeuge' / 'kategorien.yaml'
SYMBOLE = WURZEL / 'werkzeuge' / 'symbole'
SCHEMA_MANIFEST = WURZEL / 'schema' / 'manifest.schema.json'
VORLAGE = WURZEL / '.github' / 'ISSUE_TEMPLATE' / 'paket-meldung.yml'
KENNUNG = re.compile(r'^[a-z][a-z0-9_]{1,19}$')
KUERZEL = re.compile(r'^[A-Z]{2,3}$')
# Nur diese Formen dürfen in einem Symbol stehen (kein Text, keine Skripte, keine Verweise nach außen).
FORMEN = {'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse'}
SVG_NS = '{http://www.w3.org/2000/svg}'
ATTRIBUTE = {'d', 'fill', 'cx', 'cy', 'r', 'rx', 'ry', 'x', 'y', 'x1', 'x2', 'y1', 'y2', 'width', 'height', 'points'}


def lies_kategorien() -> dict:
    return yaml.safe_load(KATEGORIEN.read_text(encoding='utf-8'))


def kategorien_von(pid: str, daten: dict | None = None, manifest: dict | None = None) -> list[str]:
    """Kategorien eines Pakets: aus dem Manifest, sonst aus kategorien.yaml (leer, wenn es noch keine hat)."""
    if manifest and manifest.get('kategorien'):
        return list(manifest['kategorien'])
    daten = daten or lies_kategorien()
    return list((daten.get('pakete') or {}).get(pid) or [])


def symbol_aus_liste(pid: str, daten: dict) -> tuple[str | None, str | None]:
    eintrag = (daten.get('symbole') or {}).get(pid)
    if isinstance(eintrag, dict):
        return eintrag.get('symbol'), eintrag.get('kuerzel')
    return (eintrag or None), None


def symbol_von(pid: str, daten: dict | None = None, manifest: dict | None = None) -> tuple[str | None, str | None]:
    """(Symbol, Kürzel) eines Pakets: aus dem Manifest, sonst aus kategorien.yaml; (None, None) ohne Symbol."""
    if manifest and manifest.get('symbol'):
        return manifest['symbol'], manifest.get('kuerzel')
    return symbol_aus_liste(pid, daten or lies_kategorien())


def abweichungen(pid: str, manifest: dict, daten: dict | None = None) -> list[str]:
    """Hinweise, wo Manifest und kategorien.yaml verschieden sind (das Manifest gewinnt)."""
    daten = daten or lies_kategorien()
    hinweise = []
    liste = list((daten.get('pakete') or {}).get(pid) or [])
    if manifest.get('kategorien') and liste and list(manifest['kategorien']) != liste:
        hinweise.append(f'kategorien: Manifest {list(manifest["kategorien"])} und werkzeuge/kategorien.yaml {liste} sind verschieden – '
                        'es gilt das Manifest; bitte den Eintrag in kategorien.yaml angleichen oder entfernen')
    s_liste = symbol_aus_liste(pid, daten)
    if manifest.get('symbol') and s_liste[0] and (manifest['symbol'], manifest.get('kuerzel')) != s_liste:
        hinweise.append(f'symbol: Manifest „{manifest["symbol"]}“ und werkzeuge/kategorien.yaml „{s_liste[0]}“ sind verschieden – '
                        'es gilt das Manifest; bitte den Eintrag in kategorien.yaml angleichen oder entfernen')
    return hinweise


def symbolnamen() -> list[str]:
    """Erlaubte Symbole: genau die SVG-Dateien in werkzeuge/symbole/ (dieselben wie im Schema)."""
    return sorted(p.stem for p in SYMBOLE.glob('*.svg'))


def schema_aufzaehlung(feld: str) -> list[str]:
    s = json.loads(SCHEMA_MANIFEST.read_text(encoding='utf-8'))['properties'][feld]
    return list(s.get('enum') or s['items']['enum'])


def symbol_teile(name: str) -> list[tuple[str, dict]]:
    """Formen eines Symbols (Tag, Attribute) aus werkzeuge/symbole/<name>.svg; Fehler bei allem anderen."""
    wurzel = ET.fromstring((SYMBOLE / f'{name}.svg').read_text(encoding='utf-8'))
    if wurzel.tag != f'{SVG_NS}svg' or wurzel.get('viewBox') != '0 0 24 24':
        raise ValueError(f'{name}.svg: kein Lucide-Symbol (svg mit viewBox 0 0 24 24 erwartet)')
    teile = []
    for kind in wurzel:
        tag = kind.tag.removeprefix(SVG_NS)
        if tag not in FORMEN or len(kind) or (kind.text or '').strip():
            raise ValueError(f'{name}.svg: <{tag}> ist in einem Symbol nicht erlaubt')
        if set(kind.attrib) - ATTRIBUTE or any(not re.fullmatch(r'[0-9A-Za-z .,-]*', v) for v in kind.attrib.values()):
            raise ValueError(f'{name}.svg: Attribut in <{tag}> nicht erlaubt')
        teile.append((tag, dict(kind.attrib)))
    return teile


@functools.cache
def symbol_svg(name: str) -> str | None:
    """Symbol als SVG zum Einbetten in die Seite (einfarbig in Textfarbe, aria-hidden); None, wenn es das Symbol nicht gibt."""
    if name not in symbolnamen():
        return None
    innen = ''.join(f'<{tag} ' + ' '.join(f'{k}="{html.escape(v)}"' for k, v in attr.items()) + '/>' for tag, attr in symbol_teile(name))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{innen}</svg>')


def pakete() -> list[dict]:
    liste = []
    for ordner in sorted(p for p in (WURZEL / 'pakete').iterdir() if (p / 'manifest.yaml').exists()):
        m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8'))
        liste.append({'id': m['id'], 'name': m['name'], 'manifest': m})
    return sorted(liste, key=lambda p: p['name'].lower())


def option(p: dict) -> str:
    """Eintrag der Auswahlliste; die Kennung in Klammern liest der Workflow für das Label."""
    return f'{p["name"]} ({p["id"]})'


def pruefe_kategorien(daten: dict, liste: list[dict]) -> list[str]:
    fehler = []
    bekannt = []
    for k in daten.get('kategorien') or []:
        if not KENNUNG.match(str(k.get('kennung', ''))) or not k.get('de') or not k.get('en'):
            fehler.append(f'kategorien.yaml: Kategorie {k!r} braucht kennung, de und en')
        bekannt.append(k.get('kennung'))
    if sorted(bekannt) != sorted(schema_aufzaehlung('kategorien')):
        fehler.append('kategorien.yaml und schema/manifest.schema.json (kategorien) nennen verschiedene Kategorien – beide angleichen')
    zuordnung = daten.get('pakete') or {}
    ids = {p['id'] for p in liste}
    for p in liste:
        ks = kategorien_von(p['id'], daten, p.get('manifest'))
        if not ks:
            fehler.append(f'kategorien.yaml: Paket „{p["id"]}“ hat keine Kategorie – bitte 1–2 aus der Liste im Manifest (kategorien) oder hier eintragen')
            continue
        if len(ks) > 2:
            fehler.append(f'kategorien.yaml: Paket „{p["id"]}“ hat mehr als 2 Kategorien')
        for k in ks:
            if k not in bekannt:
                fehler.append(f'kategorien.yaml: Paket „{p["id"]}“: unbekannte Kategorie „{k}“')
    for pid in zuordnung:
        if pid not in ids:
            fehler.append(f'kategorien.yaml: „{pid}“ ist kein Paket in pakete/')
    # Symbole (#98): erlaubt sind genau die SVG-Dateien in werkzeuge/symbole/, und dieselben im Schema.
    namen = symbolnamen()
    if namen != sorted(schema_aufzaehlung('symbol')):
        fehler.append('werkzeuge/symbole/*.svg und schema/manifest.schema.json (symbol) nennen verschiedene Symbole – beide angleichen')
    for name in namen:
        try:
            symbol_teile(name)
        except (ValueError, ET.ParseError) as x:
            fehler.append(f'werkzeuge/symbole/{x}')
    for pid, eintrag in (daten.get('symbole') or {}).items():
        if pid not in ids:
            fehler.append(f'kategorien.yaml: symbole: „{pid}“ ist kein Paket in pakete/')
        if isinstance(eintrag, dict) and set(eintrag) - {'symbol', 'kuerzel'}:
            fehler.append(f'kategorien.yaml: symbole: „{pid}“: nur symbol und kuerzel möglich')
        s, k = symbol_aus_liste(pid, daten)
        if s not in namen:
            fehler.append(f'kategorien.yaml: symbole: „{pid}“: unbekanntes Symbol „{s}“ – erlaubt: {", ".join(namen)}')
        if k is not None and not KUERZEL.match(str(k)):
            fehler.append(f'kategorien.yaml: symbole: „{pid}“: Kürzel „{k}“ – 2–3 Großbuchstaben, z. B. FR')
    return fehler


def vorlage(liste: list[dict]) -> str:
    optionen = '\n'.join(f'        - {yaml.safe_dump(option(p), allow_unicode=True).strip().removesuffix("...").strip()}' for p in liste)
    return f'''# Erzeugt von werkzeuge/vorlagen.py aus pakete/*/manifest.yaml – nicht von Hand ändern.
# Generated by werkzeuge/vorlagen.py – do not edit by hand.
name: Fehler oder Wunsch zu einem Paket · Bug or wish for a package
description: Etwas an einem vorhandenen Paket funktioniert nicht oder fehlt · Something in an existing package is broken or missing
title: "[Paket] "
labels: [paket]
body:
  - type: markdown
    attributes:
      value: |
        Danke, dass du dir die Zeit nimmst! Deutsch oder Englisch – beides ist willkommen.
        **Bitte keine echten Namen, Adressen, Kunden- oder Vertragsnummern und keine Fotos echter Unterlagen.** Nimm erfundene Beispiele (z. B. Lena, Jonas).
        Ein ganz neues Paket schlägst du mit der Vorlage „Paket (User Story)“ vor.

        Thanks for taking the time! **Please no real names, addresses, customer or contract numbers and no photos of real documents.**
  - type: dropdown
    id: paket
    attributes:
      label: Welches Paket? · Which package?
      options:
{optionen}
    validations:
      required: true
  - type: input
    id: paketversion
    attributes:
      label: Paketversion · Package version
      description: Steht in Ablago unter Werkbank → Pakete · Shown in Ablago under Workbench → Packages
      placeholder: z. B. 1.3.0
  - type: input
    id: dmsversion
    attributes:
      label: Ablago-Version · Ablago version
      description: Steht in Ablago unter „Über Ablago“ (Benutzermenü) · Shown under “About Ablago” (user menu)
      placeholder: z. B. 0.144.2
  - type: checkboxes
    id: betrifft
    attributes:
      label: Was betrifft es? · What is it about?
      options:
        - label: Mappentyp oder Feld · Mappe type or field
        - label: Ansicht · View
        - label: Beispielmappen · Sample Mappen
        - label: Wörter für die Suche · Search words
        - label: Funktion des Pakets (Code) · Package function (code)
        - label: Rechte · Permissions
        - label: Installation oder Update · Installation or update
        - label: Text oder Beschreibung · Text or description
        - label: Sonstiges · Other
  - type: dropdown
    id: art
    attributes:
      label: Fehler oder Wunsch? · Bug or wish?
      options:
        - Fehler – etwas funktioniert nicht · Bug – something does not work
        - Wunsch – etwas fehlt oder könnte besser sein · Wish – something is missing or could be better
    validations:
      required: true
  - type: textarea
    id: beschreibung
    attributes:
      label: Beschreibung · Description
      description: |
        Fehler: Was hast du getan, was ist passiert, was hast du erwartet?
        Wunsch: Als … möchte ich …, damit …
        Bug: what did you do, what happened, what did you expect? · Wish: As a … I want …, so that …
    validations:
      required: true
'''


def main():
    pruefen = sys.argv[1:] == ['--pruefen']
    liste = pakete()
    fehler = pruefe_kategorien(lies_kategorien(), liste)
    soll = vorlage(liste)
    if pruefen:
        if not VORLAGE.exists() or VORLAGE.read_text(encoding='utf-8') != soll:
            fehler.append('.github/ISSUE_TEMPLATE/paket-meldung.yml ist nicht aktuell – python3 werkzeuge/vorlagen.py ausführen')
        for f in fehler:
            print(f'✗ {f}')
        print('✓ Kategorien und Issue-Vorlage' if not fehler else '')
        sys.exit(1 if fehler else 0)
    VORLAGE.write_text(soll, encoding='utf-8')
    for f in fehler:
        print(f'✗ {f}')
    print(f'Vorlage geschrieben: {len(liste)} Pakete')
    sys.exit(1 if fehler else 0)


if __name__ == '__main__':
    main()
