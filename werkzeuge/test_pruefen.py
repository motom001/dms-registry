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
    def paket(self, code: dict, dms: str | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['code'] = code
            if dms:
                m['dms'] = dms
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

    def test_verweise_auf_typen_des_dms(self):
        self.assertEqual(self.paket(self.mit(**{'0__6__mappentyp': 'dms:ablageort'})), [])
        self.assertTrue(any('bringt das DMS nicht mit' in f for f in self.paket(self.mit(**{'0__6__mappentyp': 'dms:post'}))))

    def test_rechte_mit_typen_des_dms(self):
        def mit_rechte(lesen: list, schreiben: list | None = None) -> dict:
            import copy
            c = copy.deepcopy(GUELTIG)
            c['rechte'] = {'lesen': lesen, **({'schreiben': schreiben} if schreiben is not None else {})}
            return c
        self.assertEqual(self.paket(mit_rechte(['dms:ablageort', 'dms:rolle'])), [])
        self.assertTrue(any('„dms:brief“ bringt das DMS nicht mit' in f for f in self.paket(mit_rechte(['dms:brief']))))
        self.assertTrue(any('dms:benutzer ist für Pakete nicht erlaubt' in f for f in self.paket(mit_rechte([], ['dms:benutzer']))))
        # dms:post (DMS #435): nur in code.rechte und erst ab DMS 0.94.0.
        post = mit_rechte(['dms:post'], ['dms:post'])
        self.assertTrue(any('erst ab 0.94.0' in f for f in self.paket(post)), 'Vorlage verlangt nur >=0.41.0')
        self.assertEqual(self.paket(post, dms='>=0.94.0'), [])
        self.assertEqual(self.paket(post, dms='^0.95.1'), [])
        self.assertTrue(any('erst ab 0.94.0' in f for f in self.paket(post, dms='>=0.93.9')))

    def test_schnittstelle_vektoren(self):
        # dms:vektoren und volltext.fertig (DMS #442): ab DMS 0.122.0, Vektoren nur mit Recht auf Dokumente.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen', 'schnittstellen': ['dms:vektoren']}
        c['ereignisse'] = ['volltext.fertig']
        self.assertEqual(self.paket(c, dms='>=0.122.0'), [])
        alt = self.paket(c, dms='>=0.121.0')
        self.assertTrue(any('dms:vektoren kennt das DMS erst ab 0.122.0' in f for f in alt), alt)
        self.assertTrue(any('volltext.fertig kennt das DMS erst ab 0.122.0' in f for f in alt), alt)
        c['rechte']['dokumente'] = 'keine'
        self.assertTrue(any('braucht auch code.rechte.dokumente: lesen' in f for f in self.paket(c, dms='>=0.122.0')))
        c['rechte'] = {'dokumente': 'lesen', 'schnittstellen': ['dms:alles']}
        self.assertTrue(any('schnittstellen' in f for f in self.paket(c, dms='>=0.122.0')))

    def test_schnittstelle_antworten(self):
        # dms:antworten und Einstellung adresse (DMS #444): ab DMS 0.124.0; adresse ohne Vorgabe, nur im Abschnitt, höchstens eine.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'schnittstellen': ['dms:antworten']}
        c['einstellungen'][0]['felder'].append({'schluessel': 'dienst', 'name': 'Dienst-Adresse', 'typ': 'adresse', 'pflicht': True, 'beispiel': 'http://ollama:11434/v1'})
        self.assertEqual(self.paket(c, dms='>=0.124.0'), [])
        alt = self.paket(c, dms='>=0.123.0')
        self.assertTrue(any('dms:antworten kennt das DMS erst ab 0.124.0' in f for f in alt), alt)
        self.assertTrue(any('adresse kennt das DMS erst ab 0.124.0' in f for f in alt), alt)
        c['einstellungen'][0]['felder'][-1]['standard'] = 'https://anbieter.example/v1'
        self.assertTrue(any('adresse hat keine Vorgabe' in f for f in self.paket(c, dms='>=0.124.0')))
        del c['einstellungen'][0]['felder'][-1]['standard']
        c['einstellungen'][0]['felder'].append({'schluessel': 'zweite', 'name': 'Zweite', 'typ': 'adresse'})
        self.assertTrue(any('höchstens eine Einstellung vom Typ adresse' in f for f in self.paket(c, dms='>=0.124.0')))
        c['einstellungen'][0]['felder'].pop()
        c['einstellungen'][1]['felder'].append({'schluessel': 'liste_adresse', 'name': 'L', 'typ': 'adresse'})
        self.assertTrue(any('nur in einem Abschnitt' in f for f in self.paket(c, dms='>=0.124.0')))
        c['einstellungen'][1]['felder'].pop()
        c['einstellungen'][0]['felder'][0]['beispiel'] = 'http://x'
        self.assertTrue(any('beispiel gibt es nur bei typ adresse' in f for f in self.paket(c, dms='>=0.124.0')))

    def test_schnittstelle_texterkennung(self):
        # dms:texterkennung (DMS #458): ab DMS 0.133.0, nur mit dokumente: schreiben.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'lesen': ['*'], 'dokumente': 'schreiben', 'schnittstellen': ['dms:texterkennung']}
        c['ereignisse'] = ['volltext.fertig']
        self.assertEqual(self.paket(c, dms='>=0.133.0'), [])
        alt = self.paket(c, dms='>=0.132.0')
        self.assertTrue(any('dms:texterkennung kennt das DMS erst ab 0.133.0' in f for f in alt), alt)
        c['rechte']['dokumente'] = 'lesen'
        self.assertTrue(any('braucht code.rechte.dokumente: schreiben' in f for f in self.paket(c, dms='>=0.133.0')))

    def test_dms_untergrenze(self):
        self.assertEqual(pruefen.dms_untergrenze('>=0.94.0'), (0, 94, 0))
        self.assertEqual(pruefen.dms_untergrenze('>0.93.0 <1.0.0'), (0, 93, 1))
        self.assertEqual(pruefen.dms_untergrenze('0.94.2'), (0, 94, 2))
        self.assertIsNone(pruefen.dms_untergrenze(''))

    def test_mehr_als_zwei_ebenen_geht_nicht(self):
        c = self.mit()
        c['einstellungen'][1]['felder'].append({'liste': 'unter', 'name': 'Unter', 'eintrag': 'x', 'felder': []})
        self.assertTrue(any('code' in f for f in self.paket(c)))


class Inhalt(unittest.TestCase):
    """Verweise in inhalt/ und reservierte Paket-Id (dms:…, #310 im DMS)."""

    def paket(self, ziel_typ: str, paket_id: str = 'probe') -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / paket_id
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = paket_id
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            typen = yaml.safe_load((ziel / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
            typen[0]['felder'].append({'key': 'ort', 'label': 'Ort', 'typ': 'referenz', 'ziel': ziel_typ, 'verweisart': 'bezug'})
            typen[0]['register'][0]['felder'].append('ort')
            (ziel / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump(typen, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_dms_typen_ohne_abhaengigkeit(self):
        self.assertEqual(self.paket('dms:ablageort'), [])
        self.assertEqual(self.paket('dms:benutzer'), [])

    def test_unbekannter_dms_typ(self):
        self.assertTrue(any('bringt das DMS nicht mit' in f for f in self.paket('dms:post')))

    def test_fremdes_paket_weiter_nur_mit_abhaengigkeit(self):
        self.assertTrue(any('nicht unter abhaengigkeiten' in f for f in self.paket('basis:organisation')))

    def test_beispiel_verweise(self):
        f = pruefen.pruefe_beispiel_verweise
        ok = [{'typ': 'vertrag', 'schluessel': 'strom', 'werte': {'nr': 'S'}},
              {'typ': 'zahlung', 'werte': {'vertrag': {'beispiel': 'strom'}, 'partner': {'beispiel': 'basis:stadtwerke'}}}]
        self.assertEqual(f(ok, 'probe', {'basis'}), [])
        self.assertTrue(any('nicht unter abhaengigkeiten' in x for x in f(ok, 'probe', set())))
        self.assertTrue(any('nicht gibt' in x for x in f([{'typ': 'a', 'werte': {'x': {'beispiel': 'fehlt'}}}], 'probe', set())))
        self.assertTrue(any('doppelt' in x for x in f([{'typ': 'a', 'schluessel': 'a', 'werte': {}}, {'typ': 'a', 'schluessel': 'a', 'werte': {}}], 'probe', set())))
        kreis = [{'typ': 'a', 'schluessel': 'a', 'werte': {'x': {'beispiel': 'b'}}}, {'typ': 'a', 'schluessel': 'b', 'werte': {'x': [{'beispiel': 'probe:a'}]}}]
        self.assertTrue(any('Kreis' in x for x in f(kreis, 'probe', set())))

    def test_id_dms_ist_reserviert(self):
        self.assertTrue(any('reserviert' in f for f in self.paket('beispiel', 'dms')))


class Erkennung(unittest.TestCase):
    """Feld-Eigenschaft „für die Erkennung nutzen“ (dms-registry #49, DMS #336/#391)."""

    def paket(self, erkennung_je_feld: dict, dms: str = '>=0.113.0') -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['dms'] = dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            typen = yaml.safe_load((ziel / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
            typen[0]['felder'].append({'key': 'kennwort', 'label': 'Kennwort', 'typ': 'passwort'})
            typen[0]['register'][0]['felder'].append('kennwort')
            for f in typen[0]['felder']:
                if f['key'] in erkennung_je_feld:
                    f['erkennung'] = erkennung_je_feld[f['key']]
            (ziel / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump(typen, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_gueltig(self):
        self.assertEqual(self.paket({'bezeichnung': {}, 'datum': {'art': 'datum'}, 'betrag': {'hinweis': 'Gesamtbetrag unten rechts'}, 'art': {}}), [])
        self.assertEqual(self.paket({'bezeichnung': {'art': 'nummer', 'hinweis': 'Muster 100-####'}}), [])

    def test_nur_geeignete_feldarten(self):
        self.assertTrue(any('nicht bei Feldart „passwort“' in f for f in self.paket({'kennwort': {}})))

    def test_art_passt_zur_feldart(self):
        self.assertTrue(any('passt nicht zur Feldart „datum“' in f for f in self.paket({'datum': {'art': 'iban'}})))
        self.assertTrue(any('erkennung' in f for f in self.paket({'bezeichnung': {'art': 'unbekannt'}})), 'Schema kennt die Art nicht')
        self.assertTrue(any('erkennung' in f for f in self.paket({'bezeichnung': {'hinweis': 'x' * 301}})), 'Hinweis zu lang')
        self.assertTrue(any('erkennung' in f for f in self.paket({'bezeichnung': {'feld': 1}})), 'unbekannte Angabe')

    def test_braucht_dms_0_110(self):
        self.assertTrue(any('erst ab 0.113.0' in f for f in self.paket({'bezeichnung': {}}, dms='>=0.79.0')))
        self.assertEqual(self.paket({}, dms='>=0.79.0'), [], 'ohne erkennung reicht die alte Version')

    def test_pakete_der_registry(self):
        for p in ('basis', 'vermietung', 'fahrzeuge', 'haushalt'):
            self.assertEqual(pruefen.pruefe(WURZEL / 'pakete' / p, None), [], p)


class AusText(unittest.TestCase):
    """Text → Verweis: aus_text an Verweisfeldern (dms-registry #52, DMS #534)."""

    def paket(self, felder: list, dms: str = '>=0.120.0') -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['dms'] = dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            typen = yaml.safe_load((ziel / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
            typen[0]['felder'] += felder
            typen[0]['register'][0]['felder'] += [f['key'] for f in felder]
            (ziel / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump(typen, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    VERWEIS = {'key': 'halter_verweis', 'label': 'Halter', 'typ': 'referenz', 'ziel': 'beispiel', 'verweisart': 'bezug', 'aus_text': 'halter'}

    def test_gueltig(self):
        self.assertEqual(self.paket([self.VERWEIS]), [], 'das alte Textfeld steht nicht mehr im Paket')
        self.assertEqual(self.paket([{'key': 'halter', 'label': 'Halter (Text)', 'typ': 'text'}, self.VERWEIS]), [], 'oder noch als Text')

    def test_nur_an_verweisen(self):
        self.assertTrue(any('aus_text' in f for f in self.paket([{'key': 'x', 'label': 'X', 'typ': 'text', 'aus_text': 'halter'}])))

    def test_quelle_ist_text(self):
        self.assertTrue(any('kein Textfeld' in f for f in self.paket([{**self.VERWEIS, 'aus_text': 'datum'}])))
        self.assertTrue(any('anderes Feld' in f for f in self.paket([{**self.VERWEIS, 'aus_text': 'halter_verweis'}])))
        self.assertTrue(any('aus_text' in f for f in self.paket([{**self.VERWEIS, 'aus_text': 'Halter Text'}])), 'Schema: nur Kennungen')

    def test_keine_pflicht(self):
        self.assertTrue(any('keine Pflicht' in f for f in self.paket([{**self.VERWEIS, 'pflicht': True}])))

    def test_braucht_dms_0_120(self):
        self.assertTrue(any('erst ab 0.120.0' in f for f in self.paket([self.VERWEIS], dms='>=0.113.0')))


class Formate(unittest.TestCase):
    """Feldformate und Datumsgrenzen (dms-registry #55, DMS #535)."""

    def paket(self, je_feld: dict, dms: str = '>=0.121.0', felder: list | None = None, beispiele: list | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['dms'] = dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            typen = yaml.safe_load((ziel / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
            for f in felder or []:
                typen[0]['felder'].append(f)
                typen[0]['register'][0]['felder'].append(f['key'])
            for f in typen[0]['felder']:
                f.update(je_feld.get(f['key'], {}))
            (ziel / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump(typen, allow_unicode=True), encoding='utf-8')
            if beispiele is not None:
                (ziel / 'inhalt' / 'beispiele.yaml').write_text(yaml.safe_dump(beispiele, allow_unicode=True), encoding='utf-8')
                m['inhalt']['beispiele'] = 'inhalt/beispiele.yaml'
                (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
                erw = yaml.safe_load((ziel / 'tests' / 'erwartung.yaml').read_text(encoding='utf-8')) or {}
                erw['beispiele'] = len(beispiele)
                (ziel / 'tests' / 'erwartung.yaml').write_text(yaml.safe_dump(erw, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    ADRESSE = [{'key': 'telefon', 'label': 'Telefon', 'typ': 'text'}, {'key': 'plz', 'label': 'PLZ', 'typ': 'text', 'maxLen': 10},
               {'key': 'land', 'label': 'Land', 'typ': 'text', 'standard': 'Deutschland'}]

    def test_gueltig(self):
        self.assertEqual(self.paket({'telefon': {'format': 'telefon'}, 'plz': {'format': 'plz', 'landFeld': 'land'}, 'datum': {'max': '2099-12-31'}}, felder=self.ADRESSE), [])
        self.assertEqual(self.paket({'datum': {'min': '2000-01-01', 'max': '2030-12-31'}}), [])

    def test_format_nur_bei_text(self):
        self.assertTrue(any('nur bei Feldart „text“' in f for f in self.paket({'datum': {'format': 'email'}})))
        self.assertTrue(any('format' in f for f in self.paket({'bezeichnung': {'format': 'fax'}})), 'Schema kennt das Format nicht')

    def test_landfeld(self):
        self.assertTrue(any('nur bei format: plz' in f for f in self.paket({'telefon': {'format': 'telefon', 'landFeld': 'land'}}, felder=self.ADRESSE)))
        self.assertTrue(any('kein Text- oder Auswahlfeld' in f for f in self.paket({'plz': {'format': 'plz', 'landFeld': 'gibtsnicht'}}, felder=self.ADRESSE)))

    def test_datumsgrenzen(self):
        self.assertTrue(any('min' in f for f in self.paket({'datum': {'min': 'gestern'}})))
        self.assertTrue(any('min liegt nach max' in f for f in self.paket({'datum': {'min': '2030-01-01', 'max': '2020-01-01'}})))

    def test_braucht_dms_0_121(self):
        self.assertTrue(any('erst ab 0.121.0' in f for f in self.paket({'datum': {'max': 'heute'}}, dms='>=0.113.0')))

    def test_beispiele_passen(self):
        je = {'telefon': {'format': 'telefon'}, 'plz': {'format': 'plz', 'landFeld': 'land'}, 'datum': {'max': 'heute'}}
        gut = [{'typ': 'beispiel', 'werte': {'bezeichnung': 'Lena', 'telefon': '+49 30 123456', 'plz': '01357', 'datum': '2020-01-01'}},
               {'typ': 'beispiel', 'werte': {'bezeichnung': 'Jonas', 'plz': '1010', 'land': 'Österreich'}}]
        self.assertEqual(self.paket(je, felder=self.ADRESSE, beispiele=gut), [])
        schlecht = [{'typ': 'beispiel', 'werte': {'bezeichnung': 'Markus', 'telefon': '030 abc', 'plz': '01357asda', 'datum': '2999-01-01'}}]
        f = '\n'.join(self.paket(je, felder=self.ADRESSE, beispiele=schlecht))
        self.assertIn('Telefonnummer', f)
        self.assertIn('deutsche PLZ', f)
        self.assertIn('liegt nach heute', f)

    def test_iban(self):
        self.assertTrue(pruefen.iban_ok('DE89 3704 0044 0532 0130 00'))
        self.assertFalse(pruefen.iban_ok('DE88 3704 0044 0532 0130 00'))
        self.assertFalse(pruefen.iban_ok('DE89 3704 0044 0532 0130 0'))

    def test_pakete_der_registry(self):
        for p in ('basis', 'haus', 'vermietung', 'fahrzeuge', 'haushalt'):
            self.assertEqual(pruefen.pruefe(WURZEL / 'pakete' / p, None), [], p)


class Wortlisten(unittest.TestCase):
    """inhalt.wortlisten (DMS #356): gleichbedeutende Wörter für die Suche, ab DMS 0.127.0."""

    def paket(self, gruppen, dms: str = '>=0.127.0', erwartung: int | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['dms'] = dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            m['inhalt']['wortlisten'] = 'inhalt/wortlisten.yaml'
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'inhalt' / 'wortlisten.yaml').write_text(yaml.safe_dump(gruppen, allow_unicode=True), encoding='utf-8')
            erw = yaml.safe_load((ziel / 'tests' / 'erwartung.yaml').read_text(encoding='utf-8')) or {}
            erw['wortlisten'] = len(gruppen) if erwartung is None else erwartung
            (ziel / 'tests' / 'erwartung.yaml').write_text(yaml.safe_dump(erw, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_gueltig(self):
        self.assertEqual(self.paket([{'woerter': ['Kfz', 'Auto', 'PKW']}, {'woerter': ['Nebenkosten', 'Betriebskosten']}]), [])

    def test_schema(self):
        self.assertTrue(any('wortlisten.yaml' in f for f in self.paket([{'woerter': ['Kfz']}])))
        self.assertTrue(any('wortlisten.yaml' in f for f in self.paket([{'woerter': ['Kfz', 'Auto'], 'art': 'x'}])))
        self.assertTrue(any('wortlisten.yaml' in f for f in self.paket([{'woerter': ['Kfz', 'A']}])))

    def test_doppelte_woerter_gefaltet(self):
        self.assertTrue(any('doppelt' in f for f in self.paket([{'woerter': ['Gebühr', 'gebuhr', 'Abgabe']}])))

    def test_dms_version(self):
        self.assertTrue(any('0.127.0' in f for f in self.paket([{'woerter': ['Kfz', 'Auto']}], dms='>=0.79.0')))

    def test_erwartung(self):
        self.assertTrue(any('Anzahl wortlisten' in f for f in self.paket([{'woerter': ['Kfz', 'Auto']}], erwartung=2)))

    def test_kein_wort_in_zwei_paketen(self):
        """Allgemeine Wörter stehen in Basis, fachliche im Fachpaket – keines doppelt im Katalog (DMS #356)."""
        gesehen: dict[str, str] = {}
        for m_pfad in sorted((WURZEL / 'pakete').glob('*/manifest.yaml')):
            datei = (yaml.safe_load(m_pfad.read_text(encoding='utf-8')).get('inhalt') or {}).get('wortlisten')
            if not datei:
                continue
            paket = m_pfad.parent.name
            for g in yaml.safe_load((m_pfad.parent / datei).read_text(encoding='utf-8')) or []:
                for w in g['woerter']:
                    k = pruefen.falte(w)
                    self.assertIn(gesehen.setdefault(k, paket), (paket,), f'„{w}“ steht in {gesehen[k]} und {paket}')
        self.assertIn(pruefen.falte('Rechnung'), gesehen)


if __name__ == '__main__':
    unittest.main()


def _leb(n: int) -> bytes:
    b = bytearray()
    while True:
        x = n & 0x7f; n >>= 7
        b.append(x | (0x80 if n else 0))
        if not n:
            return bytes(b)


def _name(t: str) -> bytes:
    return _leb(len(t.encode())) + t.encode()


def _modul(importe, exporte) -> bytes:
    """Kleines Modul nur mit Import- und Exportabschnitt (für wasm.pruefe)."""
    imp = _leb(len(importe))
    for modul, name, art in importe:
        imp += _name(modul) + _name(name) + {'function': b'\x00\x00', 'memory': b'\x02\x00\x01'}[art]
    exp = _leb(len(exporte))
    for name in exporte:
        exp += _name(name) + b'\x00\x00'
    return b'\0asm\x01\0\0\0' + b'\x02' + _leb(len(imp)) + imp + b'\x07' + _leb(len(exp)) + exp


class Modul(unittest.TestCase):
    def test_abi(self):
        import wasm
        gut = _modul([('env', 'memory', 'memory'), ('dms', 'log', 'function'), ('wasi_snapshot_preview1', 'fd_write', 'function')], ['dms_puffer', 'dms_ereignis'])
        self.assertEqual(wasm.pruefe(gut), [])
        self.assertTrue(any('unbekannte Importe env.system' in f for f in wasm.pruefe(_modul([('env', 'memory', 'memory'), ('env', 'system', 'function')], ['dms_puffer', 'dms_ereignis']))))
        self.assertTrue(any('importiert keinen Speicher' in f for f in wasm.pruefe(_modul([('dms', 'log', 'function')], ['dms_puffer', 'dms_ereignis']))))
        self.assertTrue(any('dms_ereignis fehlt' in f for f in wasm.pruefe(_modul([('env', 'memory', 'memory')], ['dms_puffer']))))
        # netz_strom, netz_weiter, teil (DMS #444) sind bekannt; welche das Modul nutzt, liefert dms_importe.
        neu = _modul([('env', 'memory', 'memory'), ('dms', 'netz_strom', 'function'), ('dms', 'teil', 'function')], ['dms_puffer', 'dms_ereignis'])
        self.assertEqual(wasm.pruefe(neu), [])
        self.assertEqual(wasm.dms_importe(neu), {'netz_strom', 'teil'})
        self.assertTrue(any('kein WebAssembly' in f for f in wasm.pruefe(b'kein wasm')))

    def test_bauen_sh_pflicht(self):
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['code'] = {'sprache': 'c', 'quelle': 'code/', 'rechte': {}}
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'code' / 'a.c').write_text('int x;\n', encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            self.assertEqual(pruefen.pruefe(ziel, None), [])
            (ziel / 'code' / 'bauen.sh').unlink()
            self.assertTrue(any('bauen.sh fehlt' in f for f in pruefen.pruefe(ziel, None)))
            (ziel / 'code' / 'modul.wasm').write_bytes(b'kein wasm')
            self.assertTrue(any('kein WebAssembly' in f for f in pruefen.pruefe(ziel, None)))

    def test_code_groessengrenze(self):
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['code'] = {'sprache': 'c', 'quelle': 'code/', 'rechte': {}}
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'code' / 'a.c').write_text('int x;\n', encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            (ziel / 'code' / 'daten').mkdir()
            with open(ziel / 'code' / 'daten' / 'gross.bin', 'wb') as f:
                f.truncate(pruefen.CODE_MAX + 1)
            self.assertTrue(any('höchstens 32 MB' in f for f in pruefen.pruefe(ziel, None)))
