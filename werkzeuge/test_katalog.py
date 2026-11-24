"""Tests für werkzeuge/katalog.py: Empfehlungsliste und passtZu (#198)."""
import sys
import unittest

import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import katalog  # noqa: E402


class Empfohlen(unittest.TestCase):
    def test_reihenfolge_und_nur_vorhandene(self):
        pakete = {'haushalt': {}, 'basis': {}, 'vertraege': {}}
        e = katalog.empfehlungen(pakete)
        self.assertEqual(e, [x for x in e if x in pakete])
        self.assertEqual(e[:2], ['basis', 'haushalt'])  # Reihenfolge wie in empfohlen.yaml

    def test_leer_ohne_treffer(self):
        self.assertEqual(katalog.empfehlungen({'gibtsnicht': {}}), [])


class PasstZu(unittest.TestCase):
    def test_aus_manifest(self):
        pakete = {'compliance': {'id': 'compliance'}, 'basis': {'id': 'basis', 'passtZu': ['beruflich']}}
        manifeste = {'compliance': {'passtZu': ['beruflich']}, 'basis': {}}
        self.assertEqual(katalog.herausgeber_und_umzug(pakete, manifeste), [])
        self.assertEqual(pakete['compliance']['passtZu'], ['beruflich'])
        self.assertNotIn('passtZu', pakete['basis'])  # neue Version ohne passtZu passt wieder für alle

    def test_ohne_paketordner_bleibt_es(self):
        pakete = {'alt': {'id': 'alt', 'passtZu': ['beruflich']}}
        katalog.herausgeber_und_umzug(pakete, {})
        self.assertEqual(pakete['alt']['passtZu'], ['beruflich'])



class Stufe(unittest.TestCase):
    """Stufe für „Was Ablago darf“ wie paketStufe in Ablago (Registry #234, motom001/dms#1562)."""

    def test_stufen(self):
        self.assertEqual(katalog.paket_stufe({}), 'vorlagen')
        self.assertEqual(katalog.paket_stufe({'code': {'netz': []}}), 'lokal')
        self.assertEqual(katalog.paket_stufe({'code': {'netz': ['https://api.example.org']}}), 'netz')
        dienst = {'einstellungen': [{'abschnitt': 'A', 'felder': [{'schluessel': 'url', 'typ': 'adresse'}]}]}
        self.assertEqual(katalog.paket_stufe({'code': {'netz': [], **dienst}}), 'netz')

    def test_offizielle_pakete(self):
        # Nur KI-Assistent und Sicherung (WebDAV) nutzen das Internet; alle anderen Helfer arbeiten nur hier.
        manifeste = {d.name: yaml.safe_load((d / 'manifest.yaml').read_text(encoding='utf-8'))
                     for d in (katalog.WURZEL / 'pakete').iterdir() if (d / 'manifest.yaml').exists()}
        self.assertEqual(sorted(k for k, m in manifeste.items() if katalog.paket_stufe(m) == 'netz'), ['ki_assistent', 'sicherung_webdav'])


if __name__ == '__main__':
    unittest.main()


class Zurueckgezogen(unittest.TestCase):
    """Zurückgezogene Versionen (werkzeuge/zurueckgezogen.yaml) fallen aus dem bisherigen Katalog, ein Paket ohne
    Versionen ganz (Rechnungen, #208)."""

    def test_versionen_und_paket_fallen_weg(self):
        pakete = {'alt': {'id': 'alt', 'versionen': [{'version': '1.1.0'}, {'version': '1.0.0'}]},
                  'teil': {'id': 'teil', 'versionen': [{'version': '2.0.0'}, {'version': '1.0.0'}]},
                  'bleibt': {'id': 'bleibt', 'versionen': [{'version': '1.0.0'}]}}
        raus = katalog.ohne_zurueckgezogene(pakete, {'alt-v1.1.0', 'alt-v1.0.0', 'teil-v1.0.0'})
        self.assertEqual(sorted(pakete), ['bleibt', 'teil'])
        self.assertEqual([v['version'] for v in pakete['teil']['versionen']], ['2.0.0'])
        self.assertEqual(sorted(raus), [('alt', '1.0.0'), ('alt', '1.1.0'), ('teil', '1.0.0')])

    def test_liste_im_repository(self):
        self.assertIn('rechnungen-v1.3.0', katalog.zurueckgezogen())
