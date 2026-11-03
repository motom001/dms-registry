"""Tests für Symbole und Kategorien im Manifest (#98, #80/#84 Stufe 2).

    python3 -m unittest werkzeuge/test_symbole.py
"""
import json, shutil, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import katalog  # noqa: E402
import pruefen  # noqa: E402
import vorlagen  # noqa: E402
import webseite  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent


def probe(tmp: str, **felder) -> Path:
    """Paket aus der Vorlage mit zusätzlichen Manifest-Feldern."""
    ziel = Path(tmp) / 'probe'
    shutil.copytree(WURZEL / 'vorlage', ziel)
    m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
    m['id'] = 'probe'
    m.update(felder)
    (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
    (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
    return ziel


class Liste(unittest.TestCase):
    def test_schema_und_svg_gleich(self):
        self.assertEqual(vorlagen.symbolnamen(), sorted(vorlagen.schema_aufzaehlung('symbol')))

    def test_kategorien_schema_und_yaml_gleich(self):
        self.assertEqual(sorted(k['kennung'] for k in vorlagen.lies_kategorien()['kategorien']), sorted(vorlagen.schema_aufzaehlung('kategorien')))

    def test_svg_von_lucide_und_nur_formen(self):
        for name in vorlagen.symbolnamen():
            text = (vorlagen.SYMBOLE / f'{name}.svg').read_text(encoding='utf-8')
            self.assertIn('@license lucide-static', text, name)
            self.assertTrue(vorlagen.symbol_teile(name), name)
        self.assertIn('ISC License', (vorlagen.SYMBOLE / 'LICENSE').read_text(encoding='utf-8'))

    def test_svg_mit_skript_abgelehnt(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'boese.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><script>alert(1)</script></svg>', encoding='utf-8')
            (Path(tmp) / 'link.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M0 0" onload="x()"/></svg>', encoding='utf-8')
            with mock.patch.object(vorlagen, 'SYMBOLE', Path(tmp)):
                self.assertRaises(ValueError, vorlagen.symbol_teile, 'boese')
                self.assertRaises(ValueError, vorlagen.symbol_teile, 'link')

    def test_alle_pakete_haben_ein_symbol(self):
        daten = vorlagen.lies_kategorien()
        for p in vorlagen.pakete():
            s, k = vorlagen.symbol_von(p['id'], daten, p['manifest'])
            self.assertIn(s, vorlagen.symbolnamen(), p['id'])
            if p['id'].startswith('texterkennung_'):
                self.assertEqual(s, 'languages')
                self.assertRegex(k, r'^[A-Z]{2}$')

    def test_zuordnung_wie_im_issue(self):
        daten = vorlagen.lies_kategorien()
        erwartet = {'basis': 'contact', 'bildformate': 'image', 'fahrzeuge': 'car', 'hallo_post': 'mail', 'haus': 'house', 'haushalt': 'wallet',
                    'ki_aehnlich': 'files', 'ki_assistent': 'message-circle-question-mark', 'office_email': 'file-text',
                    'sicherung_webdav': 'cloud-upload', 'texterkennung': 'scan-text', 'trennblatt': 'scan-barcode', 'vermietung': 'key-round'}
        for pid, s in erwartet.items():
            self.assertEqual(vorlagen.symbol_von(pid, daten)[0], s, pid)
        self.assertEqual(vorlagen.symbol_von('texterkennung_fra', daten), ('languages', 'FR'))
        self.assertEqual(vorlagen.symbol_von('texterkennung_ukr', daten), ('languages', 'UK'))


class ManifestGewinnt(unittest.TestCase):
    DATEN = {'pakete': {'x': ['vorlagen']}, 'symbole': {'x': 'house', 'y': {'symbol': 'languages', 'kuerzel': 'FR'}}}

    def test_symbol(self):
        self.assertEqual(vorlagen.symbol_von('x', self.DATEN), ('house', None))
        self.assertEqual(vorlagen.symbol_von('y', self.DATEN), ('languages', 'FR'))
        self.assertEqual(vorlagen.symbol_von('x', self.DATEN, {'symbol': 'car'}), ('car', None))
        self.assertEqual(vorlagen.symbol_von('z', self.DATEN, {}), (None, None))

    def test_kategorien(self):
        self.assertEqual(vorlagen.kategorien_von('x', self.DATEN), ['vorlagen'])
        self.assertEqual(vorlagen.kategorien_von('x', self.DATEN, {'kategorien': ['ki']}), ['ki'])

    def test_abweichungen(self):
        self.assertEqual(vorlagen.abweichungen('x', {'kategorien': ['vorlagen'], 'symbol': 'house'}, self.DATEN), [])
        h = vorlagen.abweichungen('x', {'kategorien': ['ki'], 'symbol': 'car'}, self.DATEN)
        self.assertEqual(len(h), 2)
        self.assertTrue(all('es gilt das Manifest' in x for x in h))
        self.assertEqual(len(vorlagen.abweichungen('y', {'symbol': 'languages', 'kuerzel': 'ES'}, self.DATEN)), 1)

    def test_kategorie_im_manifest_reicht(self):
        liste = [{'id': 'neu', 'name': 'Neu', 'manifest': {'kategorien': ['ki']}}]
        daten = {**vorlagen.lies_kategorien(), 'pakete': {}, 'symbole': {}}
        self.assertEqual(vorlagen.pruefe_kategorien(daten, liste), [])
        self.assertTrue(any('keine Kategorie' in f for f in vorlagen.pruefe_kategorien(daten, [{'id': 'neu', 'name': 'Neu', 'manifest': {}}])))

    def test_unbekanntes_symbol_in_yaml(self):
        liste = [{'id': 'neu', 'name': 'Neu', 'manifest': {'kategorien': ['ki']}}]
        daten = {**vorlagen.lies_kategorien(), 'pakete': {}, 'symbole': {'neu': 'rakete', 'weg': 'car'}}
        fehler = vorlagen.pruefe_kategorien(daten, liste)
        self.assertTrue(any('unbekanntes Symbol „rakete“' in f for f in fehler))
        self.assertTrue(any('„weg“ ist kein Paket' in f for f in fehler))


class Pruefen(unittest.TestCase):
    def test_gueltig(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(pruefen.pruefe(probe(tmp, symbol='languages', kuerzel='FR', kategorien=['sprachen', 'volltext']), None), [])

    def test_unbekanntes_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(any('symbol' in f for f in pruefen.pruefe(probe(tmp, symbol='rakete'), None)))

    def test_kuerzel_nur_mit_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(any('kuerzel nur zusammen mit symbol' in f for f in pruefen.pruefe(probe(tmp, kuerzel='FR'), None)))
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(any('kuerzel' in f for f in pruefen.pruefe(probe(tmp, symbol='languages', kuerzel='fr'), None)))

    def test_kategorien(self):
        for falsch in (['rakete'], ['ki', 'ki'], ['ki', 'suche', 'post'], []):
            with tempfile.TemporaryDirectory() as tmp:
                self.assertTrue(any('kategorien' in f for f in pruefen.pruefe(probe(tmp, kategorien=falsch), None)), falsch)

    def test_hinweis_ohne_symbol(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = pruefen.hinweise(probe(tmp))
            self.assertEqual(len(h), 1)
            self.assertIn('kein Symbol', h[0])
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(pruefen.hinweise(probe(tmp, symbol='car')), [])

    def test_keine_hinweise_fuer_pakete_der_registry(self):
        for ordner in sorted(p for p in (WURZEL / 'pakete').iterdir() if (p / 'manifest.yaml').exists()):
            self.assertEqual(pruefen.hinweise(ordner), [], ordner.name)


class Katalog(unittest.TestCase):
    def test_symbol_und_kuerzel_im_katalog(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(katalog, 'OHNE_BAU', True):
            self.assertEqual(katalog.baue(Path(tmp), False), [])
            k = json.loads((Path(tmp) / 'katalog.json').read_text(encoding='utf-8'))
            eins = (Path(tmp) / 'katalog.json').read_text(encoding='utf-8')
            # Zweiter Lauf auf denselben Stand: bis auf den Zeitpunkt gleich (deterministisch).
            self.assertEqual(katalog.baue(Path(tmp), False), [])
            zwei = (Path(tmp) / 'katalog.json').read_text(encoding='utf-8')
        nur = lambda s: {**json.loads(s), 'erstellt': None}  # noqa: E731
        self.assertEqual(nur(eins), nur(zwei))
        pakete = {p['id']: p for p in k['pakete']}
        self.assertEqual(pakete['bildformate']['symbol'], 'image')
        self.assertNotIn('kuerzel', pakete['bildformate'])
        self.assertEqual((pakete['texterkennung_spa']['symbol'], pakete['texterkennung_spa']['kuerzel']), ('languages', 'ES'))


class Webseite(unittest.TestCase):
    def test_symbol_eingebettet(self):
        h = webseite.symbol({'name': 'Texterkennung – Französisch', 'symbol': 'languages', 'kuerzel': 'FR'}, 'gross')
        self.assertTrue(h.startswith('<span class="symbol gross bild" aria-hidden="true"><svg '))
        self.assertIn('<span class="kuerzel">FR</span>', h)
        self.assertNotIn('href', h)
        self.assertNotIn('<script', h)

    def test_rueckfall_auf_buchstabe(self):
        self.assertEqual(webseite.symbol({'name': 'haus'}), '<span class="symbol" aria-hidden="true">H</span>')
        self.assertEqual(webseite.symbol({'name': 'Rakete', 'symbol': 'rakete'}, 'klein'), '<span class="symbol klein" aria-hidden="true">R</span>')


if __name__ == '__main__':
    unittest.main()
