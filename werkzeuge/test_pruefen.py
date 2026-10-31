"""Tests für pruefen.py: Einstellungen und Aktionen im Manifest (#5).

    python3 -m unittest werkzeuge/test_pruefen.py
"""
import shutil, sys, tempfile, unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pruefen  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent

GUELTIG = {
    'sprache': 'rust', 'quelle': 'code/',
    'rechte': {'lesen': ['vorlage:beispiel']},
    'einstellungen': [
        {'abschnitt': 'Allgemein', 'felder': [
            {'schluessel': 'aktiv', 'name': 'Aktiv', 'typ': 'janein', 'standard': True},
            {'schluessel': 'grenze', 'name': 'Grenze', 'typ': 'zahl', 'min': 0, 'max': 10, 'standard': 5},
            {'schluessel': 'ab', 'name': 'Ab', 'typ': 'datum', 'standard': '2027-01-01'},
            {'schluessel': 'sprache', 'name': 'Sprache', 'typ': 'auswahl', 'optionen': ['Deutsch', 'Englisch'], 'standard': 'Deutsch'},
            {'schluessel': 'tage', 'name': 'Tage', 'typ': 'mehrfachauswahl', 'optionen': ['Mo', 'Di'], 'standard': ['Mo']},
            {'schluessel': 'token', 'name': 'Token', 'typ': 'geheim'},
            {'schluessel': 'feld', 'name': 'Feld', 'typ': 'feld', 'mappentyp': 'beispiel'},
            {'schluessel': 'wer', 'name': 'Wer', 'typ': 'benutzer'},
        ]},
        {'liste': 'regeln', 'name': 'Regeln', 'eintrag': 'Regel', 'sortierbar': True, 'felder': [
            {'schluessel': 'text', 'name': 'Text', 'typ': 'text'},
            {'schluessel': 'ziel', 'name': 'Ziel', 'typ': 'mappentyp', 'pflicht': True},
        ]},
    ],
    'aktionen': [{'schluessel': 'anwenden', 'name': 'Anwenden', 'bestaetigen': True}],
}


class Einstellungen(unittest.TestCase):
    def paket(self, code: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['code'] = code
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'code' / 'main.rs').write_text('fn main() {}\n', encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def mit(self, **aenderung) -> dict:
        import copy
        c = copy.deepcopy(GUELTIG)
        for weg, wert in aenderung.items():
            block, feld, eigenschaft = weg.split('__')
            c['einstellungen'][int(block)]['felder'][int(feld)][eigenschaft] = wert
        return c

    def test_gueltig(self):
        self.assertEqual(self.paket(GUELTIG), [])

    def test_vorgaben_passen_zum_typ(self):
        self.assertTrue(any('true oder false' in f for f in self.paket(self.mit(**{'0__0__standard': 'ja'}))))
        self.assertTrue(any('zwischen min und max' in f for f in self.paket(self.mit(**{'0__1__standard': 11}))))
        self.assertTrue(any('Datum' in f for f in self.paket(self.mit(**{'0__2__standard': '1.1.2027'}))))
        self.assertTrue(any('nicht in optionen' in f for f in self.paket(self.mit(**{'0__3__standard': 'Französisch'}))))
        self.assertTrue(any('geheim hat keine Vorgabe' in f for f in self.paket(self.mit(**{'0__5__standard': 'abc'}))))
        self.assertTrue(any('keine Vorgabe' in f for f in self.paket(self.mit(**{'0__7__standard': 'x'}))))

    def test_auswahl_braucht_optionen(self):
        c = self.mit()
        del c['einstellungen'][0]['felder'][3]['optionen']
        del c['einstellungen'][0]['felder'][3]['standard']
        self.assertTrue(any('braucht optionen' in f for f in self.paket(c)))

    def test_schluessel_eindeutig(self):
        c = self.mit(**{'0__1__schluessel': 'aktiv'})
        self.assertTrue(any('„aktiv“ doppelt' in f for f in self.paket(c)))
        c = self.mit()
        c['einstellungen'][0]['felder'][0]['schluessel'] = 'regeln'
        self.assertTrue(any('„regeln“ doppelt' in f for f in self.paket(c)))
        c = self.mit()
        c['aktionen'].append({'schluessel': 'anwenden', 'name': 'Noch mal'})
        self.assertTrue(any('code.aktionen' in f for f in self.paket(c)))

    def test_verweise_nur_auf_abhaengigkeiten(self):
        self.assertTrue(any('nicht unter abhaengigkeiten' in f for f in self.paket(self.mit(**{'0__6__mappentyp': 'basis:organisation'}))))
        self.assertTrue(any('gibt es in diesem Paket nicht' in f for f in self.paket(self.mit(**{'0__6__mappentyp': 'gibtsnicht'}))))
        self.assertTrue(any('nur bei typ feld' in f for f in self.paket(self.mit(**{'0__7__mappentyp': 'beispiel'}))))

    def test_mehr_als_zwei_ebenen_geht_nicht(self):
        c = self.mit()
        c['einstellungen'][1]['felder'].append({'liste': 'unter', 'name': 'Unter', 'eintrag': 'x', 'felder': []})
        self.assertTrue(any('code' in f for f in self.paket(c)))


if __name__ == '__main__':
    unittest.main()
