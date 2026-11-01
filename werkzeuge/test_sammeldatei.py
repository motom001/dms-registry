"""Tests für sammeldatei.py: Auswahl mit Abhängigkeiten, Erzeugen und Prüfen (motom001/dms#461).

    python3 -m unittest werkzeuge/test_sammeldatei.py
"""
import hashlib, io, json, sys, tempfile, unittest, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sammeldatei as s  # noqa: E402


def archiv(inhalt: bytes) -> bytes:
    p = io.BytesIO()
    with zipfile.ZipFile(p, 'w') as z:
        z.writestr('manifest.yaml', inhalt)
    return p.getvalue()


class Sammeldatei(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ordner = Path(self.tmp.name)
        (self.ordner / 'archive').mkdir()
        pakete = []
        for pid, versionen in {
            'basis': [('1.1.1', '>=0.79.0', {}), ('1.0.0', '>=0.63.0', {})],
            'haushalt': [('1.0.2', '>=0.79.0', {'basis': '>=1.0.0'})],
            'texterkennung': [('1.0.0', '>=0.88.0', {})],
        }.items():
            vs = []
            for version, dms, abh in versionen:
                daten = archiv(f'id: {pid}\nversion: {version}\n'.encode())
                name = f'archive/{pid}-{version}.zip'
                (self.ordner / name).write_bytes(daten)
                vs.append({'version': version, 'dms': dms, 'abhaengigkeiten': abh, 'archiv': name, 'sha256': hashlib.sha256(daten).hexdigest(), 'groesse': len(daten)})
            pakete.append({'id': pid, 'name': pid.capitalize(), 'versionen': vs})
        self.katalog = {'format': 1, 'quelle': s.REPO, 'pakete': pakete}
        (self.ordner / 'katalog.json').write_text(json.dumps(self.katalog))

    def tearDown(self):
        self.tmp.cleanup()

    def test_auswahl(self):
        r = s.auswahl(self.katalog, ['haushalt', 'texterkennung'], '0.107.1')
        self.assertEqual([(p['id'], p['version'], p['gewaehlt']) for p in r], [('basis', '1.1.1', False), ('haushalt', '1.0.2', True), ('texterkennung', '1.0.0', True)])
        self.assertEqual([p['version'] for p in s.auswahl(self.katalog, ['basis'], '0.70.0')], ['1.0.0'])
        with self.assertRaisesRegex(ValueError, 'texterkennung: keine Version passt zu DMS 0.80.0'):
            s.auswahl(self.katalog, ['texterkennung'], '0.80.0')
        self.assertTrue(s.passt('0.2.5', '^0.2.0') and not s.passt('0.3.0', '^0.2.0') and s.passt('1.5.0', '>=1.0.0 <2.0.0'))

    def test_erzeugen_und_pruefen(self):
        daten = s.erzeuge(self.ordner, ['haushalt'], '0.107.1')
        self.assertEqual(s.pruefe(daten, self.katalog), [])
        z = zipfile.ZipFile(io.BytesIO(daten))
        self.assertEqual(sorted(z.namelist()), ['LIESMICH.txt', 'pakete/basis-1.1.1.zip', 'pakete/haushalt-1.0.2.zip', 'sammeldatei.json'])
        self.assertEqual(z.getinfo('pakete/basis-1.1.1.zip').compress_type, zipfile.ZIP_STORED)
        self.assertEqual(z.read('pakete/basis-1.1.1.zip'), (self.ordner / 'archive/basis-1.1.1.zip').read_bytes())

    def umgebaut(self, aendern) -> bytes:
        z = zipfile.ZipFile(io.BytesIO(s.erzeuge(self.ordner, ['haushalt'], None)))
        d = {n: z.read(n) for n in z.namelist()}
        vz = json.loads(d['sammeldatei.json'])
        aendern(d, vz)
        d['sammeldatei.json'] = json.dumps(vz).encode()
        p = io.BytesIO()
        with zipfile.ZipFile(p, 'w') as neu:
            for n, x in d.items():
                neu.writestr(n, x)
        return p.getvalue()

    def test_veraendert(self):
        def kippen(d, vz):
            b = bytearray(d['pakete/basis-1.1.1.zip']); b[10] ^= 1; d['pakete/basis-1.1.1.zip'] = bytes(b)
        self.assertTrue(any('Prüfsumme passt nicht zum Verzeichnis' in f for f in s.pruefe(self.umgebaut(kippen))))
        self.assertTrue(any('steht nicht im Verzeichnis' in f for f in s.pruefe(self.umgebaut(lambda d, vz: d.__setitem__('x.sh', b'')))))
        self.assertTrue(any('fehlt' in f for f in s.pruefe(self.umgebaut(lambda d, vz: d.pop('pakete/basis-1.1.1.zip')))))
        self.assertTrue(s.pruefe(self.umgebaut(lambda d, vz: vz['pakete'][0].update(archiv='../basis.zip'))))
        # Archiv und Verzeichnis passend geändert: nur der Abgleich mit katalog.json findet es.
        def tauschen(d, vz):
            neu = archiv(b'id: basis\nversion: 1.1.1\nboese: ja\n')
            d['pakete/basis-1.1.1.zip'] = neu
            vz['pakete'][0].update(sha256=hashlib.sha256(neu).hexdigest(), groesse=len(neu))
        self.assertEqual(s.pruefe(self.umgebaut(tauschen)), [])
        self.assertTrue(any('passt nicht zum Katalog' in f for f in s.pruefe(self.umgebaut(tauschen), self.katalog)))


if __name__ == '__main__':
    unittest.main()
