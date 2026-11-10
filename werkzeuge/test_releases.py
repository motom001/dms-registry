"""Tests für werkzeuge/releases.py und die Release-Adressen in werkzeuge/katalog.py (#156, #133) – ohne Netz."""
import hashlib, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import katalog  # noqa: E402
import releases  # noqa: E402
import sammeldatei  # noqa: E402


class FalschesGitHub:
    """Nachbildung der Releases eines Repos."""

    def __init__(self):
        self.liste, self.angelegt, self.hochgeladen, self.n = [], [], [], 0

    def releases(self):
        return json.loads(json.dumps(self.liste))

    def anlegen(self, tag, name, text):
        self.n += 1
        r = {'id': self.n, 'tag_name': tag, 'name': name, 'body': text, 'assets': []}
        self.liste.append(r)
        self.angelegt.append(tag)
        return r

    def hochladen(self, release, name, daten):
        r = next(x for x in self.liste if x['id'] == release['id'])
        a = {'name': name, 'size': len(daten), 'digest': 'sha256:' + hashlib.sha256(daten).hexdigest(), 'download_count': 0}
        r['assets'].append(a)
        self.hochgeladen.append(name)
        return a


def stand(tmp: Path, versionen=('1.0.0', '1.1.0')) -> Path:
    """Ein Katalog mit einem Paket in mehreren Versionen und den Archiven auf „Pages“."""
    (tmp / 'archive').mkdir()
    vs = []
    for ver in reversed(versionen):
        daten = f'paket {ver}'.encode()
        (tmp / 'archive' / f'probe-{ver}.zip').write_bytes(daten)
        vs.append({'version': ver, 'dms': '>=0.200.0', 'abhaengigkeiten': {}, 'archiv': katalog.release_url('probe', ver),
                   'spiegel': f'archive/probe-{ver}.zip', 'sha256': hashlib.sha256(daten).hexdigest(), 'groesse': len(daten),
                   'changelog': 'https://example.org/CHANGELOG.md'})
    k = {'format': 1, 'pakete': [{'id': 'probe', 'name': 'Probe', 'versionen': vs}]}
    (tmp / 'katalog.json').write_text(json.dumps(k), encoding='utf-8')
    return tmp


class Releases(unittest.TestCase):
    def test_anlegen_einmal(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            self.assertEqual(releases.anlegen(stand(Path(t)), gh), [])
            self.assertEqual(sorted(gh.angelegt), ['probe-v1.0.0', 'probe-v1.1.0'])
            self.assertEqual(sorted(gh.hochgeladen), ['probe-1.0.0.zip', 'probe-1.1.0.zip'])
            # Zweiter Lauf: nichts Neues.
            self.assertEqual(releases.anlegen(Path(t), gh), [])
            self.assertEqual(len(gh.hochgeladen), 2)

    def test_geaenderte_release_datei(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            releases.anlegen(stand(Path(t)), gh)
            gh.liste[0]['assets'][0]['size'] += 1
            f = releases.anlegen(Path(t), gh)
            self.assertTrue(any('ändern sich nie' in x for x in f), f)

    def test_ohne_archiv(self):
        with tempfile.TemporaryDirectory() as t:
            ordner = stand(Path(t))
            (ordner / 'archive' / 'probe-1.0.0.zip').unlink()
            f = releases.anlegen(ordner, FalschesGitHub())
            self.assertTrue(any('weder Release-Datei' in x for x in f), f)

    def test_zaehlen(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            releases.anlegen(stand(Path(t)), gh)
            for r, n in zip(gh.liste, (7, 120)):
                r['assets'][0]['download_count'] = n
            releases.zaehlen(Path(t), gh)
            p = json.loads((Path(t) / 'katalog.json').read_text())['pakete'][0]
            self.assertEqual(p['downloads'], 127)
            self.assertEqual(sorted(v['downloads'] for v in p['versionen']), [7, 120])

    def test_ausduennen(self):
        with tempfile.TemporaryDirectory() as t:
            ordner = stand(Path(t), ('1.0.0', '1.1.0', '1.2.0'))
            gh = FalschesGitHub()
            releases.anlegen(ordner, gh)
            k = json.loads((ordner / 'katalog.json').read_text())
            k['pakete'][0]['versionen'][-1].pop('spiegel')  # 1.0.0 ohne Spiegel
            (ordner / 'katalog.json').write_text(json.dumps(k))
            (ordner / 'archive' / 'probe-1.2.0.zip').unlink()  # Spiegel fehlt – vom Release zurückholen
            self.assertEqual(releases.ausduennen(ordner, gh, hole=lambda url: b'paket 1.2.0'), [])
            self.assertEqual(sorted(p.name for p in (ordner / 'archive').iterdir()), ['probe-1.1.0.zip', 'probe-1.2.0.zip'])

    def test_ausduennen_nur_mit_release(self):
        with tempfile.TemporaryDirectory() as t:
            ordner = stand(Path(t))
            k = json.loads((ordner / 'katalog.json').read_text())
            for v in k['pakete'][0]['versionen']:
                v.pop('spiegel')
            (ordner / 'katalog.json').write_text(json.dumps(k))
            self.assertEqual(releases.ausduennen(ordner, FalschesGitHub()), [])
            self.assertEqual(len(list((ordner / 'archive').iterdir())), 2)  # kein Release – nichts gelöscht

    def test_groesse(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / 'a.bin').write_bytes(b'x' * 2 * 1048576)
            self.assertEqual(releases.groesse(Path(t), 3), [])
            self.assertTrue(releases.groesse(Path(t), 1))


class KatalogAdressen(unittest.TestCase):
    def test_release_und_spiegel(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(katalog, 'OHNE_BAU', True):
            self.assertEqual(katalog.baue(Path(tmp), False), [])
            k = json.loads((Path(tmp) / 'katalog.json').read_text(encoding='utf-8'))
        v = next(p for p in k['pakete'] if p['id'] == 'haus')['versionen'][0]
        self.assertEqual(v['archiv'], f'https://github.com/motom001/dms-registry/releases/download/haus-v{v["version"]}/haus-{v["version"]}.zip')
        self.assertEqual(v['spiegel'], f'archive/haus-{v["version"]}.zip')

    def test_spiegel_nur_die_letzten(self):
        vs = [{'version': x} for x in ('1.3.0', '1.2.0', '1.1.0', '1.0.0')]
        with mock.patch.object(katalog, 'SPIEGEL_VERSIONEN', 3):
            self.assertEqual(katalog.spiegeln(vs), {'1.3.0', '1.2.0', '1.1.0'})
        self.assertEqual(katalog.spiegeln(vs), {'1.3.0', '1.2.0', '1.1.0', '1.0.0'})

    def test_veroeffentlicht_ohne_archiv_auf_pages(self):
        """Liegt ein veröffentlichtes Archiv nicht mehr auf Pages, kommt es zur Prüfung vom Release."""
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(katalog, 'OHNE_BAU', True):
            katalog.baue(Path(tmp), False)
            archive = {p.name: p.read_bytes() for p in (Path(tmp) / 'archive').iterdir()}
            for p in (Path(tmp) / 'archive').iterdir():
                p.unlink()
            geholt = []

            def hole(url):
                geholt.append(url)
                return archive[url.rsplit('/', 1)[1]]
            with mock.patch.object(katalog, 'hole', hole):
                self.assertEqual(katalog.baue(Path(tmp), False), [])
            self.assertTrue(geholt and all(u.startswith(katalog.RELEASES) for u in geholt))
            self.assertFalse(any((Path(tmp) / 'archive').iterdir()))  # nichts neu geschrieben
            with mock.patch.object(katalog, 'hole', lambda url: b'anders'):
                f = katalog.baue(Path(tmp), False)
            self.assertTrue(any('Prüfsumme' in x for x in f), f)


class SammeldateiSpiegel(unittest.TestCase):
    def test_lokal(self):
        self.assertEqual(sammeldatei.lokal({'archiv': 'https://github.com/x.zip', 'spiegel': 'archive/a-1.0.0.zip'}), 'archive/a-1.0.0.zip')
        self.assertEqual(sammeldatei.lokal({'archiv': 'archive/a-1.0.0.zip'}), 'archive/a-1.0.0.zip')
        self.assertIsNone(sammeldatei.lokal({'archiv': 'https://github.com/x.zip'}))

    def test_nur_versionen_mit_spiegel(self):
        k = {'pakete': [{'id': 'probe', 'name': 'Probe', 'versionen': [
            {'version': '2.0.0', 'dms': '>=0.1.0', 'archiv': 'https://github.com/a.zip'},
            {'version': '1.0.0', 'dms': '>=0.1.0', 'archiv': 'https://github.com/b.zip', 'spiegel': 'archive/probe-1.0.0.zip'}]}]}
        self.assertEqual(sammeldatei.auswahl(k, ['probe'], None)[0]['version'], '1.0.0')


if __name__ == '__main__':
    unittest.main()
