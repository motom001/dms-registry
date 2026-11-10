"""Tests für webseite.py: Die DMS-Version kommt nur im Fragment #dms=…, nie als Query (motom001/dms#622).

    python3 -m unittest werkzeuge/test_webseite.py

Ein Query (?dms=…) ginge an GitHub Pages und stünde dort im Zugriffsprotokoll – das Fragment nicht.
"""
import re, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import webseite as w  # noqa: E402

FRAGMENT = r"/(?:^#|&)dms=(\d+\.\d+\.\d+)(?:&|$)/.exec(location.hash)"


class VersionNurImFragment(unittest.TestCase):
    def test_dms_js_liest_fragment_merkt_und_entfernt_es(self):
        self.assertIn(FRAGMENT, w.SKRIPT)
        self.assertIn("VSCHL = 'dms-version'", w.SKRIPT)
        self.assertIn("history.replaceState(null, '', location.pathname + location.search)", w.SKRIPT)
        self.assertIn('window.dmsVersion = { lies: liesVersion, merke: merkeVersion }', w.SKRIPT)

    def test_sammelseite_nutzt_dms_js_und_liest_die_adresse_nicht(self):
        html = w.sammelseite()
        # dms.js (liest das Fragment) muss vor sammeldatei.js laufen: beide „defer“, also Reihenfolge im Kopf.
        dms, sammel = html.index('dms.js?v='), html.index('sammeldatei.js?v=')
        self.assertLess(dms, sammel)
        self.assertIn('window.dmsVersion.lies()', w.SAMMEL_SKRIPT)
        self.assertIn('window.dmsVersion.merke(', w.SAMMEL_SKRIPT)
        for verboten in ('location.search', 'location.hash', 'location.href', 'URLSearchParams', 'localStorage'):
            self.assertNotIn(verboten, w.SAMMEL_SKRIPT, verboten)

    def test_kein_skript_erwartet_die_version_als_query(self):
        for name, quelltext in (('dms.js', w.SKRIPT), ('sammeldatei.js', w.SAMMEL_SKRIPT)):
            self.assertIsNone(re.search(r"""get\(\s*['"]dms['"]\s*\)|[?&]dms=""", quelltext), name)
            # Query nur für Kategorie, Autor und Paketart (#165) (teilbare Filter), nie für die Version.
            for feld in re.findall(r"""\.(?:get|set)\(\s*['"]([^'"]+)['"]""", quelltext):
                self.assertIn(feld, {'kategorie', 'autor', 'art'}, (name, feld))

    def test_stand_haengt_auch_am_sammelskript(self):
        self.assertIn(f'sammeldatei.js?v={w.STAND}', w.sammelseite())



class BeispielDokumente(unittest.TestCase):
    """Katalogseite zeigt die Zahl der Beispiel-Dokumente neben der Zahl der Beispiele (Registry #137)."""

    def seite(self, inhalt: dict) -> str:
        v = {'version': '1.0.0', 'dms': '>=0.223.0', 'abhaengigkeiten': {}, 'inhalt': inhalt, 'code': False, 'archiv': 'archive/x.zip',
             'sha256': '0' * 64, 'groesse': 1, 'veroeffentlicht': '2026-11-08T00:00:00Z', 'quelle': '', 'readme': '', 'changelog': ''}
        p = {'id': 'probe_gibtsnicht', 'name': 'Probe', 'beschreibung': 'Test.', 'lizenz': 'MIT', 'autor': {'name': 'Lena', 'github': 'lena'}, 'aktuell': '1.0.0', 'versionen': [v]}
        return w.detail(p, [p])

    def test_mit_und_ohne_dokumente(self):
        h = self.seite({'mappentypen': [{'schluessel': 'a', 'name': 'A'}], 'sichten': [], 'beispiele': 2, 'beispieldokumente': 3})
        self.assertIn('2 Beispielmappen und 3 Beispiel-Dokumenten mit erfundenen Daten', h)
        self.assertIn('2 Beispielmappen (3 Dokumente)', h)
        h = self.seite({'mappentypen': [{'schluessel': 'a', 'name': 'A'}], 'sichten': [], 'beispiele': 2})
        self.assertIn('2 Beispielmappen mit erfundenen Daten', h)
        self.assertNotIn('Dokumente)', h)


if __name__ == '__main__':
    unittest.main()


class Uebersicht(unittest.TestCase):
    """Katalog-Übersicht (#165): Paketarten, „Für den Anfang“, Sprachen und Ergänzungen nicht in der ersten Übersicht."""

    def paket(self, pid, **v):
        x = {'version': '1.0.0', 'dms': '>=0.1.0', 'code': False, 'inhalt': {'mappentypen': [], 'sichten': [], 'beispiele': 0}}
        x.update(v)
        return {'id': pid, 'name': pid, 'beschreibung': 'Erster Satz. Zweiter Satz.', 'autor': {'name': 'A', 'github': 'a'},
                'aktuell': '1.0.0', 'versionen': [x]}

    def test_paketart(self):
        self.assertEqual(w.paketart(self.paket('basis')), 'grundlagen')
        self.assertEqual(w.paketart(self.paket('sprache_fr', sprache={'kennung': 'fr'})), 'sprachen')
        self.assertEqual(w.paketart(self.paket('texterkennung_fra', ergaenzt={'paket': 'texterkennung'})), 'ergaenzungen')
        self.assertEqual(w.paketart(self.paket('haus', inhalt={'mappentypen': [{'schluessel': 'x', 'name': 'X'}]})), 'vorlagen')
        self.assertEqual(w.paketart(self.paket('benachrichtigungen')), 'automatisierungen')
        self.assertEqual(w.paketart(self.paket('pdfa', code=True)), 'funktionen')

    def test_kachel_klein_und_versteckt(self):
        k = w.kachel(self.paket('texterkennung_fra', ergaenzt={'paket': 'texterkennung'}))
        self.assertIn('data-versteckt="1"', k)
        self.assertIn('>Erster Satz.<', k)
        self.assertNotIn('Zweiter Satz.</span>', k)
        self.assertNotIn('data-versteckt', w.kachel(self.paket('pdfa', code=True)))

    def test_empfohlen_nur_vorhandene(self):
        pakete = [self.paket('basis'), self.paket('haus')]
        self.assertEqual([p['id'] for p in w.empfohlen(pakete)], ['basis'])

    def test_uebersicht(self):
        pakete = [self.paket('basis'), self.paket('pdfa', code=True), self.paket('sprache_fr', sprache={'kennung': 'fr'})]
        h = w.uebersicht({'erstellt': '2026-11-10T10:00:00Z'}, pakete, 'de')
        self.assertIn('id="anfang"', h)
        self.assertEqual(h.count('href="paket/basis/"'), 2)  # einmal oben, einmal (versteckt) unter „Weitere Pakete“
        self.assertIn('data-anfang="1"', h)
        self.assertIn('<option value="sprachen">Sprachen (1)</option>', h)
        self.assertNotIn('value="code"', h)
        self.assertIn('data-ansicht="liste"', h)


class WasMitkommt(unittest.TestCase):
    """„Was mitkommt“ (#115, #164) mit den echten Paketen Vermietung, Haushalt, Basis und Trennblatt."""

    @classmethod
    def setUpClass(cls):
        import yaml
        cls.pakete = []
        for pid in ('basis', 'haushalt', 'haus', 'vermietung', 'trennblatt', 'benachrichtigungen'):
            m = yaml.safe_load((w.WURZEL / 'pakete' / pid / 'manifest.yaml').read_text(encoding='utf-8'))
            v = {'version': m['version'], 'dms': m['dms'], 'abhaengigkeiten': m.get('abhaengigkeiten') or {}, 'code': bool(m.get('code')),
                 'inhalt': {'mappentypen': [], 'sichten': [], 'beispiele': 0}, 'archiv': 'archive/x.zip', 'sha256': '0' * 64, 'groesse': 1,
                 'veroeffentlicht': '2026-11-10T00:00:00Z', 'quelle': '', 'readme': '', 'changelog': ''}
            cls.pakete.append({'id': pid, 'name': m['name'], 'beschreibung': m['beschreibung'], 'lizenz': 'MIT',
                               'autor': {'name': 'Lena', 'github': 'lena'}, 'aktuell': m['version'], 'versionen': [v]})
        cls.nach_id = {p['id']: p for p in cls.pakete}

    def seite(self, pid):
        return w.detail(self.nach_id[pid], self.pakete)

    def test_feldzeile_im_neuen_stil(self):
        index = w.alle_typen(self.pakete)
        z = w.feldzeile({'key': 'v', 'label': 'Hausverwaltung', 'typ': 'referenz', 'ziel': 'basis:organisation', 'verweisart': 'bezug', 'pflicht': True},
                        'vermietung', index)
        self.assertIn('<strong>Hausverwaltung</strong><span class="art">Verweis</span><span class="pflicht">Pflicht</span>', z)
        self.assertIn('<a href="../basis/#typ-organisation">Organisation</a> <span class="leise">(Basis)</span> · Bezug', z)
        self.assertNotIn('(Verweis', z)  # keine Klammern um die Art wie früher

    def test_zusammenhaenge_paketuebergreifend(self):
        h = self.seite('basis')
        organisation = h[h.index('id="typ-organisation"'):]
        organisation = organisation[:organisation.index('</details>')]
        self.assertIn('Wird verwendet von:', organisation)
        self.assertIn('href="../vermietung/#typ-mietobjekt"', organisation)
        h = self.seite('vermietung')
        self.assertIn('Verweist auf:', h)
        self.assertIn('href="#typ-mietobjekt"', h)  # eigener Typ als Sprungmarke

    def test_mappentyp_erst_mit_beschreibung(self):
        h = self.seite('vermietung')
        self.assertRegex(h, r'<details class="typ" id="typ-mietobjekt"><summary><strong>Mietobjekt</strong> <span class="leise klein">\d+ Felder</span>'
                            r'<span class="typtext leise">Ein vermietetes Haus')

    def test_automatisierung_in_klartext(self):
        index = w.alle_typen(self.pakete)
        a = {'name': 'X', 'wenn': {'art': 'datum', 'typ': 'mietvertrag', 'feld': 'ende', 'vorlauf': 60, 'einheit': 'tage', 'uhrzeit': '07:00'},
             'dann': [{'art': 'aufgabe', 'als': 'aufgabe', 'empfaenger': [{'art': 'ersteller'}], 'text': 't'}]}
        wenn, dann, ablauf = w.auto_zeilen(a, 'vermietung', index)
        self.assertEqual(wenn, "60 Tage vor „Ende“ (Mietvertrag), geprüft um 07:00")
        self.assertEqual(dann, "Aufgabe an die Person, die die Mappe angelegt hat")
        self.assertEqual(ablauf, 'einmal je Termin')
        a['wenn']['wiederholung'] = 12
        self.assertTrue(w.auto_zeilen(a, 'vermietung', index)[2].startswith('wiederkehrend (jährlich)'))
        z = {'name': 'Z', 'wenn': {'art': 'zeitplan', 'uhrzeit': '00:00', 'tage': [1, 2, 3, 4, 5, 6, 7]}, 'dann': [{'art': 'anmeldeschutz', 'was': 'sammel'}]}
        self.assertEqual(w.auto_zeilen(z, 'benachrichtigungen', index), ('täglich um 00:00', 'Sammelmeldung Anmeldeschutz senden', 'wiederkehrend nach Zeitplan'))

    def test_nur_automatisierungen_ohne_leere_spalten(self):
        h = self.seite('benachrichtigungen')
        self.assertNotIn('<h3>Mappentypen</h3>', h)
        self.assertIn('<h3>Automatisierungen</h3>', h)

    def test_einstellungen_bei_code(self):
        h = self.seite('trennblatt')
        self.assertIn('<h3>Einstellungen</h3>', h)
        self.assertIn('<strong>Barcode auf dem Trennblatt</strong><span class="art">Text</span>', h)
        self.assertIn('legt nichts in der Ablage an · ', h)
        self.assertIn('In Ablago unter Werkbank → Pakete → Trennblatt → Einstellungen.', h)
        g = w.einstellungen_block({'einstellungen': [{'abschnitt': 'Dienst', 'felder': [{'schluessel': 'k', 'name': 'Schlüssel', 'typ': 'geheim'},
                                                                                     {'schluessel': 'p', 'name': 'Prompt', 'typ': 'mehrzeilig'}]}]}, 'KI')
        self.assertIn('<span class="art">Geheim</span>', g)
        self.assertIn('<span class="art">Langtext</span>', g)
        self.assertIn('Adresse und Zugangsdaten trägst du selbst ein.', g)

    def test_ansicht_ohne_bedingungen_klappt_nicht_auf(self):
        h = w.sicht_baum([{'schluessel': 'a', 'name': 'Alle', 'typen': []}, {'schluessel': 'b', 'name': 'Offen', 'typen': [],
                          'bedingungen': [{'feld': 'x', 'operator': 'leer'}]}], {}, {})
        self.assertIn('<div class="sicht ohne"><strong>Alle</strong>', h)
        self.assertIn('<details class="sicht"><summary><strong>Offen</strong>', h)

    def test_vorgaben(self):
        index = w.alle_typen(self.pakete)
        h = w.vorgaben_block([{'kennung': 'strom', 'typ': 'vertrag', 'werte': {'name': 'Strom'}},
                              {'an': {'paket': 'x', 'kennung': 'y'}, 'dokumente': [{'datei': 'vorlagen/a.md'}]}], 'haushalt', index)
        self.assertIn('href="#typ-vertrag">Vertrag</a>: Strom', h)
        self.assertIn('1 Text-Vorlage zum Ausfüllen', h)

    def test_kurzanleitung(self):
        self.assertEqual(w.kurzanleitung({'kurzanleitung': {'de': ['a', 'b', 'c']}}), ['a', 'b', 'c'])
        self.assertEqual(w.kurzanleitung({}), [])
        import pruefen
        self.assertTrue(pruefen.kurzanleitung_hinweise({'code': {'netz': []}}))
        self.assertEqual(pruefen.kurzanleitung_hinweise({'code': {'netz': []}, 'ergaenzt': {'paket': 'x'}}), [])
        self.assertEqual(pruefen.kurzanleitung_hinweise({'sprache': {'kennung': 'fr'}}), [])
        self.assertTrue(pruefen.kurzanleitung_hinweise({'kurzanleitung': {'de': ['a', 'b', 'c'], 'en': ['a', 'b']}}))
        self.assertEqual(pruefen.kurzanleitung_hinweise({'kurzanleitung': {'de': ['a', 'b', 'c']}}), [])


class Zusammenhaenge(unittest.TestCase):
    """Diagramm als Inline-SVG (#115 Punkt 4): beim Bauen erzeugt, nichts von Dritten, Farben aus der Seite."""

    def index(self):
        t = lambda pid, s, name, felder=(): {'schluessel': s, 'name': name, 'paket': pid, 'paketname': pid.title(), 'felder': list(felder)}
        return {
            'basis:organisation': t('basis', 'organisation', 'Organisation'),
            'basis:ablageort': t('basis', 'ablageort', 'Ablageort'),
            'x:vertrag': t('x', 'vertrag', 'Vertrag', [{'key': 'o', 'typ': 'referenz', 'ziel': 'basis:organisation', 'verweisart': 'bezug'},
                                                      {'key': 'a', 'typ': 'referenz', 'ziel': 'basis:ablageort'}]),
            'x:zahlung': t('x', 'zahlung', 'Zahlung', [{'key': 'v', 'typ': 'referenz', 'ziel': 'vertrag', 'verweisart': 'zugehoerigkeit'},
                                                      {'key': 's', 'typ': 'referenz', 'ziel': 'zahlung'}]),
        }

    def test_kanten_und_reihen(self):
        import zusammenhang as z
        i = self.index()
        k = z.kanten_aller(i)
        self.assertEqual(k, {('x:vertrag', 'basis:organisation'): False, ('x:zahlung', 'x:vertrag'): True})  # ohne Ablageort, ohne sich selbst
        knoten, kanten = z.netz(i, ['x:vertrag', 'x:zahlung'])
        self.assertEqual(knoten, ['x:vertrag', 'x:zahlung', 'basis:organisation'])
        self.assertEqual(z.anordnung(knoten, kanten), {'basis:organisation': 0, 'x:vertrag': 1, 'x:zahlung': 2})

    def test_svg(self):
        import zusammenhang as z
        i = self.index()
        knoten, kanten = z.netz(i, ['x:vertrag', 'x:zahlung'])
        svg = z.zeichne(knoten, kanten, i, 'Titel', fokus='x', kennung='t')
        self.assertIn('<title id="t-titel">Titel</title>', svg)
        self.assertIn('class="kante gehoert"', svg)
        self.assertIn('class="kante bezug"', svg)
        self.assertIn('<g class="knoten fremd">', svg)
        self.assertNotIn('href', svg)          # nichts nachladen, keine Links im Bild
        self.assertNotIn('fill="#', svg)       # Farben nur über die Seite (hell/dunkel)
        self.assertNotIn('<script', svg)
        # Kreise brechen ab statt endlos zu laufen
        self.assertEqual(set(z.anordnung(['a', 'b'], {('a', 'b'): True, ('b', 'a'): False})), {'a', 'b'})

    def test_gesamtseite_mit_echten_paketen(self):
        WasMitkommt.setUpClass()
        h = w.zusammenhangseite(WasMitkommt.pakete)
        self.assertIn('<h1>Wie alles zusammenhängt</h1>', h)
        self.assertIn('<svg class="zusammenhang"', h)
        self.assertIn('verweisen außerdem', h)  # Ablageort getrennt genannt
        self.assertIn('href="../paket/vermietung/#typ-mietobjekt"', h)  # Textfassung
        self.assertIn('Zusammenhänge als Bild', w.detail(WasMitkommt.nach_id['vermietung'], WasMitkommt.pakete))
