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
            # Query nur für Kategorie und Autor (teilbare Filter), nie für die Version.
            for feld in re.findall(r"""\.(?:get|set)\(\s*['"]([^'"]+)['"]""", quelltext):
                self.assertIn(feld, {'kategorie', 'autor'}, (name, feld))

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
