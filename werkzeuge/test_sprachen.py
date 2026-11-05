"""Tests für Sprachpakete und Beschriftungen je Sprache (Registry #116, #135; Ablago #728, #731).

    python3 -m unittest werkzeuge/test_sprachen.py
"""
import json, shutil, sys, tempfile, unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import katalog  # noqa: E402
import pruefen  # noqa: E402
import sprachen  # noqa: E402
import webseite  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent
SPRACHPAKETE = ('fr', 'nl', 'es', 'it', 'tr', 'pl')
MIT_TYPEN = ('basis', 'haushalt', 'haus', 'fahrzeuge', 'vermietung')


def typ(**feld) -> dict:
    return {'schluessel': 'vertrag', 'name': 'Vertrag', 'beschreibung': '', 'felder': [{'key': 'art', 'label': 'Art', 'typ': 'auswahl', 'optionen': ['Strom', 'Gas'], **feld}],
            'register': [{'key': 'daten', 'name': 'Daten', 'art': 'felder', 'felder': ['art']}]}


class BeschriftungenImPaket(unittest.TestCase):
    """#135: beschriftungen an Typ, Feld, Register und Ansicht."""

    def test_optionen_nur_feste_werte_des_felds(self):
        self.assertEqual(pruefen.pruefe_beschriftungen([typ(beschriftungen={'en': {'label': 'Kind', 'optionen': {'Strom': 'Electricity'}}})], []), [])
        f = pruefen.pruefe_beschriftungen([typ(beschriftungen={'en': {'optionen': {'Wasser': 'Water'}}})], [])
        self.assertTrue(any('„Wasser“, das es unter optionen nicht gibt' in x for x in f), f)

    def test_optionen_nur_bei_auswahlfeldern(self):
        t = typ(beschriftungen={'en': {'optionen': {'Strom': 'Electricity'}}})
        t['felder'][0]['typ'] = 'text'
        self.assertTrue(any('nur bei Auswahlfeldern' in x for x in pruefen.pruefe_beschriftungen([t], [])))

    def test_deutsch_nur_fuer_optionen(self):
        self.assertEqual(pruefen.pruefe_beschriftungen([typ(beschriftungen={'de': {'optionen': {'Strom': 'Strom (Netz)'}}})], []), [])
        f = pruefen.pruefe_beschriftungen([typ(beschriftungen={'de': {'label': 'Sorte'}})], [])
        self.assertTrue(any('beschriftungen.de nur für optionen' in x for x in f), f)
        t = {**typ(), 'beschriftungen': {'de': {'name': 'Kontrakt'}}}
        self.assertTrue(pruefen.pruefe_beschriftungen([t], []))
        self.assertTrue(pruefen.pruefe_beschriftungen([], [{'schluessel': 'x', 'name': 'X', 'beschriftungen': {'de': {'name': 'Y'}}}]))

    def test_schema_kennt_sprachcodes_und_teile(self):
        v = pruefen.inhalt_validator('mappentypen')
        gut = [typ(beschriftungen={'en': {'label': 'Kind'}, 'pt-BR': {'label': 'Tipo'}})]
        self.assertEqual(list(v.iter_errors(gut)), [])
        for falsch in ({'english': {'label': 'Kind'}}, {'en': {'titel': 'Kind'}}, {'en': {'label': '<b>Kind</b>'}}, {'en': {'label': 'x' * 501}}):
            self.assertTrue(list(v.iter_errors([typ(beschriftungen=falsch)])), falsch)
        s = pruefen.inhalt_validator('sichten')
        self.assertEqual(list(s.iter_errors([{'schluessel': 'a', 'name': 'A', 'beschriftungen': {'en': {'name': 'A', 'beschreibung': 'B'}}}])), [])

    def test_mitgelieferte_pakete_haben_englische_beschriftungen(self):
        """#116: Basis, Haushalt, Haus, Fahrzeuge, Vermietung – jeder Typ, jedes Feld, jede Option, jedes Register, jede Ansicht."""
        for pid in MIT_TYPEN:
            o = WURZEL / 'pakete' / pid
            for t in yaml.safe_load((o / 'inhalt/mappentypen.yaml').read_text(encoding='utf-8')):
                self.assertIn('name', t['beschriftungen']['en'], (pid, t['schluessel']))
                for f in t['felder']:
                    en = f['beschriftungen']['en']
                    self.assertTrue(en.get('label'), (pid, f['key']))
                    if f.get('hilfe'):
                        self.assertTrue(en.get('hilfe'), (pid, f['key'], 'hilfe'))
                    self.assertEqual(set(en.get('optionen', {})), set(f.get('optionen') or []), (pid, f['key']))
                for r in t['register']:
                    self.assertTrue(r['beschriftungen']['en']['name'], (pid, r['key']))
            for s in yaml.safe_load((o / 'inhalt/sichten.yaml').read_text(encoding='utf-8')):
                self.assertTrue(s['beschriftungen']['en']['name'], (pid, s['schluessel']))
            self.assertEqual(pruefen.pruefe(o, None), [], pid)


class Sprachpaket(unittest.TestCase):
    """#116 / Ablago #731: Paketart „Sprache“."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.o = Path(self.tmp.name) / 'sprache_fr'
        shutil.copytree(WURZEL / 'pakete' / 'sprache_fr', self.o)

    def tearDown(self):
        self.tmp.cleanup()

    def manifest(self, **aenderung):
        m = yaml.safe_load((self.o / 'manifest.yaml').read_text(encoding='utf-8'))
        for k, v in aenderung.items():
            if v is None:
                m.pop(k, None)
            elif isinstance(v, dict) and isinstance(m.get(k), dict):
                m[k].update(v)
            else:
                m[k] = v
        (self.o / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')

    def fehler(self) -> list[str]:
        return pruefen.pruefe(self.o, None)

    def test_erste_welle_vollstaendig_und_gueltig(self):
        for k in SPRACHPAKETE:
            o = WURZEL / 'pakete' / f'sprache_{k}'
            self.assertEqual(pruefen.pruefe(o, None), [], k)
            m = yaml.safe_load((o / 'manifest.yaml').read_text(encoding='utf-8'))
            self.assertEqual(m['sprache']['kennung'], k)
            self.assertIs(m['sprache']['maschinell'], True, 'erste Welle ist maschinell übersetzt')
            self.assertEqual(m['kuerzel'], k.upper())
            self.assertIn('Maschinell übersetzt – Verbesserungen willkommen', (o / 'README.md').read_text(encoding='utf-8'))
            self.assertTrue((o / 'beschriftungen' / 'basis.yaml').exists())

    def test_gueltig(self):
        self.assertEqual(self.fehler(), [])

    def test_kein_code_kein_inhalt_keine_abhaengigkeiten(self):
        self.manifest(code={'sprache': 'c', 'quelle': 'code/'})
        self.assertTrue(any('keinen Code' in f for f in self.fehler()))
        self.manifest(code=None, inhalt={'mappentypen': 'inhalt/mappentypen.yaml'})
        self.assertTrue(any('inhalt bleibt' in f for f in self.fehler()))
        self.manifest(inhalt={}, abhaengigkeiten={'basis': '>=1.0.0'})
        self.assertTrue(any('hängt von keinem Paket ab' in f for f in self.fehler()))

    def test_nur_erlaubte_dateien(self):
        (self.o / 'code').mkdir()
        (self.o / 'code' / 'x.c').write_text('int main(){}', encoding='utf-8')
        (self.o / 'texte' / 'logo.svg').write_text('<svg/>', encoding='utf-8')
        f = self.fehler()
        self.assertTrue(any(x.startswith('code/x.c: gehört nicht') for x in f), f)
        self.assertTrue(any(x.startswith('texte/logo.svg: gehört nicht') for x in f), f)

    def test_kein_html_keine_steuerzeichen(self):
        d = json.loads((self.o / 'texte/anmeldung.json').read_text(encoding='utf-8'))
        for text, erwartet in (('<a href="https://example.org">ici</a>', 'HTML'), ('<img src=x onerror=alert(1)>', 'HTML'), ('a\u0007b', 'Steuerzeichen'), ('x' * 4001, 'länger als 4000')):
            (self.o / 'texte/anmeldung.json').write_text(json.dumps({**d, 'titel': text}, ensure_ascii=False), encoding='utf-8')
            self.assertTrue(any(erwartet in f for f in self.fehler()), (text[:20], self.fehler()))
        # Spitze Klammern wie im Deutschen (Aufruf der Konsole) sind kein HTML.
        self.assertIsNone(pruefen.pruefe_sprachtext('Usage : dms passwort <email>', 'x'))

    def test_manifest_der_sprache(self):
        self.manifest(dms='>=0.200.0')
        self.assertTrue(any('erst ab 0.203.0' in f for f in self.fehler()))
        self.manifest(dms='>=0.203.0', sprache={'kennung': 'en'})
        self.assertTrue(any('sprache/kennung' in f for f in self.fehler()), self.fehler())
        self.manifest(sprache={'kennung': 'nl'})
        self.assertTrue(any('heißt sprache_nl' in f for f in self.fehler()))
        self.assertTrue(any('kuerzel eines Sprachpakets' in f for f in self.fehler()))
        self.manifest(sprache={'kennung': 'fr', 'geprueft_von': '<script>'})
        self.assertTrue(any('geprueft_von' in f for f in self.fehler()))

    def test_beschriftungen_passen_zum_paket(self):
        b = yaml.safe_load((self.o / 'beschriftungen/basis.yaml').read_text(encoding='utf-8'))
        b['mappentypen']['organisation']['felder']['gibtsnicht'] = {'label': 'X'}
        b['mappentypen']['organisation']['felder']['art']['optionen']['Bäcker'] = 'Boulanger'
        b['sichten']['fehlt'] = {'name': 'X'}
        (self.o / 'beschriftungen/basis.yaml').write_text(yaml.safe_dump(b, allow_unicode=True), encoding='utf-8')
        (self.o / 'beschriftungen/gibtsnicht.yaml').write_text('sichten: {}\n', encoding='utf-8')
        f = self.fehler()
        for teil in ('Feld „gibtsnicht“', 'Option „Bäcker“', 'Ansicht „fehlt“', 'Paket „gibtsnicht“ gibt es in der Registry nicht'):
            self.assertTrue(any(teil in x for x in f), (teil, f))

    def test_erwartung_nennt_die_sprache(self):
        (self.o / 'tests/erwartung.yaml').write_text('mappentypen: []\nsichten: []\nsprache: nl\n', encoding='utf-8')
        self.assertTrue(any('sprache passt nicht' in f for f in self.fehler()))


class GegenAblago(unittest.TestCase):
    """werkzeuge/sprachen.py: gleiche Regeln wie Ablago beim Installieren, Abdeckung."""
    DE = {'a': {'x': 'X {name}', 'y_one': 'Eine', 'y_other': '{anzahl} Stück', 'aufruf': 'dms api <GET|POST>', 'z': 'Z'}}

    def test_regeln(self):
        r = sprachen.vergleiche(self.DE, {'a': {'x': 'x {name}', 'y_few': '{anzahl} sztuki', 'aufruf': 'dms api <GET|POST>', 'z': '<b>z</b>', 'neu': 'n'}, 'b': {'q': 'q'}})
        self.assertEqual(set(r['texte']['a']), {'x', 'y_few', 'aufruf'})
        self.assertTrue(any('„z“: spitze Klammern' in f for f in r['fehler']))
        self.assertTrue(any('„neu“: den Schlüssel gibt es' in h for h in r['hinweise']))
        self.assertTrue(any('texte/b.json' in h for h in r['hinweise']))
        r = sprachen.vergleiche(self.DE, {'a': {'x': 'x {fremd}'}})
        self.assertTrue(any('{fremd}' in h for h in r['hinweise']))
        self.assertEqual(r['fehler'], [])

    def test_abdeckung_abgerundet_mehrzahl_einmal(self):
        self.assertEqual(sprachen.abdeckung(self.DE, {'a': {'x': 'x', 'y_few': 'y'}}), (2, 4, 50))
        self.assertEqual(sprachen.abdeckung(self.DE, {'a': {'x': 'x', 'y_one': 'y', 'aufruf': 'a'}}), (3, 4, 75))

    def test_fehlende_texte_auf_englisch(self):
        z = sprachen.fehlend(self.DE, {'a': {'z': 'Zed'}}, {'a': {'x': 'x', 'y_one': 'y', 'aufruf': 'a'}})
        self.assertEqual(z, ['a.z\tZed'])


class KatalogUndWebseite(unittest.TestCase):
    def test_katalog_nennt_die_sprache(self):
        m = yaml.safe_load((WURZEL / 'pakete/sprache_fr/manifest.yaml').read_text(encoding='utf-8'))
        self.assertEqual(katalog.sprache_von(m), {'kennung': 'fr', 'maschinell': True, 'ablago': '0.203.0'})
        m['sprache']['geprueft_von'] = '@lena-beispiel'
        self.assertEqual(katalog.sprache_von(m)['geprueft_von'], '@lena-beispiel')
        schema = json.loads((WURZEL / 'schema/katalog.schema.json').read_text(encoding='utf-8'))
        from jsonschema import Draft202012Validator
        v = Draft202012Validator({'$schema': schema['$schema'], '$defs': schema['$defs'], **schema['$defs']['paketversion']['properties']['sprache']})
        self.assertEqual(list(v.iter_errors(katalog.sprache_von(m))), [])

    def test_hinweis_maschinell_bzw_geprueft(self):
        p = {'id': 'sprache_fr', 'name': 'Sprache: Französisch', 'versionen': [{'sprache': {'kennung': 'fr', 'maschinell': True, 'ablago': '0.203.0'}}]}
        h = webseite.sprach_hinweis(p)
        self.assertIn('Maschinell übersetzt', h)
        self.assertIn('Verbesserungen willkommen', h)
        self.assertIn(webseite.MITMACHEN_SPRACHE, h)
        self.assertIn('template=uebersetzung.yml', h)
        p['versionen'][0]['sprache'] = {'kennung': 'fr', 'maschinell': False, 'ablago': '0.203.0', 'geprueft_von': '@lena-beispiel'}
        self.assertIn('Geprüft von @lena-beispiel', webseite.sprach_hinweis(p))
        self.assertEqual(webseite.sprach_hinweis({'versionen': [{}]}), '')

    def test_vorlage_uebersetzung_verbessern(self):
        v = yaml.safe_load((WURZEL / '.github/ISSUE_TEMPLATE/uebersetzung.yml').read_text(encoding='utf-8'))
        self.assertIn('Übersetzung verbessern', v['name'])
        self.assertEqual({x.get('id') for x in v['body'] if x.get('id')}, {'sprache', 'stelle', 'jetzt', 'besser', 'dmsversion'})


if __name__ == '__main__':
    unittest.main()
