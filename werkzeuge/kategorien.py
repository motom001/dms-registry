"""
Kategorien des Paketkatalogs (#84) aus werkzeuge/kategorien.yaml – gemeinsam für pruefen.py, katalog.py und
webseite.py.

Stufe 1: Die Zuordnung Paket → Kategorien steht in dieser Datei, nicht im Manifest. Je Paket 1 oder 2 Kennungen
aus der festen Liste; die erste ist die Hauptkategorie (Ziel von „Ähnliche Pakete ›“ auf der Paketseite).
"""
import re
from pathlib import Path

import yaml

DATEI = Path(__file__).resolve().parent / 'kategorien.yaml'
KENNUNG = re.compile(r'^[a-z][a-z0-9]{1,19}$')
HOECHSTENS = 2


def lade(pfad: Path = DATEI) -> dict:
    """{'kategorien': [{'kennung', 'de', 'en'}, …], 'pakete': {id: [kennung, …]}} – ohne Prüfung."""
    daten = yaml.safe_load(pfad.read_text(encoding='utf-8')) or {}
    return {'kategorien': daten.get('kategorien') or [], 'pakete': daten.get('pakete') or {}}


def fehler_der_liste(daten: dict) -> list[str]:
    """Prüft die Liste der Kategorien selbst: Kennung gültig und eindeutig, Name deutsch und englisch."""
    fehler, gesehen = [], set()
    if not isinstance(daten.get('kategorien'), list) or not daten['kategorien']:
        return ['kategorien: Liste fehlt oder ist leer']
    for i, k in enumerate(daten['kategorien'], 1):
        if not isinstance(k, dict):
            fehler.append(f'kategorien[{i}]: erwartet kennung, de und en')
            continue
        kennung = k.get('kennung')
        if not isinstance(kennung, str) or not KENNUNG.match(kennung):
            fehler.append(f'kategorien[{i}]: Kennung „{kennung}“ ungültig (Kleinbuchstaben und Ziffern, 2–20 Zeichen)')
        elif kennung in gesehen:
            fehler.append(f'kategorien[{i}]: Kennung „{kennung}“ doppelt')
        gesehen.add(kennung)
        for sprache in ('de', 'en'):
            if not isinstance(k.get(sprache), str) or not k[sprache].strip():
                fehler.append(f'kategorien[{i}] ({kennung}): Name „{sprache}“ fehlt')
        if set(k) - {'kennung', 'de', 'en'}:
            fehler.append(f'kategorien[{i}] ({kennung}): unbekannte Angabe ' + ', '.join(sorted(set(k) - {'kennung', 'de', 'en'})))
    if not isinstance(daten.get('pakete'), dict):
        fehler.append('pakete: erwartet Paket-Id → Liste von Kennungen')
    return fehler


def kennungen(daten: dict) -> list[str]:
    return [k['kennung'] for k in daten['kategorien'] if isinstance(k, dict) and isinstance(k.get('kennung'), str)]


def fehler_des_pakets(daten: dict, pid: str) -> list[str]:
    """Fehler zur Zuordnung eines Pakets – klar genug, dass ein Autor sie ohne Nachfragen beheben kann."""
    erlaubt = kennungen(daten)
    liste = ', '.join(erlaubt)
    pakete = daten.get('pakete') if isinstance(daten.get('pakete'), dict) else {}
    if pid not in pakete:
        return [f'Kategorie fehlt: in werkzeuge/kategorien.yaml unter „pakete:“ eine Zeile „{pid}: [<kennung>]“ eintragen '
                f'(1–{HOECHSTENS} Kennungen aus: {liste}; siehe REGELN.md, „Kategorien“)']
    wert = pakete[pid]
    if not isinstance(wert, list) or not all(isinstance(x, str) for x in wert):
        return [f'werkzeuge/kategorien.yaml: „{pid}“ braucht eine Liste, z. B. „{pid}: [{erlaubt[0] if erlaubt else "vorlagen"}]“']
    fehler = []
    if not 1 <= len(wert) <= HOECHSTENS:
        fehler.append(f'werkzeuge/kategorien.yaml: „{pid}“ hat {len(wert)} Kategorien – erlaubt sind 1 bis {HOECHSTENS}')
    if len(set(wert)) != len(wert):
        fehler.append(f'werkzeuge/kategorien.yaml: „{pid}“ nennt eine Kategorie doppelt')
    for x in wert:
        if x not in erlaubt:
            fehler.append(f'werkzeuge/kategorien.yaml: „{pid}“: unbekannte Kategorie „{x}“ (erlaubt: {liste}; neue Kategorien nur über ein Issue)')
    return fehler


def fehler_gesamt(daten: dict, ids: set[str]) -> list[str]:
    """Liste prüfen und Einträge für Pakete, die es nicht (mehr) gibt."""
    fehler = fehler_der_liste(daten)
    if isinstance(daten.get('pakete'), dict):
        for pid in sorted(set(daten['pakete']) - ids):
            fehler.append(f'pakete: „{pid}“ gibt es unter pakete/ nicht – Eintrag entfernen oder Id korrigieren')
    return fehler


def von(daten: dict, pid: str) -> list[str]:
    """Kategorien eines Pakets in der Reihenfolge der Datei (erste = Hauptkategorie); leer, wenn keine."""
    wert = (daten.get('pakete') or {}).get(pid)
    return list(wert) if isinstance(wert, list) else []


def namen(daten: dict, sprache: str) -> dict[str, str]:
    """Kennung → Name in einer Sprache, in der Reihenfolge der Liste."""
    return {k['kennung']: k.get(sprache) or k.get('de') or k['kennung'] for k in daten['kategorien'] if isinstance(k, dict) and 'kennung' in k}
