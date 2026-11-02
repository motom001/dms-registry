"""Tests für die Kategorien des Katalogs (#84): Liste, Prüfung, katalog.json, Sammeldatei und Webseite.

    python3 -m unittest werkzeuge/test_kategorien.py
"""
import json, shutil, subprocess, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kategorien as k  # noqa: E402
import katalog  # noqa: E402
import pruefen  # noqa: E402
import sammeldatei  # noqa: E402

WURZEL = Path(__file__).resolve().parent.parent
IDS = {p.name for p in (WURZEL / 'pakete').iterdir() if p.is_dir()}


class Liste(unittest.TestCase):
    def setUp(self):
        self.daten = k.lade()

    def test_datei_gueltig_und_vollstaendig(self):
        self.assertEqual(k.fehler_gesamt(self.daten, IDS), [])
        for pid in sorted(IDS):
            self.assertEqual(k.fehler_des_pakets(self.daten, pid), [], pid)

    def test_feste_liste_aus_dem_issue(self):
        self.assertEqual(k.kennungen(self.daten), ['vorlagen', 'dateiformate', 'volltext', 'sprachen', 'ki', 'post', 'sicherung', 'entwickler'])
        self.assertEqual(k.namen(self.daten, 'de')['volltext'], 'Texterkennung und Volltext')
        self.assertEqual(k.namen(self.daten, 'en')['ki'], 'AI')
        self.assertEqual(k.von(self.daten, 'office_email'), ['dateiformate', 'volltext'])
        self.assertEqual(sorted(p for p in IDS if 'vorlagen' in k.von(self.daten, p)), ['basis', 'fahrzeuge', 'haus', 'haushalt', 'vermietung'])

    def test_fehler_je_paket(self):
        d = {'kategorien': [{'kennung': 'ki', 'de': 'KI', 'en': 'AI'}, {'kennung': 'post', 'de': 'Post', 'en': 'Mail'}],
             'pakete': {'a': ['ki', 'post', 'ki'], 'b': ['gibtsnicht'], 'c': [], 'd': 'ki'}}
        f = k.fehler_des_pakets(d, 'neu')
        self.assertEqual(len(f), 1)
        self.assertIn('Kategorie fehlt', f[0])
        self.assertIn('werkzeuge/kategorien.yaml', f[0])
        self.assertIn('neu: [<kennung>]', f[0])
        self.assertIn('ki, post', f[0])
        self.assertTrue(any('3 Kategorien' in x for x in k.fehler_des_pakets(d, 'a')))
        self.assertTrue(any('doppelt' in x for x in k.fehler_des_pakets(d, 'a')))
        self.assertTrue(any('unbekannte Kategorie „gibtsnicht“' in x for x in k.fehler_des_pakets(d, 'b')))
        self.assertTrue(any('0 Kategorien' in x for x in k.fehler_des_pakets(d, 'c')))
        self.assertTrue(any('braucht eine Liste' in x for x in k.fehler_des_pakets(d, 'd')))

    def test_fehler_der_liste(self):
        d = {'kategorien': [{'kennung': 'ki', 'de': 'KI', 'en': 'AI'}, {'kennung': 'ki', 'de': 'KI'}, {'kennung': 'Gross', 'de': 'x', 'en': 'y', 'farbe': 'rot'}],
             'pakete': {'weg': ['ki']}}
        f = k.fehler_gesamt(d, set())
        self.assertTrue(any('doppelt' in x for x in f))
        self.assertTrue(any('Name „en“ fehlt' in x for x in f))
        self.assertTrue(any('Kennung „Gross“ ungültig' in x for x in f))
        self.assertTrue(any('unbekannte Angabe farbe' in x for x in f))
        self.assertTrue(any('„weg“ gibt es unter pakete/ nicht' in x for x in f))


class Pruefen(unittest.TestCase):
    def test_nur_pakete_der_registry(self):
        # Ordner außerhalb von pakete/ (Tests, Vorlage) brauchen keine Kategorie.
        self.assertEqual(pruefen.pruefe_kategorien(WURZEL / 'vorlage'), [])
        self.assertEqual(pruefen.pruefe_kategorien(Path(tempfile.gettempdir()) / 'probe'), [])
        self.assertEqual(pruefen.pruefe_kategorien(WURZEL / 'pakete' / 'basis'), [])
        self.assertIn('Kategorie fehlt', pruefen.pruefe_kategorien(WURZEL / 'pakete' / 'gibtsnochnicht')[0])

    def test_neues_paket_ohne_eintrag(self):
        """Neues Paket unter pakete/ ohne Zeile in kategorien.yaml: pruefen.py schlägt mit klarer Meldung fehl."""
        with tempfile.TemporaryDirectory() as tmp:
            wurzel = Path(tmp)
            (wurzel / 'werkzeuge').mkdir()
            for d in ('pruefen.py', 'kategorien.py', 'kategorien.yaml', 'wasm.py'):
                shutil.copy(WURZEL / 'werkzeuge' / d, wurzel / 'werkzeuge' / d)
            shutil.copytree(WURZEL / 'schema', wurzel / 'schema')
            shutil.copytree(WURZEL / 'vorlage', wurzel / 'pakete' / 'neu_paket')
            m = wurzel / 'pakete' / 'neu_paket' / 'manifest.yaml'
            m.write_text(m.read_text(encoding='utf-8').replace('id: vorlage', 'id: neu_paket'), encoding='utf-8')
            lic = wurzel / 'pakete' / 'neu_paket' / 'LICENSE'
            lic.write_text(lic.read_text(encoding='utf-8').replace('<Name>', 'Test').replace('<Jahr>', '2026'), encoding='utf-8')
            r = subprocess.run([sys.executable, '-B', str(wurzel / 'werkzeuge/pruefen.py'), str(wurzel / 'pakete/neu_paket')], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn('Kategorie fehlt: in werkzeuge/kategorien.yaml', r.stdout)
            # Wie im Test des DMS: nur pruefen.py und die Schemas kopiert → keine Kategorien-Prüfung.
            for d in ('kategorien.py', 'kategorien.yaml'):
                (wurzel / 'werkzeuge' / d).unlink()
            r = subprocess.run([sys.executable, '-B', str(wurzel / 'werkzeuge/pruefen.py'), str(wurzel / 'pakete/neu_paket')], capture_output=True, text=True)
            self.assertNotIn('Kategorie', r.stdout)


class FesteZeit:
    @staticmethod
    def now(tz=None):
        return datetime(2026, 11, 2, 12, 0, 0, tzinfo=timezone.utc)

    fromisoformat = staticmethod(datetime.fromisoformat)


class Katalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.a = Path(cls.tmp.name) / 'a'
        cls.a.mkdir()
        with mock.patch.object(katalog, 'datetime', FesteZeit), mock.patch.object(katalog, 'OHNE_BAU', True):
            assert katalog.baue(cls.a, False) == []
        cls.roh = (cls.a / 'katalog.json').read_bytes()
        cls.json = json.loads(cls.roh)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_feld_je_paket(self):
        nach_id = {p['id']: p for p in self.json['pakete']}
        self.assertEqual(set(nach_id), IDS)
        self.assertEqual(nach_id['office_email']['kategorien'], ['dateiformate', 'volltext'])
        self.assertEqual(list(nach_id['basis']), list(katalog.PAKETFELDER))
        # Pro Version kein Feld – Kategorien gehören zum Paket.
        self.assertNotIn('kategorien', nach_id['basis']['versionen'][0])

    def test_gleiche_eingabe_gleiche_bytes(self):
        # Noch einmal bauen (bisheriger Stand = eben gebaut) …
        with mock.patch.object(katalog, 'datetime', FesteZeit), mock.patch.object(katalog, 'OHNE_BAU', True):
            self.assertEqual(katalog.baue(self.a, False), [])
        self.assertEqual((self.a / 'katalog.json').read_bytes(), self.roh)
        # … und aus einem älteren Katalog ohne Kategorien, Felder in anderer Reihenfolge.
        b = Path(self.tmp.name) / 'b'
        shutil.copytree(self.a / 'archive', b / 'archive')
        alt = json.loads(self.roh)
        alt['pakete'] = [dict(reversed([(x, y) for x, y in p.items() if x != 'kategorien'])) for p in alt['pakete']]
        (b / 'katalog.json').write_text(json.dumps(alt), encoding='utf-8')
        with mock.patch.object(katalog, 'datetime', FesteZeit), mock.patch.object(katalog, 'OHNE_BAU', True):
            self.assertEqual(katalog.baue(b, False), [])
        self.assertEqual((b / 'katalog.json').read_bytes(), self.roh)

    def test_ohne_kategorie_kein_katalog(self):
        leer = {'kategorien': k.lade()['kategorien'], 'pakete': {}}
        with mock.patch.object(katalog.kategorien, 'lade', return_value=leer), mock.patch.object(katalog, 'OHNE_BAU', True):
            f = katalog.baue(Path(self.tmp.name) / 'c', True)
        self.assertTrue(any(x.startswith('basis: Kategorie fehlt') for x in f), f)

    def test_sammeldatei(self):
        daten = sammeldatei.erzeuge(self.a, ['office_email', 'haushalt'], None, '2026-11-02T12:00:00Z')
        self.assertEqual(sammeldatei.pruefe(daten, self.json), [])

    def test_webseite(self):
        import webseite
        aus = Path(self.tmp.name) / 'web'
        shutil.copytree(self.a, aus, ignore=shutil.ignore_patterns('archive'))
        with mock.patch.object(sys, 'argv', ['webseite.py', str(aus)]):
            webseite.main()
        start = (aus / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<option value="dateiformate">Dateiformate (2)</option>', start)
        self.assertIn('<option value="motom001">Thomas Meissner (14)</option>', start)
        self.assertIn('href="index.html?kategorie=volltext" data-kategorie="volltext">Texterkennung und Volltext</a>', start)
        en = (aus / 'en' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('href="../en/index.html?kategorie=ki" data-kategorie="ki">AI</a>', en)
        office = (aus / 'paket' / 'office_email' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<a class="weiter" href="../../index.html?kategorie=dateiformate">Ähnliche Pakete<span class="pfeil" aria-hidden="true">›</span></a>', office)
        self.assertIn('<a class="weiter" href="../../autor/motom001/">Weitere Pakete von Thomas Meissner', office)
        self.assertNotIn('Alle Pakete von', office)
        # „Braucht“ und „Erweiterungen dafür“ bleiben ohne Pfeil.
        haushalt = (aus / 'paket' / 'haushalt' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<h3>Braucht</h3>', haushalt)
        self.assertIn('<h3>Erweiterungen dafür</h3>', haushalt)


if __name__ == '__main__':
    unittest.main()
