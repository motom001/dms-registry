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
