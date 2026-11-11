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

    def test_mehrfach_und_ausschluss(self):
        # DMS #658: mehrfach nur bei Verweisen, schliesst_aus auf ein Feld desselben Verweistyps, ab 0.179.0.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['einstellungen'][0]['felder'] += [
            {'schluessel': 'nur', 'name': 'Nur diese', 'typ': 'benutzer', 'mehrfach': True, 'schliesst_aus': 'ohne'},
            {'schluessel': 'ohne', 'name': 'Ohne diese', 'typ': 'benutzer', 'mehrfach': True, 'schliesst_aus': 'nur'},
        ]
        self.assertEqual(self.paket(c, dms='>=0.179.0'), [])
        self.assertTrue(any('erst ab 0.179.0' in f for f in self.paket(c, dms='>=0.178.0')))
        falsch = copy.deepcopy(c)
        falsch['einstellungen'][0]['felder'][-1]['typ'] = 'rolle'
        self.assertTrue(any('schliesst_aus „ohne“ muss ein anderes Feld' in f for f in self.paket(falsch, dms='>=0.179.0')))
        falsch = copy.deepcopy(c)
        falsch['einstellungen'][0]['felder'][0]['mehrfach'] = True
        self.assertTrue(any('mehrfach: true gibt es nur bei' in f for f in self.paket(falsch, dms='>=0.179.0')))

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

    def test_schnittstelle_erkennen(self):
        # dms:erkennen (DMS #511): ab DMS 0.125.0, ohne weitere Rechte.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'schnittstellen': ['dms:erkennen']}
        self.assertEqual(self.paket(c, dms='>=0.125.0'), [])
        alt = self.paket(c, dms='>=0.124.0')
        self.assertTrue(any('dms:erkennen kennt das DMS erst ab 0.125.0' in f for f in alt), alt)

    def test_schnittstelle_klassifizieren(self):
        # dms:klassifizieren (DMS #939): ab DMS 0.226.0, ohne weitere Rechte.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'schnittstellen': ['dms:klassifizieren']}
        self.assertEqual(self.paket(c, dms='>=0.226.0'), [])
        alt = self.paket(c, dms='>=0.225.0')
        self.assertTrue(any('dms:klassifizieren kennt das DMS erst ab 0.226.0' in f for f in alt), alt)

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

    def test_schnittstelle_umwandeln(self):
        # dms:umwandeln (DMS #577): ab DMS 0.137.0, nur mit code.umwandeln, dem Ereignis datei.umwandeln und Lesen.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen', 'schnittstellen': ['dms:umwandeln']}
        c['ereignisse'] = ['datei.umwandeln']
        c['umwandeln'] = ['image/tiff', 'image/webp']
        self.assertEqual(self.paket(c, dms='>=0.137.0'), [])
        alt = self.paket(c, dms='>=0.136.0')
        self.assertTrue(any('dms:umwandeln kennt das DMS erst ab 0.137.0' in f for f in alt), alt)
        ohne = copy.deepcopy(c)
        del ohne['umwandeln']
        self.assertTrue(any('braucht code.umwandeln' in f for f in self.paket(ohne, dms='>=0.137.0')))
        ohne = copy.deepcopy(c)
        ohne['ereignisse'] = []
        self.assertTrue(any('braucht das Ereignis datei.umwandeln' in f for f in self.paket(ohne, dms='>=0.137.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte']['dokumente'] = 'keine'
        self.assertTrue(any('dms:umwandeln braucht auch code.rechte.dokumente: lesen' in f for f in self.paket(ohne, dms='>=0.137.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen'}
        self.assertTrue(any('code.umwandeln: braucht' in f for f in self.paket(ohne, dms='>=0.137.0')))
        # PDF, JPEG und PNG liest das DMS selbst (Schema).
        kern = copy.deepcopy(c)
        kern['umwandeln'] = ['image/png']
        self.assertTrue(self.paket(kern, dms='>=0.137.0'))
        kern['umwandeln'] = ['TIFF']
        self.assertTrue(self.paket(kern, dms='>=0.137.0'))

    def test_schnittstelle_volltext(self):
        # dms:volltext (DMS #614): ab DMS 0.145.0, nur mit code.volltext, dem Ereignis datei.volltext und Lesen.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen', 'schnittstellen': ['dms:volltext']}
        c['ereignisse'] = ['datei.volltext']
        c['volltext'] = ['message/rfc822', 'text/plain', 'application/octet-stream']
        self.assertEqual(self.paket(c, dms='>=0.145.0'), [])
        alt = self.paket(c, dms='>=0.144.2')
        self.assertTrue(any('dms:volltext kennt das DMS erst ab 0.145.0' in f for f in alt), alt)
        ohne = copy.deepcopy(c)
        del ohne['volltext']
        self.assertTrue(any('braucht code.volltext' in f for f in self.paket(ohne, dms='>=0.145.0')))
        ohne = copy.deepcopy(c)
        ohne['ereignisse'] = []
        self.assertTrue(any('braucht das Ereignis datei.volltext' in f for f in self.paket(ohne, dms='>=0.145.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte']['dokumente'] = 'keine'
        self.assertTrue(any('dms:volltext braucht auch code.rechte.dokumente: lesen' in f for f in self.paket(ohne, dms='>=0.145.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen'}
        self.assertTrue(any('code.volltext: braucht' in f for f in self.paket(ohne, dms='>=0.145.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen'}
        del ohne['volltext']
        self.assertTrue(any('datei.volltext gibt es nur mit' in f for f in self.paket(ohne, dms='>=0.145.0')))
        # PDF, JPEG und PNG liest das DMS selbst (Schema); höchstens 40 Dateitypen.
        kern = copy.deepcopy(c)
        kern['volltext'] = ['application/pdf']
        self.assertTrue(self.paket(kern, dms='>=0.145.0'))
        kern['volltext'] = ['Word']
        self.assertTrue(self.paket(kern, dms='>=0.145.0'))
        kern['volltext'] = [f'application/x-{i}' for i in range(41)]
        self.assertTrue(self.paket(kern, dms='>=0.145.0'))

    def test_schnittstelle_archivfassung(self):
        # dms:archivfassung (DMS #631): ab DMS 0.149.0, nur mit code.archivfassung.typen, dem Ereignis datei.archivfassung
        # und Lesen; PDF, JPEG und PNG erlaubt; auswahl (DMS #660, ab 0.176.0) nennt je Art eine Ja/Nein-Einstellung.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen', 'schnittstellen': ['dms:archivfassung']}
        c['ereignisse'] = ['datei.archivfassung']
        c['archivfassung'] = {'typen': ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']}
        self.assertEqual(self.paket(c, dms='>=0.149.0'), [])
        alt = self.paket(c, dms='>=0.148.1')
        self.assertTrue(any('dms:archivfassung kennt das DMS erst ab 0.149.0' in f for f in alt), alt)
        ohne = copy.deepcopy(c)
        del ohne['archivfassung']
        self.assertTrue(any('braucht code.archivfassung.typen' in f for f in self.paket(ohne, dms='>=0.149.0')))
        ohne = copy.deepcopy(c)
        ohne['ereignisse'] = []
        self.assertTrue(any('braucht das Ereignis datei.archivfassung' in f for f in self.paket(ohne, dms='>=0.149.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte']['dokumente'] = 'keine'
        self.assertTrue(any('dms:archivfassung braucht auch code.rechte.dokumente: lesen' in f for f in self.paket(ohne, dms='>=0.149.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen'}
        self.assertTrue(any('code.archivfassung: braucht' in f for f in self.paket(ohne, dms='>=0.149.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte'] = {'lesen': ['*'], 'dokumente': 'lesen'}
        del ohne['archivfassung']
        self.assertTrue(any('datei.archivfassung gibt es nur mit' in f for f in self.paket(ohne, dms='>=0.149.0')))
        # auswahl: gültig ab 0.176.0; unbekannter Schlüssel, falscher Typ, unbekannte Art; nur_scans gibt es nicht mehr.
        mit = copy.deepcopy(c)
        mit['archivfassung']['auswahl'] = {'pdf_text': 'pdf_text', 'pdf_scan': 'pdf_scan', 'bilder': 'bilder'}
        mit['einstellungen'] = [{'abschnitt': 'Archivfassung', 'felder': [
            {'schluessel': k, 'name': n, 'typ': 'janein', 'standard': True}
            for k, n in (('pdf_text', 'PDFs mit Text'), ('pdf_scan', 'Gescannte PDFs'), ('bilder', 'Fotos und Bilder'))]}]
        self.assertEqual(self.paket(mit, dms='>=0.176.0'), [])
        alt = self.paket(mit, dms='>=0.175.0')
        self.assertTrue(any('auswahl kennt das DMS erst ab 0.176.0' in f for f in alt), alt)
        falsch = copy.deepcopy(mit)
        falsch['archivfassung']['auswahl']['bilder'] = 'gibtsnicht'
        self.assertTrue(any('auswahl.bilder: der Schlüssel einer Einstellung vom Typ janein' in f for f in self.paket(falsch, dms='>=0.176.0')))
        falsch = copy.deepcopy(mit)
        falsch['einstellungen'][0]['felder'][0]['typ'] = 'text'
        del falsch['einstellungen'][0]['felder'][0]['standard']
        self.assertTrue(any('auswahl.pdf_text: der Schlüssel einer Einstellung vom Typ janein' in f for f in self.paket(falsch, dms='>=0.176.0')))
        falsch = copy.deepcopy(mit)
        falsch['archivfassung']['auswahl']['alles'] = 'pdf_text'
        self.assertTrue(self.paket(falsch, dms='>=0.176.0'))
        falsch = copy.deepcopy(mit)
        falsch['archivfassung']['nur_scans'] = 'pdf_text'
        self.assertTrue(self.paket(falsch, dms='>=0.176.0'))
        # emails (DMS #946, dms-registry #143): erst ab der Version mit der Art emails.
        mail = copy.deepcopy(mit)
        mail['archivfassung']['typen'] += ['message/rfc822', 'application/vnd.ms-outlook']
        mail['archivfassung']['auswahl']['emails'] = 'emails'
        mail['einstellungen'][0]['felder'].append({'schluessel': 'emails', 'name': 'E-Mails', 'typ': 'janein', 'standard': True})
        v = '.'.join(map(str, pruefen.DMS_ARCHIV_EMAILS_AB))
        self.assertEqual(self.paket(mail, dms=f'>={v}'), [])
        alt = self.paket(mail, dms='>=0.176.0')
        self.assertTrue(any('auswahl.emails kennt das DMS erst ab' in f for f in alt), alt)
        # Schema: unbekannte Angaben, keine Dateitypen, Dateitypen in Kurzform.
        kern = copy.deepcopy(c)
        kern['archivfassung']['stufe'] = 'B'
        self.assertTrue(self.paket(kern, dms='>=0.149.0'))
        kern = copy.deepcopy(c)
        kern['archivfassung']['typen'] = []
        self.assertTrue(self.paket(kern, dms='>=0.149.0'))
        kern['archivfassung']['typen'] = ['PDF']
        self.assertTrue(self.paket(kern, dms='>=0.149.0'))

    def test_schnittstelle_sicherung(self):
        # dms:sicherung-lesen (DMS #585): ab DMS 0.142.0, nur zusammen mit dem Ereignis sicherung.fertig; keine Mappen nötig.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'schnittstellen': ['dms:sicherung-lesen']}
        c['ereignisse'] = ['sicherung.fertig']
        self.assertEqual(self.paket(c, dms='>=0.142.0'), [])
        alt = self.paket(c, dms='>=0.141.0')
        self.assertTrue(any('dms:sicherung-lesen kennt das DMS erst ab 0.142.0' in f for f in alt), alt)
        ohne = copy.deepcopy(c)
        ohne['ereignisse'] = []
        self.assertTrue(any('braucht das Ereignis sicherung.fertig' in f for f in self.paket(ohne, dms='>=0.142.0')))
        ohne = copy.deepcopy(c)
        ohne['rechte'] = {}
        self.assertTrue(any('sicherung.fertig gibt es nur mit' in f for f in self.paket(ohne, dms='>=0.142.0')))

    def test_mappen_ereignisse(self):
        # Ereignisse zu Mappen (DMS #670): ab 0.153.0, nur mit code.mappentypen (eigene, lesbare Typen) und umgekehrt.
        import copy
        c = copy.deepcopy(GUELTIG)
        c['rechte'] = {'lesen': ['beispiel']}
        c['ereignisse'] = ['mappe.geaendert', 'frist.erreicht']
        c['mappentypen'] = ['beispiel']
        self.assertEqual(self.paket(c, dms='>=0.153.0'), [])
        self.assertTrue(any('erst ab 0.153.0' in f for f in self.paket(c, dms='>=0.152.0')))
        ohne = copy.deepcopy(c); del ohne['mappentypen']
        self.assertTrue(any('braucht code.mappentypen' in f for f in self.paket(ohne, dms='>=0.153.0')))
        nur = copy.deepcopy(c); nur['ereignisse'] = ['post.angelegt']
        self.assertTrue(any('nur mit Mappen-Ereignissen' in f for f in self.paket(nur, dms='>=0.153.0')))
        fremd = copy.deepcopy(c); fremd['mappentypen'] = ['gibtsnicht']
        self.assertTrue(any('gibt es in diesem Paket nicht' in f for f in self.paket(fremd, dms='>=0.153.0')))
        blind = copy.deepcopy(c); blind['rechte'] = {'lesen': ['dms:post']}
        self.assertTrue(any('auch lesen dürfen' in f for f in self.paket(blind, dms='>=0.153.0')))
        # Fremde Mappentypen und „*“ (DMS #686): lesbar und ab 0.166.0.
        andere = copy.deepcopy(c); andere['mappentypen'] = ['basis:organisation', 'dms:post']; andere['rechte'] = {'lesen': ['basis:organisation', 'dms:post']}
        self.assertEqual(self.paket(andere, dms='>=0.166.0'), [])
        self.assertTrue(any('erst ab 0.166.0' in f for f in self.paket(andere, dms='>=0.153.0')))
        alle = copy.deepcopy(c); alle['mappentypen'] = ['*']; alle['rechte'] = {'lesen': ['*']}
        self.assertEqual(self.paket(alle, dms='>=0.166.0'), [])
        halb = copy.deepcopy(alle); halb['rechte'] = {'lesen': ['beispiel']}
        self.assertTrue(any('geht nur mit code.rechte.lesen' in f for f in self.paket(halb, dms='>=0.166.0')))
        nichtlesbar = copy.deepcopy(andere); nichtlesbar['rechte'] = {'lesen': ['dms:post']}
        self.assertTrue(any('auch lesen dürfen' in f for f in self.paket(nichtlesbar, dms='>=0.166.0')))
        benutzer = copy.deepcopy(c); benutzer['mappentypen'] = ['dms:benutzer']
        self.assertTrue(any('Pakete sehen keine Benutzer' in f for f in self.paket(benutzer, dms='>=0.166.0')))

    def test_dms_untergrenze(self):
        self.assertEqual(pruefen.dms_untergrenze('>=0.94.0'), (0, 94, 0))
        self.assertEqual(pruefen.dms_untergrenze('>0.93.0 <1.0.0'), (0, 93, 1))
        self.assertEqual(pruefen.dms_untergrenze('0.94.2'), (0, 94, 2))
        self.assertIsNone(pruefen.dms_untergrenze(''))

    def test_mehr_als_zwei_ebenen_geht_nicht(self):
        c = self.mit()
        c['einstellungen'][1]['felder'].append({'liste': 'unter', 'name': 'Unter', 'eintrag': 'x', 'felder': []})
        self.assertTrue(any('code' in f for f in self.paket(c)))


class DmsVersion(unittest.TestCase):
    """Nötige DMS-Version und Lizenz (motom001/dms#651): Schreibweise; in den Katalog nur freie Lizenzen der Positivliste."""

    def manifest(self, **werte) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m.update(werte)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_schreibweise(self):
        self.assertTrue(any('dms' in f for f in self.manifest(dms='ab 0.121')))
        self.assertTrue(any('dms' in f for f in self.manifest(dms='>=0.121')))

    def test_gueltige_angabe(self):
        self.assertEqual([f for f in self.manifest(dms='>=0.121.0') if 'dms' in f], [])

    def test_nur_freie_lizenz(self):
        for lizenz in ('LicenseRef-Kommerzielle-Lizenz', 'NONE'):
            self.assertTrue(any('lizenz' in f for f in self.manifest(lizenz=lizenz)), lizenz)


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

    def test_dms_ablageort_veraltet(self):
        # DMS #883, Registry #138: dms:ablageort ist ein Alias für basis:ablageort – Warnung (Hinweis), kein Fehler.
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            typen = yaml.safe_load((ziel / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
            typen[0]['felder'].append({'key': 'ort', 'label': 'Ort', 'typ': 'referenz', 'ziel': 'dms:ablageort'})
            (ziel / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump(typen, allow_unicode=True), encoding='utf-8')
            h = pruefen.veraltete_verweise(ziel)
            self.assertEqual(len(h), 1, h)
            self.assertIn('inhalt/mappentypen.yaml', h[0])
            self.assertIn('„dms:ablageort“ ist veraltet', h[0])
            self.assertIn('basis:ablageort', h[0])
            self.assertIn(h[0], pruefen.hinweise(ziel))
            # Auch in code.rechte.
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['code'] = {'rechte': {'lesen': ['dms:ablageort']}}
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            self.assertTrue(any(x.startswith('inhalt/mappentypen.yaml, manifest.yaml:') for x in pruefen.veraltete_verweise(ziel)))

    def test_registry_ohne_dms_ablageort(self):
        # Basis bringt den Ablageort (1.6.0); kein Paket der Registry verweist mehr auf dms:ablageort.
        for o in sorted((WURZEL / 'pakete').iterdir()):
            if o.is_dir():
                self.assertEqual(pruefen.veraltete_verweise(o), [], o.name)
        self.assertEqual(pruefen.veraltete_verweise(WURZEL / 'vorlage'), [])

    def test_basis_bringt_ablageort(self):
        typen = yaml.safe_load((WURZEL / 'pakete' / 'basis' / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'))
        a = next(t for t in typen if t['schluessel'] == 'ablageort')
        self.assertEqual([f['key'] for f in a['felder']], ['name', 'liegt_in', 'beschreibung'])
        self.assertTrue(a['felder'][0].get('pflicht'))
        self.assertEqual((a['felder'][1]['ziel'], a['felder'][1]['verweisart']), ('ablageort', 'zugehoerigkeit'))
        self.assertEqual([r['key'] for r in a['register']], ['allgemein', 'enthaelt', 'liegt_hier', 'fotos'])
        self.assertEqual(a['titelVorlage'], '{liegt_in} › {name}')
        self.assertIn('en', a['beschriftungen'])
        for p in ('haushalt', 'haus', 'vermietung', 'fahrzeuge'):
            m = yaml.safe_load((WURZEL / 'pakete' / p / 'manifest.yaml').read_text(encoding='utf-8'))
            self.assertEqual(m['abhaengigkeiten']['basis'], '>=1.6.0', p)
            self.assertIn('basis:ablageort', (WURZEL / 'pakete' / p / 'inhalt' / 'mappentypen.yaml').read_text(encoding='utf-8'), p)

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

    def sicht_alle(self, typen: list, dms: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'; m['dms'] = dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            sichten = yaml.safe_load((ziel / 'inhalt' / 'sichten.yaml').read_text(encoding='utf-8'))
            sichten[0]['typen'] = typen
            (ziel / 'inhalt' / 'sichten.yaml').write_text(yaml.safe_dump(sichten, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_ansicht_ueber_alle_mappentypen(self):
        # DMS #725: „*“ = alle Mappentypen, allein und ab Ablago 0.182.0.
        self.assertEqual(self.sicht_alle(['*'], '>=0.182.0'), [])
        self.assertTrue(any('erst ab 0.182.0' in f for f in self.sicht_alle(['*'], '>=0.150.0')))
        self.assertTrue(any('steht allein' in f for f in self.sicht_alle(['*', 'beispiel'], '>=0.182.0')))

    def test_id_dms_ist_reserviert(self):
        self.assertTrue(any('reserviert' in f for f in self.paket('beispiel', 'dms')))


class Ergaenzt(unittest.TestCase):
    """ergaenzt (motom001/dms#405): Ergänzung eines anderen Pakets, z. B. eine Zusatzsprache der Texterkennung."""

    def paket(self, ergaenzt, abh: dict | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            m['abhaengigkeiten'] = abh if abh is not None else {'texterkennung': '>=2.0.0'}
            m['ergaenzt'] = ergaenzt
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_gueltig(self):
        self.assertEqual(self.paket('texterkennung'), [])
        self.assertEqual(self.paket({'paket': 'texterkennung', 'gruppe': 'Weitere Sprachen'}), [])

    def test_muss_abhaengigkeit_sein(self):
        self.assertTrue(any('muss auch unter abhaengigkeiten' in f for f in self.paket('texterkennung', {})))

    def test_form(self):
        self.assertTrue(self.paket({'paket': 'texterkennung', 'farbe': 'rot'}))
        self.assertTrue(self.paket({'paket': 'texterkennung', 'gruppe': 'x' * 41}))
        self.assertTrue(self.paket('Texterkennung!'))

    def test_katalog_immer_als_objekt(self):
        import katalog
        self.assertEqual(katalog.ergaenzt_von({'ergaenzt': 'texterkennung'}), {'paket': 'texterkennung'})
        self.assertEqual(katalog.ergaenzt_von({'ergaenzt': {'paket': 'texterkennung', 'gruppe': 'Weitere Sprachen'}}), {'paket': 'texterkennung', 'gruppe': 'Weitere Sprachen'})

    def test_zusatzsprachen_der_registry(self):
        for ordner in sorted((WURZEL / 'pakete').glob('texterkennung.*')):
            m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8'))
            self.assertEqual(m.get('ergaenzt'), {'paket': 'texterkennung', 'gruppe': 'Weitere Sprachen'}, ordner.name)


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


class Verweise(unittest.TestCase):
    """Auswahlfilter (DMS #172, #173) und „folgt aus“ (DMS #886): dms-registry #139."""

    paket = AusText.paket

    ORG = {'key': 'oberes', 'label': 'Oberes', 'typ': 'referenz', 'ziel': 'beispiel'}
    TEIL = {'key': 'teil', 'label': 'Teil', 'typ': 'referenz', 'ziel': 'beispiel'}
    # Im Beispiel-Typ zeigt „oberes“ auf ein Beispiel; „teil“ ist ein anderes Beispiel, dessen „oberes“ übernommen wird.
    FOLGT = {**ORG, 'folgtAus': {'feld': 'teil', 'zielFeld': 'oberes'}}
    FILTER = {**TEIL, 'auswahlFilter': [{'art': 'feld', 'feld': 'oberes', 'op': 'zeigtAuf', 'wert': {'art': 'eigenesFeld', 'feld': 'oberes'}}]}

    def test_gueltig(self):
        self.assertEqual(self.paket([self.FOLGT, self.FILTER], dms='>=0.225.0'), [])
        self.assertEqual(self.paket([self.ORG, self.FILTER], dms='>=0.212.0'), [], 'Auswahlfilter allein braucht keine neue Version')

    def test_auswahlfilter(self):
        self.assertTrue(any('nur bei Verweisfeldern' in f for f in self.paket([{'key': 'x', 'label': 'X', 'typ': 'text', 'auswahlFilter': []}])))
        self.assertTrue(any('gibt es im Ziel-Mappentyp nicht' in f for f in self.paket([{**self.TEIL, 'auswahlFilter': [{'art': 'feld', 'feld': 'fehlt', 'op': 'leer'}]}])))
        self.assertTrue(any('anderes Feld dieses Mappentyps' in f for f in self.paket([{**self.TEIL, 'auswahlFilter': [{'art': 'feld', 'feld': 'teil', 'op': 'zeigtAuf', 'wert': {'art': 'eigenesFeld', 'feld': 'teil'}}]}])))

    def test_folgt_aus(self):
        self.assertTrue(any('kein anderes Feld' in f for f in self.paket([{**self.ORG, 'folgtAus': {'feld': 'fehlt', 'zielFeld': 'oberes'}}], dms='>=0.225.0')))
        self.assertTrue(any('kein Verweisfeld mit einer Mappe' in f for f in self.paket([{**self.FOLGT}, {**self.TEIL, 'mehrfach': True}], dms='>=0.225.0')))
        self.assertTrue(any('gibt es in „beispiel“ nicht' in f for f in self.paket([{**self.ORG, 'folgtAus': {'feld': 'teil', 'zielFeld': 'fehlt'}}, self.TEIL], dms='>=0.225.0')))
        self.assertTrue(any('selben Mappentyp' in f for f in self.paket([{**self.ORG, 'folgtAus': {'feld': 'teil', 'zielFeld': 'datum'}}, self.TEIL], dms='>=0.225.0')))
        self.assertTrue(any('im Kreis' in f for f in self.paket([self.FOLGT, {**self.TEIL, 'folgtAus': {'feld': 'oberes', 'zielFeld': 'teil'}}], dms='>=0.225.0')))
        self.assertTrue(any('erst ab 0.225.0' in f for f in self.paket([self.FOLGT, self.TEIL], dms='>=0.212.0')))


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



class Automatisierungen(unittest.TestCase):
    """inhalt.automatisierungen (DMS #712, Registry #108): Karten, Felder, Empfänger, DMS-Version, jede Frist erinnert."""

    TYPEN = {'vertrag': [
        {'key': 'name', 'typ': 'text'},
        {'key': 'kuendigen_bis', 'typ': 'datum', 'frist': {'vorlauf': 30, 'einheit': 'tage'}},
        {'key': 'verantwortlich', 'typ': 'referenz', 'ziel': 'dms:benutzer'},
        {'key': 'partner', 'typ': 'referenz', 'ziel': 'basis:organisation'},
    ]}

    def auto(self, **x):
        a = {'schluessel': 'k', 'name': 'Kündigung', 'wenn': {'art': 'datum', 'typ': 'vertrag', 'feld': 'kuendigen_bis', 'vorlauf': 30, 'einheit': 'tage'},
             'dann': [{'art': 'aufgabe', 'als': 'aufgabe', 'empfaenger': [{'art': 'feld', 'feld': 'verantwortlich', 'sonst': 'ersteller'}], 'text': 'Kündigen bis {datum}'}]}
        a.update(x)
        return a

    def pruefe(self, liste, dms='>=0.177.0'):
        return pruefen.pruefe_automatisierungen(liste, self.TYPEN, 'probe', {'basis'}, dms)

    def test_gueltig(self):
        self.assertEqual(self.pruefe([self.auto()]), [])

    def test_dms_version(self):
        self.assertTrue(any('0.177.0' in f for f in self.pruefe([self.auto()], dms='>=0.127.0')))

    def test_frist_ohne_automatisierung(self):
        self.assertTrue(any('Frist ohne mitgelieferte Automatisierung' in f for f in self.pruefe([])))
        self.assertEqual(pruefen.pruefe_automatisierungen([], self.TYPEN, 'probe', set(), '>=0.127.0'), [], 'ältere Pakete: Feld erinnert selbst')

    def test_benachrichtigungen(self):
        """Zeitplan, Favorit geändert und die Karten der Benachrichtigungen (DMS #678): passende Wenn-Karte, ab 0.181.0."""
        z = self.auto(schluessel='z', wenn={'art': 'zeitplan', 'uhrzeit': '07:00', 'jeBenutzer': True, 'profilzeit': True}, dann=[{'art': 'zusammenfassung'}])
        f = self.auto(schluessel='f', wenn={'art': 'favorit.geaendert'}, dann=[{'art': 'favoriten'}])
        s = self.auto(schluessel='s', wenn={'art': 'zeitplan', 'uhrzeit': '00:00', 'tage': [1, 2, 3, 4, 5, 6, 7]}, dann=[{'art': 'anmeldeschutz', 'was': 'sammel'}])
        k = self.auto(schluessel='k2', wenn={'art': 'benutzer.gesperrt'}, dann=[{'art': 'anmeldeschutz', 'was': 'konto'}])
        self.assertEqual(self.pruefe([self.auto(), z, f, s, k], dms='>=0.181.0'), [])
        self.assertTrue(any('0.181.0' in x for x in self.pruefe([self.auto(), z])))
        ohne = self.auto(schluessel='o', wenn={'art': 'zeitplan', 'uhrzeit': '07:00'}, dann=[{'art': 'zusammenfassung'}])
        self.assertTrue(any('jeBenutzer' in x for x in self.pruefe([self.auto(), ohne], dms='>=0.181.0')))
        falsch = self.auto(schluessel='x', wenn={'art': 'mappe.angelegt'}, dann=[{'art': 'favoriten'}])
        self.assertTrue(any('favorit.geaendert' in x for x in self.pruefe([self.auto(), falsch], dms='>=0.181.0')))
        rolle = self.auto(schluessel='r', wenn={'art': 'zeitplan', 'jeBenutzer': True, 'rolle': 'x'}, dann=[{'art': 'zusammenfassung'}])
        self.assertTrue(any('feste Rollen' in x for x in self.pruefe([self.auto(), rolle], dms='>=0.181.0')))
        tage = self.auto(schluessel='t', wenn={'art': 'zeitplan', 'tage': [0, 8]}, dann=[{'art': 'anmeldeschutz', 'was': 'sammel'}])
        self.assertTrue(any('wenn.tage' in x for x in self.pruefe([self.auto(), tage], dms='>=0.181.0')))

    def test_unbekannte_karten(self):
        self.assertTrue(any('unbekannte Wenn-Karte' in f for f in self.pruefe([self.auto(wenn={'art': 'zaehler.geaendert'})])))
        self.assertTrue(any('unbekannte Dann-Karte' in f for f in self.pruefe([self.auto(dann=[{'art': 'email', 'text': 'x'}])])))

    def test_feld_und_typ(self):
        self.assertTrue(any('kein Datumsfeld' in f for f in self.pruefe([self.auto(wenn={'art': 'datum', 'typ': 'vertrag', 'feld': 'name', 'vorlauf': 3})])))
        self.assertTrue(any('gibt es in diesem Paket nicht' in f for f in self.pruefe([self.auto(wenn={'art': 'mappe.angelegt', 'typ': 'gibtsnicht'})])))
        self.assertTrue(any('abhaengigkeiten' in f or 'Abhängigkeiten' in f for f in self.pruefe([self.auto(wenn={'art': 'mappe.angelegt', 'typ': 'fremd:x'})])))

    def test_empfaenger(self):
        dann = lambda e: [{'art': 'aufgabe', 'als': 'aufgabe', 'empfaenger': [e], 'text': 'x'}]  # noqa: E731
        self.assertTrue(any('feste Personen' in f for f in self.pruefe([self.auto(dann=dann({'art': 'person', 'id': 'abc'}))])))
        self.assertTrue(any('feste Personen' in f for f in self.pruefe([self.auto(dann=dann({'art': 'rolle', 'id': 'admin'}))])))
        self.assertTrue(any('Verweis auf Benutzer' in f for f in self.pruefe([self.auto(dann=dann({'art': 'feld', 'feld': 'partner'}))])))
        self.assertEqual(self.pruefe([self.auto(dann=dann({'art': 'ersteller'}))]), [])

    def test_person_aus_dem_ereignis(self):
        auto = {'schluessel': 'v', 'name': 'Vertretung', 'wenn': {'art': 'benutzer.abwesenheit_gesetzt'},
                'dann': [{'art': 'aufgabe', 'als': 'aufgabe', 'empfaenger': [{'art': 'ereignis', 'feld': 'vertreter'}], 'text': 'Du vertrittst {benutzer}.'}]}
        self.assertEqual(pruefen.pruefe_automatisierungen([auto], {}, 'probe', set(), '>=0.177.0'), [])
        auto['dann'][0]['empfaenger'] = [{'art': 'ereignis', 'feld': 'chef'}]
        self.assertTrue(any('keine Person' in f for f in pruefen.pruefe_automatisierungen([auto], {}, 'probe', set(), '>=0.177.0')))

    def test_doppelter_schluessel(self):
        self.assertTrue(any('doppelt' in f for f in self.pruefe([self.auto(), self.auto()])))

    def test_alle_pakete_mit_fristen_erinnern(self):
        """Jedes Paket mit einer Frist bringt ab 0.177.0 eine Automatisierung dafür mit (Registry #113)."""
        for p in ('haushalt', 'haus', 'fahrzeuge', 'vermietung'):
            self.assertEqual(pruefen.pruefe(WURZEL / 'pakete' / p, None), [], p)


PDF = b'%PDF-1.4\n% Beispiel fuer Lena, example.org\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'
PNG = b'\x89PNG\r\n\x1a\n' + b'\x01' * 32
JPEG = b'\xff\xd8\xff\xe0' + b'\x02' * 32


class BeispielDokumente(unittest.TestCase):
    """Beispiel-Dokumente in Paketen (Registry #137, motom001/dms#878)."""

    def paket(self, dokumente: list, dateien: dict, dms: str = '>=0.223.0', typ: str = 'beispiel') -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'], m['dms'] = 'probe', dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            mt = ziel / 'inhalt' / 'mappentypen.yaml'
            mt.write_text('\n'.join(z for z in mt.read_text(encoding='utf-8').splitlines() if not z.strip().startswith('frist:')) + '\n', encoding='utf-8')
            bsp = [{'typ': typ, 'schluessel': 'erstes', 'werte': {'bezeichnung': 'Wartungsvertrag Heizung'}, **({'dokumente': dokumente} if dokumente is not None else {})}]
            (ziel / 'inhalt' / 'beispiele.yaml').write_text(yaml.safe_dump(bsp, allow_unicode=True), encoding='utf-8')
            for name, inhalt in dateien.items():
                (ziel / 'inhalt' / name).parent.mkdir(parents=True, exist_ok=True)
                (ziel / 'inhalt' / name).write_bytes(inhalt)
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            self.hinweise = pruefen.hinweise(ziel)
            return pruefen.pruefe(ziel, None)

    GUT = [{'datei': 'beispiele/heizung/vertrag.pdf', 'titel': 'Wartungsvertrag', 'datum': '2023-04-01'},
           {'datei': 'beispiele/heizung/rechnung.png', 'register': 'dokumente'}, {'datei': 'beispiele/heizung/foto.JPG'}]
    DATEIEN = {'beispiele/heizung/vertrag.pdf': PDF, 'beispiele/heizung/rechnung.png': PNG, 'beispiele/heizung/foto.JPG': JPEG}

    def test_gueltig_und_groessen_gemeldet(self):
        self.assertEqual(self.paket(self.GUT, self.DATEIEN), [])
        h = '\n'.join(self.hinweise)
        self.assertIn('Beispiel-Dokumente: 3 Datei(en), zusammen', h)
        self.assertIn('inhalt/beispiele/heizung/vertrag.pdf', h)

    def test_schema(self):
        f = '\n'.join(self.paket([{'datei': 'beispiele/heizung/vertrag.pdf', 'unbekannt': 1}], self.DATEIEN))
        self.assertIn('unbekannt', f)
        f = '\n'.join(self.paket([{'datei': 'beispiele/heizung/vertrag.pdf', 'datum': '1.4.2023'}], self.DATEIEN))
        self.assertIn('datum', f)
        f = '\n'.join(self.paket([{'titel': 'ohne Datei'}], self.DATEIEN))
        self.assertIn('datei', f)

    def test_pfad_unter_beispiele(self):
        f = '\n'.join(self.paket([{'datei': 'mappentypen.yaml'}], {}))
        self.assertIn('muss unter inhalt/beispiele/ liegen', f)
        f = '\n'.join(self.paket([{'datei': 'beispiele/../manifest.pdf'}], {}))
        self.assertIn('muss unter inhalt/beispiele/ liegen', f)

    def test_datei_fehlt_oder_ist_leer(self):
        self.assertTrue(any('fehlt' in x for x in self.paket([{'datei': 'beispiele/gibtsnicht.pdf'}], {})))
        self.assertTrue(any('ist leer' in x for x in self.paket([{'datei': 'beispiele/leer.pdf'}], {'beispiele/leer.pdf': b''})))

    def test_nur_pdf_png_jpeg_passend_zur_endung(self):
        f = '\n'.join(self.paket([{'datei': 'beispiele/falsch.pdf'}], {'beispiele/falsch.pdf': PNG}))
        self.assertIn('kein PDF, PNG oder JPEG', f)
        f = '\n'.join(self.paket([{'datei': 'beispiele/notiz.txt'}], {'beispiele/notiz.txt': b'Hallo'}))
        self.assertTrue('notiz.txt' in f, f)
        self.assertEqual(pruefen.dateiart('a.gif', b'GIF89a'), None)
        self.assertEqual(pruefen.dateiart('a.jpeg', JPEG), 'image/jpeg')

    def test_jede_datei_genannt(self):
        f = '\n'.join(self.paket(self.GUT, {**self.DATEIEN, 'beispiele/uebrig.pdf': PDF}))
        self.assertIn('inhalt/beispiele/uebrig.pdf: liegt unter inhalt/beispiele/, aber kein Beispiel nennt', f)
        # Auch ohne ein einziges genanntes Dokument.
        f = '\n'.join(self.paket(None, {'beispiele/uebrig.pdf': PDF}, dms='>=0.41.0'))
        self.assertIn('kein Beispiel nennt', f)

    def test_groesse_je_datei_und_gesamt(self):
        alt = pruefen.BEISPIEL_DATEI_MAX, pruefen.PAKET_MAX
        try:
            pruefen.BEISPIEL_DATEI_MAX, pruefen.PAKET_MAX = 40, 200
            f = '\n'.join(self.paket(self.GUT, self.DATEIEN))
            self.assertIn('höchstens 0 MB je Datei', f)
            pruefen.BEISPIEL_DATEI_MAX = 1000
            gross = {f'beispiele/teil{i}.pdf': PDF for i in range(4)}
            f = '\n'.join(self.paket([{'datei': n} for n in gross], gross))
            self.assertIn('inhalt/beispiele/: zusammen', f)
        finally:
            pruefen.BEISPIEL_DATEI_MAX, pruefen.PAKET_MAX = alt
        # Die Grenze von 2 MB je Datei gilt für Beispiel-Dokumente nicht.
        gross = PDF + b'0' * (3 * 1024 * 1024)
        self.assertEqual(self.paket([{'datei': 'beispiele/gross.pdf'}], {'beispiele/gross.pdf': gross}), [])

    def test_register_muss_dokumentenregister_sein(self):
        f = '\n'.join(self.paket([{'datei': 'beispiele/heizung/vertrag.pdf', 'register': 'daten'}], self.DATEIEN))
        self.assertIn('kein Dokumentenregister „daten“', f)

    def test_braucht_ablago_0_222(self):
        f = '\n'.join(self.paket(self.GUT, self.DATEIEN, dms='>=0.221.0'))
        self.assertIn('dms: ">=0.223.0"', f)

    def test_katalog_zaehlt_beispiel_dokumente(self):
        import katalog
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            ziel.mkdir()
            (ziel / 'inhalt').mkdir()
            (ziel / 'inhalt' / 'beispiele.yaml').write_text(yaml.safe_dump([{'typ': 'a', 'werte': {}, 'dokumente': [{'datei': 'beispiele/a.pdf'}, {'datei': 'beispiele/b.pdf'}]}, {'typ': 'a', 'werte': {}}]), encoding='utf-8')
            m = {'id': 'probe', 'version': '1.0.0', 'dms': '>=0.223.0', 'inhalt': {'beispiele': 'inhalt/beispiele.yaml'}}
            e = katalog.eintrag(ziel, m, 'probe-1.0.0.zip', b'x', '2026-11-08T00:00:00Z')
            self.assertEqual((e['inhalt']['beispiele'], e['inhalt']['beispieldokumente']), (2, 2))
            (ziel / 'inhalt' / 'beispiele.yaml').write_text(yaml.safe_dump([{'typ': 'a', 'werte': {}}]), encoding='utf-8')
            self.assertNotIn('beispieldokumente', katalog.eintrag(ziel, m, 'probe-1.0.0.zip', b'x', '2026-11-08T00:00:00Z')['inhalt'])


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

    def test_eine_grenze_wie_im_dms(self):
        import json
        import katalog, sammeldatei  # noqa: E401
        self.assertEqual(pruefen.PAKET_MAX, 128 * 1024 * 1024)
        self.assertEqual(pruefen.CODE_MAX, pruefen.PAKET_MAX)
        self.assertEqual(katalog.PAKET_MAX, pruefen.PAKET_MAX)
        self.assertEqual(sammeldatei.ARCHIV_MAX, pruefen.PAKET_MAX)
        schema = json.loads((WURZEL / 'schema' / 'sammeldatei.schema.json').read_text(encoding='utf-8'))
        self.assertIn(f'"maximum": {pruefen.PAKET_MAX}', json.dumps(schema))

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
            self.assertTrue(any('höchstens 128 MB' in f for f in pruefen.pruefe(ziel, None)))


class FremdeTypen(unittest.TestCase):
    """Ansichten mit fremde_typen (DMS #656): ab 0.178.0, Kennung nach dem Muster einer Mappentyp-Kennung."""

    def paket(self, fremde, dms: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / 'probe'
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = 'probe'
            m['dms'] = dms
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            # Ab 0.177.0 braucht eine Frist eine mitgelieferte Automatisierung – hier geht es nur um fremde_typen.
            mt = ziel / 'inhalt' / 'mappentypen.yaml'
            mt.write_text('\n'.join(z for z in mt.read_text(encoding='utf-8').splitlines() if not z.strip().startswith('frist:')) + '\n', encoding='utf-8')
            sichten = yaml.safe_load((ziel / 'inhalt' / 'sichten.yaml').read_text(encoding='utf-8'))
            sichten[0]['fremde_typen'] = fremde
            (ziel / 'inhalt' / 'sichten.yaml').write_text(yaml.safe_dump(sichten, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_fremde_typen(self):
        self.assertEqual(self.paket([{'kennung': 'vertrag', 'name': 'Vertrag'}], '>=0.178.0'), [])
        alt = self.paket([{'kennung': 'vertrag', 'name': 'Vertrag'}], '>=0.177.0')
        self.assertTrue(any('fremde_typen kennt das DMS erst ab 0.178.0' in f for f in alt), alt)
        self.assertTrue(self.paket([{'kennung': 'Vertrag!'}], '>=0.178.0'))
        self.assertTrue(self.paket([{'name': 'ohne Kennung'}], '>=0.178.0'))


class Paketsprache(unittest.TestCase):
    """Registry #157: gleiche Kennungen (Hinweise für neue Felder), Text-Vorlagen, Mappentyp in genau einem Paket."""

    TYP = [{'schluessel': 'rechnung', 'name': 'Rechnung', 'felder': [
        {'key': 'absender', 'typ': 'referenz'}, {'key': 'von', 'typ': 'datum'}, {'key': 'betrag', 'typ': 'text'},
        {'key': 'an', 'typ': 'referenz'}, {'key': 'kennwort', 'typ': 'passwort'}]}]

    def test_kennungen(self):
        h = pruefen.kennung_hinweise(self.TYP, None)
        self.assertTrue(any('rechnung.absender' in x and '„von“' in x for x in h), h)
        self.assertTrue(any('rechnung.von' in x and '„beginn“' in x for x in h), h)
        self.assertTrue(any('rechnung.betrag' in x and 'hier text' in x for x in h), h)
        self.assertFalse(any('rechnung.an' in x for x in h), h)
        # nur neue Felder
        self.assertEqual(pruefen.kennung_hinweise(self.TYP, set()), [])
        self.assertEqual(len(pruefen.kennung_hinweise(self.TYP, {('rechnung', 'absender')})), 1)

    def test_neue_felder_ohne_basis(self):
        self.assertEqual(pruefen.neue_felder(WURZEL / 'pakete' / 'haushalt', None, self.TYP, None), set())

    def test_vorlage_text(self):
        ok = 'Kündigung\n\nSehr geehrte Damen und Herren,\nhiermit kündige ich {vertragsnummer} von {von.name} zum {kuendigen_bis}.\n' \
             'Mehr: [Hilfe](https://help.ablago.app) oder <https://example.org/kuendigen>\n\n*Muster ohne Gewähr, keine Rechtsberatung.*\n'
        self.assertEqual(pruefen.pruefe_vorlage_text(ok.encode(), 'v.md', {'kennwort'}), [])
        for schlecht, teil in [
            ('<b>fett</b>', 'kein HTML'), ('<!-- x -->', 'kein HTML'), ('![Logo](https://example.org/l.png)', 'keine Bilder'),
            ('[x](http://example.org)', 'nur mit https'), ('[x](javascript:alert(1))', 'nur mit https'), ('siehe http://example.org', 'nur mit https://'),
            ('[a]: http://example.org', 'nur mit https'), ('Passwort: {kennwort}', 'Passwortfelder'), ('{konto.kennwort}', 'Passwortfelder')]:
            f = pruefen.pruefe_vorlage_text(schlecht.encode(), 'v.md', {'kennwort'})
            self.assertTrue(any(teil in x for x in f), (schlecht, f))
        self.assertTrue(pruefen.pruefe_vorlage_text(b'\xff\xfe', 'v.md', set()))
        self.assertTrue(pruefen.pruefe_vorlage_text(b'a' * (pruefen.VORLAGE_MAX + 1), 'v.md', set()))

    def test_vorlagen_ordner(self):
        with tempfile.TemporaryDirectory() as tmp:
            o = Path(tmp)
            v = o / 'inhalt' / 'vorlagen'
            v.mkdir(parents=True)
            (v / 'kuendigung.md').write_text('Kündigung {vertragsnummer}\n', encoding='utf-8')
            self.assertEqual(pruefen.pruefe_vorlagen(o, self.TYP), [])
            (v / 'brief.docx').write_bytes(b'PK')
            (v / 'LICENSE').write_text('MIT License', encoding='utf-8')
            f = pruefen.pruefe_vorlagen(o, self.TYP)
            self.assertTrue(any('brief.docx' in x for x in f), f)
            self.assertTrue(any('LICENSE' in x for x in f), f)
            (v / 'brief.docx').unlink()
            (v / 'LICENSE').write_text('Creative Commons Attribution 4.0 International', encoding='utf-8')
            self.assertEqual(pruefen.pruefe_vorlagen(o, self.TYP), [])

    def test_mappentyp_in_einem_paket(self):
        with tempfile.TemporaryDirectory() as tmp:
            for pid in ('eins', 'zwei'):
                o = Path(tmp) / pid
                (o / 'inhalt').mkdir(parents=True)
                (o / 'manifest.yaml').write_text(yaml.safe_dump({'id': pid, 'inhalt': {'mappentypen': 'inhalt/mappentypen.yaml'}}), encoding='utf-8')
                (o / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump([{'schluessel': 'vertrag', 'name': 'Vertrag'}]), encoding='utf-8')
            h = pruefen.doppelte_typen([Path(tmp) / 'eins', Path(tmp) / 'zwei'])
            self.assertEqual(len(h), 1)
            self.assertIn('eins:vertrag', h[0])
        self.assertEqual(pruefen.doppelte_typen(sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir())), [])


class Kennungen(unittest.TestCase):
    """Registry #173: gleiche zusammengesetzte Kennung <paket>_<schluessel> aus zwei Paketen."""

    def paket(self, wurzel: Path, pid: str, typen: list[str], ergaenzt: str | None = None) -> Path:
        o = wurzel / pid
        (o / 'inhalt').mkdir(parents=True)
        m = {'id': pid, 'inhalt': {'mappentypen': 'inhalt/mappentypen.yaml'}}
        if ergaenzt:
            m['ergaenzt'] = ergaenzt
        (o / 'manifest.yaml').write_text(yaml.safe_dump(m), encoding='utf-8')
        (o / 'inhalt' / 'mappentypen.yaml').write_text(yaml.safe_dump([{'schluessel': s, 'name': s} for s in typen]), encoding='utf-8')
        return o

    def test_kollision(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.paket(Path(tmp), 'haus', ['garten_pflanze'])
            b = self.paket(Path(tmp), 'haus_garten', ['pflanze'])
            f, h = pruefen.kennungs_kollisionen([a, b])
            self.assertEqual(len(f), 1, f)
            self.assertIn('haus_garten_pflanze', f[0])
            self.assertTrue(any('haus_garten' in x for x in h), h)

    def test_ergaenzung_ohne_hinweis(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self.paket(Path(tmp), 'texterkennung', [])
            b = self.paket(Path(tmp), 'texterkennung_fra', [], ergaenzt='texterkennung')
            self.assertEqual(pruefen.kennungs_kollisionen([a, b]), ([], []))

    def test_registry_ohne_kollision(self):
        f, h = pruefen.kennungs_kollisionen(sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir()))
        self.assertEqual(f, [])
        self.assertEqual(h, [])


class IdsNurEinmal(unittest.TestCase):
    """Registry #173: Eine Paket-Id gehört für immer zu einem Paket (werkzeuge/ids.txt)."""

    def paket(self, wurzel: Path, pid: str) -> Path:
        o = wurzel / pid
        o.mkdir(parents=True)
        (o / 'manifest.yaml').write_text(yaml.safe_dump({'id': pid}), encoding='utf-8')
        return o

    def test_registry(self):
        self.assertEqual(pruefen.id_pruefung(sorted(p for p in (WURZEL / 'pakete').iterdir() if (p / 'manifest.yaml').exists()), None), [])

    def test_neue_id_eintragen(self):
        with tempfile.TemporaryDirectory() as tmp:
            o = self.paket(Path(tmp), 'garten')
            self.assertTrue(any('ids.txt eintragen' in x for x in pruefen.id_pruefung([o], None, 'haus\n')))
            self.assertEqual(pruefen.id_pruefung([o], None, 'haus\ngarten\n'), [])

    def test_nie_streichen(self):
        self.assertTrue(any('gestrichen' in x for x in pruefen.id_pruefung([], 'x', 'haus\n', 'haus\nalt\n')))

    def test_alte_id_fuer_neues_paket(self):
        with tempfile.TemporaryDirectory() as tmp:
            o = self.paket(Path(tmp), 'alt')
            f = pruefen.id_pruefung([o], 'x', '# Kommentar\nalt\n', 'alt\n', gab_es=lambda pid: False)
            self.assertTrue(any('schon vergeben' in x for x in f), f)
            self.assertEqual(pruefen.id_pruefung([o], 'x', 'alt\n', 'alt\n', gab_es=lambda pid: True), [])


class KennungenNach1084(unittest.TestCase):
    """Registry #173 nach motom001/dms#1084: Ids 40 + Punkt-Zusatz 20, Schlüssel 60, herausgeber, ersetzt."""

    def paket(self, pid: str, **felder) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ziel = Path(tmp) / pid
            shutil.copytree(WURZEL / 'vorlage', ziel)
            m = yaml.safe_load((ziel / 'manifest.yaml').read_text(encoding='utf-8'))
            m['id'] = pid
            m.pop('code', None)
            shutil.rmtree(ziel / 'code', ignore_errors=True)
            m.update(felder)
            (ziel / 'manifest.yaml').write_text(yaml.safe_dump(m, allow_unicode=True), encoding='utf-8')
            (ziel / 'LICENSE').write_text((ziel / 'LICENSE').read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            return pruefen.pruefe(ziel, None)

    def test_id_mit_punkt(self):
        neu = {'dms': '>=0.229.0', 'abhaengigkeiten': {'texterkennung': '>=2.0.0'}}
        self.assertEqual(self.paket('texterkennung.fra', ergaenzt='texterkennung', **neu), [])
        self.assertTrue(any('ergänzt das Paket vor dem Punkt' in f for f in self.paket('texterkennung.fra', **neu)))
        self.assertTrue(any('ergänzt das Paket vor dem Punkt' in f for f in self.paket('haus.fra', ergaenzt='texterkennung', **neu)))
        self.assertTrue(any('erst ab 0.229.0' in f for f in self.paket('texterkennung.fra', ergaenzt='texterkennung', dms='>=0.228.0',
                                                                      abhaengigkeiten={'texterkennung': '>=2.0.0'})))
        for falsch in ('a.b.c', 'haus..x', '.haus', 'haus.', 'haus.' + 'x' * 21):
            self.assertTrue(self.paket(falsch, dms='>=0.229.0'), falsch)

    def test_laengen(self):
        self.assertEqual(self.paket('h' * 40, dms='>=0.229.0'), [])
        self.assertTrue(any('über 20 Zeichen' in f for f in self.paket('h' * 21, dms='>=0.228.0')))
        self.assertTrue(self.paket('h' * 41, dms='>=0.229.0'))

    def test_ersetzt(self):
        self.assertEqual(self.paket('neu', dms='>=0.229.0', ersetzt='alt'), [])
        self.assertEqual(self.paket('neu', dms='>=0.229.0', ersetzt=['alt', 'aelter']), [])
        self.assertTrue(any('erst ab 0.229.0' in f for f in self.paket('neu', dms='>=0.228.0', ersetzt='alt')))
        self.assertTrue(any('nicht die eigene' in f for f in self.paket('neu', dms='>=0.229.0', ersetzt='neu')))
        self.assertTrue(self.paket('neu', dms='>=0.229.0', ersetzt=['a1', 'a2', 'a3', 'a4', 'a5', 'a6']))

    def test_herausgeber_nur_app_ablago(self):
        self.assertTrue(self.paket('probe', herausgeber='org.example'))
        self.assertEqual(self.paket('probe', herausgeber='app.ablago'), [])

    def test_herausgeber_pflicht_fuer_neue_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            o = Path(tmp) / 'probe_neu_gibtsnicht'
            o.mkdir()
            m = {'id': o.name, 'version': '1.0.0', 'dms': '>=0.1.0'}
            f = pruefen.kennungen_pruefung(o, m, None, 'HEAD', False)
            self.assertTrue(any('herausgeber: app.ablago fehlt' in x for x in f), f)
            self.assertEqual(pruefen.kennungen_pruefung(o, {**m, 'herausgeber': 'app.ablago'}, None, 'HEAD', False), [])
            self.assertEqual(pruefen.kennungen_pruefung(o, m, None, None, False), [])  # ohne Basis (main): katalog.py prüft
        # Unveränderte Version eines vorhandenen Pakets braucht das Feld nicht (bis zur nächsten Version).
        haus = yaml.safe_load((WURZEL / 'pakete' / 'haus' / 'manifest.yaml').read_text(encoding='utf-8'))
        self.assertFalse(pruefen.neue_version(WURZEL / 'pakete' / 'haus', haus, 'HEAD'))

    def test_lange_schluessel_brauchen_0229(self):
        with tempfile.TemporaryDirectory() as tmp:
            o = Path(tmp)
            (o / 'typen.yaml').write_text(yaml.safe_dump([{'schluessel': 's' * 41, 'felder': [{'key': 'k' * 45}]}]), encoding='utf-8')
            m = {'id': 'probe', 'dms': '>=0.228.0', 'inhalt': {'mappentypen': 'typen.yaml'}}
            self.assertEqual(len(pruefen.lange_schluessel(o, m)), 2)
            self.assertTrue(pruefen.kennungen_pruefung(o, m, None, None, False))
            self.assertEqual(pruefen.kennungen_pruefung(o, {**m, 'dms': '>=0.229.0'}, None, None, False), [])

    def test_umzug_in_der_id_pruefung(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = Path(tmp)
            for pid, m in (('texterkennung', {'id': 'texterkennung'}), ('texterkennung.fra', {'id': 'texterkennung.fra', 'ersetzt': 'texterkennung_fra'})):
                (w / pid).mkdir()
                (w / pid / 'manifest.yaml').write_text(yaml.safe_dump(m), encoding='utf-8')
            ids = 'texterkennung\ntexterkennung_fra\ntexterkennung.fra\n'
            self.assertEqual(pruefen.id_pruefung([w / 'texterkennung.fra'], None, ids), [])
            self.assertTrue(any('gab es nie' in x for x in pruefen.id_pruefung([w / 'texterkennung.fra'], None, 'texterkennung\ntexterkennung.fra\n')))
            (w / 'texterkennung_fra').mkdir()
            self.assertTrue(any('gibt es aber noch' in x for x in pruefen.id_pruefung([w / 'texterkennung.fra'], None, ids)))
            (w / 'texterkennung_fra').rmdir()
            shutil.rmtree(w / 'texterkennung')
            self.assertTrue(any('Hauptpaket' in x for x in pruefen.id_pruefung([w / 'texterkennung.fra'], None, ids)))


class Etappe15(unittest.TestCase):
    """Paketformat Etappe 15/16 (Registry #159, Entwurf): neue Bausteine und ihre Prüfungen."""

    VERTRAG = {'schluessel': 'vertrag', 'name': 'Vertrag', 'beschreibung': 'x', 'felder': [
        {'key': 'bezeichnung', 'label': 'Bezeichnung', 'typ': 'text'},
        {'key': 'vertragsart', 'label': 'Vertragsart', 'typ': 'referenz', 'ziel': 'vertragsart',
         'vorbelegen': [{'von': 'mindestlaufzeit', 'nach': 'mindestlaufzeit'}]},
        {'key': 'betrifft', 'label': 'Betrifft', 'typ': 'referenz', 'ziel': ['basis:person', 'basis:organisation'], 'mehrfach': True, 'gleicherTyp': True},
        {'key': 'mindestlaufzeit', 'label': 'Mindestlaufzeit', 'typ': 'zeitraum'},
        {'key': 'betrag', 'label': 'Betrag', 'typ': 'betrag', 'negativ': True},
        {'key': 'status', 'label': 'Status', 'typ': 'text', 'berechnet': True},
        {'key': 'kaltmiete', 'label': 'Kaltmiete', 'typ': 'betrag', 'anzeigen': {'bedingungen': [{'art': 'vorgabe', 'feld': 'vertragsart', 'vorgabe': ['miete']}]}},
        {'key': 'nummer', 'label': 'Nummer', 'typ': 'zusammengesetzt', 'vorlage': '{bezeichnung} · {betrag}'},
        {'key': 'positionen', 'label': 'Positionen', 'typ': 'tabelle', 'quelle': {'typ': 'teil', 'feld': 'vertrag'}},
    ], 'register': [{'key': 'allgemein', 'name': 'Allgemein', 'art': 'felder',
                     'felder': ['bezeichnung', 'vertragsart', 'betrifft', 'mindestlaufzeit', 'betrag', 'status', 'kaltmiete', 'nummer', 'positionen'],
                     'abschnitte': [{'vor': 'kaltmiete', 'titel': 'Miete', 'anzeigen': {'modus': 'eine', 'bedingungen': [{'art': 'merkmal', 'merkmal': 'beruflich'},
                                                                                 {'art': 'feld', 'bedingung': {'feld': 'betrag', 'op': 'groesser', 'wert': {'art': 'fest', 'wert': 100}}}]}}]},
                    {'key': 'vorlagen', 'name': 'Vorlagen', 'art': 'dokumente'}]}
    ART = {'schluessel': 'vertragsart', 'name': 'Vertragsart', 'beschreibung': 'x', 'felder': [
        {'key': 'name', 'label': 'Name', 'typ': 'text'}, {'key': 'mindestlaufzeit', 'label': 'Mindestlaufzeit', 'typ': 'zeitraum'}],
        'register': [{'key': 'allgemein', 'name': 'Allgemein', 'art': 'felder', 'felder': ['name', 'mindestlaufzeit']},
                     {'key': 'vorlagen', 'name': 'Vorlagen', 'art': 'dokumente'}]}
    TEIL = {'schluessel': 'teil', 'name': 'Teil', 'beschreibung': 'x', 'gehoertZu': 'vertrag', 'felder': [
        {'key': 'vertrag', 'label': 'Vertrag', 'typ': 'referenz', 'ziel': 'vertrag', 'pflicht': True}],
        'register': [{'key': 'allgemein', 'name': 'Allgemein', 'art': 'felder', 'felder': ['vertrag']}]}
    VORGABEN = [{'kennung': 'miete', 'typ': 'vertragsart', 'werte': {'name': 'Miete', 'mindestlaufzeit': {'anzahl': 0, 'einheit': 'monate'}},
                 'vorlagen': [{'datei': 'vorlagen/kuendigung.md', 'register': 'vorlagen', 'titel': 'Kündigung'}]}]
    MANIFEST = {'id': 'probe', 'dms': '>=0.239.0', 'code': {'rechte': {'schreiben': ['vertrag']}}}

    def test_paket_nach_zeitplan(self):
        a = [{'schluessel': 'taeglich', 'name': 'Täglich prüfen', 'eingeschaltet': True, 'wenn': {'art': 'zeitplan', 'uhrzeit': '05:00', 'tage': [1, 2, 3, 4, 5, 6, 7]},
              'dann': [{'art': 'paket', 'aufgabe': 'taeglich'}]}]
        self.assertEqual(list(pruefen.inhalt_validator('automatisierungen').iter_errors(a)), [])
        self.assertEqual(pruefen.pruefe_automatisierungen(a, {}, 'probe', set(), '>=0.233.0', ('zeitplan.ausgefuehrt',)), [])
        f = '\n'.join(pruefen.pruefe_automatisierungen(a, {}, 'probe', set(), '>=0.226.0', ()))
        self.assertIn('zeitplan.ausgefuehrt', f)
        self.assertIn('erst ab', f)
        a[0]['wenn'] = {'art': 'datum', 'typ': 'x', 'feld': 'y', 'vorlauf': 1, 'einheit': 'tage'}
        self.assertTrue(any('nur mit wenn: zeitplan' in x for x in pruefen.pruefe_automatisierungen(a, {}, 'probe', set(), '>=0.233.0', ('zeitplan.ausgefuehrt',))))

    def lauf(self, typen=None, vorgaben=None, manifest=None, mit_datei=True):
        import copy
        with tempfile.TemporaryDirectory() as tmp:
            o = Path(tmp)
            if mit_datei:
                (o / 'inhalt' / 'vorlagen').mkdir(parents=True)
                (o / 'inhalt' / 'vorlagen' / 'kuendigung.md').write_text('Kündigung\n', encoding='utf-8')
            return pruefen.pruefe_etappe15(o, copy.deepcopy(manifest or self.MANIFEST), copy.deepcopy(typen or [self.VERTRAG, self.ART, self.TEIL]),
                                           copy.deepcopy(self.VORGABEN if vorgaben is None else vorgaben), [], {'basis'})

    def test_gueltig(self):
        self.assertEqual(self.lauf(), [])

    def test_schema(self):
        v = pruefen.inhalt_validator('mappentypen')
        self.assertEqual(list(v.iter_errors([self.VERTRAG, self.ART, self.TEIL])), [])
        self.assertEqual(list(pruefen.inhalt_validator('vorgaben').iter_errors(self.VORGABEN)), [])
        self.assertTrue(list(pruefen.inhalt_validator('vorgaben').iter_errors([{'ergaenzt': 'fahrzeuge:pkw', 'kennung': 'x', 'vorlagen': []}])))
        self.assertEqual(list(pruefen.inhalt_validator('vorgaben').iter_errors([{'ergaenzt': 'vertraege:miete', 'vorlagen': [{'datei': 'vorlagen/garage.md'}]}])), [])
        self.assertTrue(list(pruefen.inhalt_validator('vorgaben').iter_errors([{'ergaenzt': 'vertraege:miete', 'vorlagen': [{'datei': 'vorlagen/a.b.md'}]}])))

    def test_braucht_version(self):
        # Mindestversion je Baustein wie DMS_*_AB in Ablago; die Meldung nennt die höchste nötige.
        f = self.lauf(manifest={**self.MANIFEST, 'dms': '>=0.226.0'})
        self.assertTrue(any('Feldart zusammengesetzt kennt Ablago erst ab 0.239.0' in x for x in f), f)
        self.assertFalse(any('vorläufig' in x for x in f), f)
        for ab, was in (('0.230.0', 'mehrere Ziele'), ('0.231.0', 'berechnet'), ('0.232.0', 'Feldart tabelle'), ('0.234.0', 'vorbelegen'),
                        ('0.235.0', 'gehoertZu'), ('0.236.0', 'Vorgaben')):
            self.assertEqual(pruefen.__dict__[{'0.230.0': 'DMS_MEHRERE_ZIELE_AB', '0.231.0': 'DMS_BERECHNET_AB', '0.232.0': 'DMS_TABELLE_AB',
                                               '0.234.0': 'DMS_VORBELEGEN_AB', '0.235.0': 'DMS_TEILE_AB', '0.236.0': 'DMS_VORGABEN_AB'}[ab]],
                             tuple(int(x) for x in ab.split('.')), was)

    def test_version_je_baustein(self):
        """Was schon in Ablago ist, braucht nur die Version, in der es kam (#1035: 0.227.0, #1033: 0.228.0)."""
        typ = {'schluessel': 'abo', 'name': 'Abo', 'beschreibung': 'x', 'felder': [
            {'key': 'laufzeit', 'label': 'Laufzeit', 'typ': 'zeitraum', 'standard': 'P12M'},
            {'key': 'rabatt', 'label': 'Rabatt', 'typ': 'prozent'},
            {'key': 'notiz', 'label': 'Notiz', 'typ': 'langtext', 'anzeigen': {'bedingungen': [{'art': 'merkmal', 'merkmal': 'beruflich', 'nicht': True}]}}],
            'register': [{'key': 'a', 'name': 'A', 'art': 'felder', 'felder': ['laufzeit', 'rabatt', 'notiz']}]}
        self.assertEqual(list(pruefen.inhalt_validator('mappentypen').iter_errors([typ])), [])
        f = pruefen.pruefe_etappe15(Path('.'), {'id': 'probe', 'dms': '>=0.227.0'}, [typ], [], [], set())
        self.assertTrue(f and 'Anzeigen, wenn' in f[0] and '0.228.0' in f[0] and 'vorläufig' not in f[0], f)
        self.assertEqual(pruefen.pruefe_etappe15(Path('.'), {'id': 'probe', 'dms': '>=0.228.0'}, [typ], [], [], set()), [])

    def test_alte_schreibweise(self):
        import copy
        v = copy.deepcopy(self.VERTRAG)
        v['felder'][0]['anzeigenWenn'] = [{'merkmal': 'beruflich'}]
        self.assertTrue(any('anzeigenWenn heißt in Ablago anzeigen' in x for x in self.lauf(typen=[v, self.ART, self.TEIL])))

    def test_berechnet_braucht_schreibrecht(self):
        f = self.lauf(manifest={'id': 'probe', 'dms': '>=0.239.0', 'code': {'rechte': {'lesen': ['vertrag']}}})
        self.assertTrue(any('code.rechte.schreiben' in x for x in f), f)
        f = self.lauf(manifest={'id': 'probe', 'dms': '>=0.239.0'})
        self.assertTrue(any('nur ein Paket mit Code' in x for x in f), f)

    def test_fehler(self):
        import copy
        v = copy.deepcopy(self.VERTRAG)
        felder = {f['key']: f for f in v['felder']}
        felder['kaltmiete']['anzeigen'] = {'bedingungen': [{'art': 'feld', 'bedingung': {'feld': 'gibtsnicht', 'op': 'leer'}},
                                                           {'art': 'vorgabe', 'feld': 'vertragsart', 'vorgabe': ['unbekannt']},
                                                           {'art': 'feld', 'bedingung': {'feld': 'betrag', 'op': 'enthaelt'}},
                                                           {'art': 'verweistyp', 'feld': 'betrifft', 'typ': 'fahrzeuge:fahrzeug'}]}
        felder['nummer']['vorlage'] = '{nummer} {kennwort}'
        felder['positionen']['quelle'] = {'typ': 'teil', 'feld': 'falsch'}
        felder['vertragsart']['vorbelegen'] = [{'von': 'gibtsnicht', 'nach': 'vertragsart'}]
        teil = copy.deepcopy(self.TEIL)
        teil['felder'][0]['pflicht'] = False
        f = '\n'.join(self.lauf(typen=[v, self.ART, teil]))
        for teil_text in ('gibtsnicht“ – das Feld gibt es', 'Vorgabe „unbekannt“', 'vorlage nennt „nummer“', 'quelle.feld „falsch“',
                          'vorbelegen von „gibtsnicht“', 'vorbelegen nach „vertragsart“', 'gehoertZu',
                          'Operator „enthaelt“ gibt es dafür nicht', 'kein Ziel dieses Verweisfelds'):
            self.assertIn(teil_text, f)

    def test_ziel_optional(self):
        import copy
        v = copy.deepcopy(self.VERTRAG)
        v['felder'].append({'key': 'betrifft2', 'label': 'B', 'typ': 'referenz', 'zielOptional': ['fahrzeuge:fahrzeug'], 'mehrfach': True, 'gleicherTyp': True})
        self.assertEqual(self.lauf(typen=[v, self.ART, self.TEIL]), [])
        self.assertEqual(list(pruefen.inhalt_validator('mappentypen').iter_errors([v])), [])
        v['felder'][-1]['zielOptional'] = ['vertrag']
        self.assertTrue(any('zielOptional' in x for x in self.lauf(typen=[v, self.ART, self.TEIL])))

    def test_vorgaben(self):
        f = '\n'.join(self.lauf(vorgaben=[
            {'kennung': 'a', 'typ': 'vertragsart', 'werte': {'mindestlaufzeit': 24, 'gibtsnicht': 1}, 'vorlagen': [{'datei': 'vorlagen/fehlt.md', 'register': 'allgemein'}]},
            {'kennung': 'a', 'typ': 'fremd:typ', 'werte': {}},
            {'ergaenzt': 'probe:a', 'vorlagen': [{'datei': 'vorlagen/kuendigung.md'}]}]))
        for teil_text in ('ist ein Zeitraum', '„gibtsnicht“ gibt es', 'fehlt.md fehlt', 'kein Dokumentenregister', 'Kennung doppelt',
                          '„fremd“ muss unter abhaengigkeiten', 'Vorgabe eines anderen Pakets', 'Vorgabe „unbekannt“' if False else 'Vorgabe „miete“'):
            self.assertIn(teil_text, f)
