"""Tests für werkzeuge/releases.py und die Release-Adressen in werkzeuge/katalog.py (#156, #133) – ohne Netz."""
import hashlib, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import katalog  # noqa: E402
import releases  # noqa: E402
import sammeldatei  # noqa: E402


class FalschesGitHub:
    """Nachbildung der Releases eines Repos mit eingeschaltetem „Immutable releases“: An ein veröffentlichtes Release
    lässt sich nichts mehr hochladen."""

    def __init__(self):
        self.liste, self.angelegt, self.hochgeladen, self.veroeffentlicht, self.n = [], [], [], [], 0

    def releases(self):
        return json.loads(json.dumps(self.liste))

    def anlegen(self, tag, name, text):
        self.n += 1
        r = {'id': self.n, 'tag_name': tag, 'name': name, 'body': text, 'assets': [], 'draft': True}
        self.liste.append(r)
        self.angelegt.append(tag)
        return r

    def hochladen(self, release, name, daten):
        r = next(x for x in self.liste if x['id'] == release['id'])
        if not r['draft']:
            raise RuntimeError('422: Release ist unveränderlich')
        a = {'name': name, 'size': len(daten), 'digest': 'sha256:' + hashlib.sha256(daten).hexdigest(), 'download_count': 0}
        r['assets'].append(a)
        self.hochgeladen.append(name)
        return a

    def veroeffentlichen(self, release):
        r = next(x for x in self.liste if x['id'] == release['id'])
        r['draft'] = False
        self.veroeffentlicht.append(r['tag_name'])
        return r


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
            self.assertEqual(sorted(gh.veroeffentlicht), ['probe-v1.0.0', 'probe-v1.1.0'])
            self.assertTrue(all(not r['draft'] and r['assets'] for r in gh.liste))
            # Zweiter Lauf: nichts Neues.
            self.assertEqual(releases.anlegen(Path(t), gh), [])
            self.assertEqual(len(gh.hochgeladen), 2)

    def test_geaenderte_release_datei(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            releases.anlegen(stand(Path(t)), gh)
            gh.liste[0]['assets'][0]['size'] += 1
            f = releases.anlegen(Path(t), gh)
            self.assertTrue(any('lässt sich nicht mehr ändern' in x for x in f), f)

    def test_entwurf_wird_weiterverwendet(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            ordner = stand(Path(t), ('1.0.0',))
            gh.anlegen('probe-v1.0.0', 'Probe 1.0.0', '')  # Lauf brach nach dem Anlegen ab
            self.assertEqual(releases.anlegen(ordner, gh), [])
            self.assertEqual(len(gh.liste), 1)
            self.assertFalse(gh.liste[0]['draft'])
            self.assertEqual(gh.hochgeladen, ['probe-1.0.0.zip'])

    def test_veroeffentlicht_ohne_datei(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            ordner = stand(Path(t), ('1.0.0',))
            gh.veroeffentlichen(gh.anlegen('probe-v1.0.0', 'Probe 1.0.0', ''))
            f = releases.anlegen(ordner, gh)
            self.assertTrue(any('veröffentlichtes Release ohne passende Datei' in x for x in f), f)
            self.assertEqual(gh.hochgeladen, [])

    def test_hoechstens_je_lauf(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            ordner = stand(Path(t), ('1.0.0', '1.1.0', '1.2.0'))
            self.assertEqual(releases.anlegen(ordner, gh, hoechstens=2), [])
            self.assertEqual(len(gh.veroeffentlicht), 2)
            vs = {v['version']: v for v in json.loads((ordner / 'katalog.json').read_text())['pakete'][0]['versionen']}
            ohne = [v for v in vs.values() if not v['archiv'].startswith('https://')]
            self.assertEqual(len(ohne), 1)
            self.assertEqual(ohne[0]['archiv'], f'archive/probe-{ohne[0]["version"]}.zip')  # lädt vorerst von Pages

    def test_verlorene_version(self):
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            ordner = stand(Path(t))
            releases.anlegen(ordner, gh)
            k = json.loads((ordner / 'katalog.json').read_text())
            k['pakete'][0]['versionen'].pop()  # 1.0.0 fehlt plötzlich
            (ordner / 'katalog.json').write_text(json.dumps(k))
            f = releases.zaehlen(ordner, gh)
            self.assertTrue(any('probe-v1.0.0' in x for x in f), f)
            with mock.patch.object(releases, 'zurueckgezogen', lambda: {'probe-v1.0.0'}):
                self.assertEqual(releases.zaehlen(ordner, gh), [])

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

    def test_umzug_auf_neue_id(self):
        # Registry #173: Releases der früheren Id bleiben, ihre Downloads zählen beim neuen Paket mit.
        with tempfile.TemporaryDirectory() as t:
            gh = FalschesGitHub()
            releases.anlegen(stand(Path(t)), gh)
            for r, n in zip(gh.liste, (7, 120)):
                r['assets'][0]['download_count'] = n
            k = json.loads((Path(t) / 'katalog.json').read_text())
            neu = k['pakete'][0]
            neu.update({'id': 'probe.neu', 'ersetzt': ['probe']})
            neu['versionen'] = neu['versionen'][:0] + [dict(neu['versionen'][0], version='2.0.0')]
            (Path(t) / 'katalog.json').write_text(json.dumps(k))
            self.assertEqual(releases.zaehlen(Path(t), gh), [])
            self.assertEqual(json.loads((Path(t) / 'katalog.json').read_text())['pakete'][0]['downloads'], 127)
            neu.pop('ersetzt')
            (Path(t) / 'katalog.json').write_text(json.dumps(k))
            self.assertTrue(releases.zaehlen(Path(t), gh))  # ohne ersetzt: Versionen verloren

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
        self.assertEqual(katalog.spiegeln(vs), {'1.3.0'})  # Vorgabe: nur die aktuelle (#133)
        with mock.patch.object(katalog, 'SPIEGEL_VERSIONEN', None):
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


class Umzug(unittest.TestCase):
    """Registry #173: herausgeber an jedem Paket, die ersetzte Id fällt aus dem Katalog."""

    def test_herausgeber_und_ersetzt(self):
        pakete = {'texterkennung_fra': {'id': 'texterkennung_fra', 'versionen': []},
                  'texterkennung.fra': {'id': 'texterkennung.fra', 'versionen': []}, 'haus': {'id': 'haus', 'versionen': []}}
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(katalog, 'WURZEL', Path(tmp)):
            f = katalog.herausgeber_und_umzug(pakete, {'texterkennung.fra': {'ersetzt': 'texterkennung_fra'}, 'haus': {}})
        self.assertEqual(f, [])
        self.assertEqual(sorted(pakete), ['haus', 'texterkennung.fra'])
        self.assertEqual(pakete['texterkennung.fra']['ersetzt'], ['texterkennung_fra'])
        self.assertNotIn('ersetzt', pakete['haus'])
        self.assertEqual({p['herausgeber'] for p in pakete.values()}, {'app.ablago'})


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
