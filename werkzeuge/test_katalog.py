"""Tests für werkzeuge/katalog.py: Empfehlungsliste und passtZu (#198)."""
import sys
import unittest
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


if __name__ == '__main__':
    unittest.main()
