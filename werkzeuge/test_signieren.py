"""Tests für signieren.py: Katalog signieren und prüfen, ohne Secret, Sammeldatei mit signiertem Katalog (#74).

    python3 -m unittest werkzeuge/test_signieren.py

Braucht openssl (ab 3.0) – auf den GitHub-Runnern vorhanden.
"""
import hashlib, io, json, os, shutil, subprocess, sys, tempfile, unittest, zipfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sammeldatei as s  # noqa: E402
import signieren as g  # noqa: E402

# Echter Signierschlüssel des Projekts (schluessel/signier.pub, im DMS server/src/projektschluessel.ts): Kennung und
# Fingerabdruck müssen hier genauso herauskommen wie im DMS und in SECURITY.md.
SIGNIER_PUB = (Path(__file__).resolve().parent.parent / 'schluessel' / 'signier.pub').read_text()


def neuer_schluessel(ordner: Path, name: str) -> tuple[Path, Path]:
    privat, oeffentlich = ordner / f'{name}.pem', ordner / f'{name}.pub'
    subprocess.run(['openssl', 'genpkey', '-algorithm', 'ed25519', '-out', str(privat)], check=True, capture_output=True)
    subprocess.run(['openssl', 'pkey', '-in', str(privat), '-pubout', '-out', str(oeffentlich)], check=True, capture_output=True)
    return privat, oeffentlich


def leise(f, *args):
    puffer = io.StringIO()
    with redirect_stdout(puffer):
        r = f(*args)
    return r, puffer.getvalue()


@unittest.skipUnless(shutil.which('openssl'), 'openssl fehlt')
class Signieren(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        self.ordner = self.t / 'site'
        (self.ordner / 'archive').mkdir(parents=True)
        self.signier, self.signier_pub = neuer_schluessel(self.t, 'signier')
        self.reserve, self.reserve_pub = neuer_schluessel(self.t, 'reserve')
        self.fremd, self.fremd_pub = neuer_schluessel(self.t, 'fremd')
        self.oeff = [str(self.signier_pub), str(self.reserve_pub)]
        archiv = io.BytesIO()
        with zipfile.ZipFile(archiv, 'w') as z:
            z.writestr('manifest.yaml', 'id: basis\nversion: 1.0.0\n')
        self.archiv = archiv.getvalue()
        (self.ordner / 'archive/basis-1.0.0.zip').write_bytes(self.archiv)
        katalog = {'format': 1, 'erstellt': '2026-11-02T10:00:00Z', 'quelle': s.REPO, 'signatur': None, 'pakete': [{
            'id': 'basis', 'name': 'Basis', 'versionen': [{'version': '1.0.0', 'dms': '>=0.60.0', 'abhaengigkeiten': {}, 'archiv': 'archive/basis-1.0.0.zip',
                                                          'sha256': hashlib.sha256(self.archiv).hexdigest(), 'groesse': len(self.archiv)}]}]}
        (self.ordner / 'katalog.json').write_text(json.dumps(katalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_kennung_wie_im_dms(self):
        self.assertEqual(g.kennung(SIGNIER_PUB), '6d868387314e64df')
        self.assertEqual(g.fingerabdruck(SIGNIER_PUB), '6d86 8387 314e 64df 715c a3bd 9856 58d5 f888 c0ea 7cab ac91 a43f 9b99 6052 e728')
        with self.assertRaises(g.Fehler):
            g.kennung('kein Schlüssel')

    def test_signieren_und_pruefen(self):
        r, aus = leise(g.main, ['signieren', str(self.ordner), '--schluessel', str(self.signier), *sum([['--oeffentlich', o] for o in self.oeff], [])])
        self.assertEqual(r, 0, aus)
        sig = json.loads((self.ordner / 'katalog.sig').read_text())
        self.assertEqual(sig['format'], 1)
        self.assertEqual(sig['verfahren'], 'ed25519')
        self.assertEqual(sig['erstellt'], '2026-11-02T10:00:00Z')
        self.assertEqual(sig['schluessel'], g.kennung(self.signier_pub.read_text()))
        self.assertEqual(leise(g.main, ['pruefen', str(self.ordner), '--oeffentlich', str(self.reserve_pub), '--oeffentlich', str(self.signier_pub)])[0], 0)
        # Ein Byte im Katalog geändert: ungültig.
        k = self.ordner / 'katalog.json'
        k.write_bytes(k.read_bytes().replace(b'"Basis"', b'"Basiz"'))
        r, aus = leise(g.main, ['pruefen', str(self.ordner), *sum([['--oeffentlich', o] for o in self.oeff], [])])
        self.assertEqual(r, 1)
        self.assertIn('passt zu keinem', aus)

    def test_reserveschluessel_und_fremder_schluessel(self):
        self.assertEqual(leise(g.main, ['signieren', str(self.ordner), '--schluessel', str(self.reserve), '--oeffentlich', self.oeff[0], '--oeffentlich', self.oeff[1]])[0], 0)
        r, aus = leise(g.main, ['signieren', str(self.ordner), '--schluessel', str(self.fremd), '--oeffentlich', self.oeff[0], '--oeffentlich', self.oeff[1]])
        self.assertEqual(r, 1)
        self.assertIn('passt zu keinem veröffentlichten', aus)

    def test_ohne_oeffentliche_schluessel_warnt(self):
        with mock.patch.object(g, 'SCHLUESSEL_ORDNER', self.t / 'leer'):
            r, aus = leise(g.main, ['signieren', str(self.ordner), '--schluessel', str(self.signier)])
        self.assertEqual(r, 0, aus)
        self.assertIn('Noch keine öffentlichen Schlüssel', aus)

    def test_ohne_secret_bleibt_gruen_und_loescht_alte_signatur(self):
        (self.ordner / 'katalog.sig').write_text('{"alt": true}')
        with mock.patch.dict(os.environ, {'KATALOG_SIGNIERSCHLUESSEL': '', 'GITHUB_ACTIONS': 'true'}):
            r, aus = leise(g.main, ['signieren', str(self.ordner), '--schluessel-env', 'KATALOG_SIGNIERSCHLUESSEL'])
        self.assertEqual(r, 0)
        self.assertIn('::warning title=Katalog nicht signiert::', aus)
        self.assertFalse((self.ordner / 'katalog.sig').exists())

    def test_secret_aus_umgebung(self):
        pem = self.signier.read_text()
        with mock.patch.dict(os.environ, {'KATALOG_SIGNIERSCHLUESSEL': pem}):
            r, aus = leise(g.main, ['signieren', str(self.ordner), '--schluessel-env', 'KATALOG_SIGNIERSCHLUESSEL', '--oeffentlich', self.oeff[0]])
        self.assertEqual(r, 0, aus)
        self.assertNotIn('PRIVATE KEY', aus, 'der private Schlüssel erscheint nie in der Ausgabe')
        self.assertTrue((self.ordner / 'katalog.sig').exists())

    def test_schluesselwechsel_datei(self):
        neu, neu_pub = neuer_schluessel(self.t, 'neu')
        ziel = self.t / 'katalog.schluessel.sig'
        self.assertEqual(leise(g.main, ['signieren-datei', str(neu_pub), '--schluessel', str(self.signier), '--ziel', str(ziel)])[0], 0)
        g.pruefe(neu_pub.read_bytes(), ziel.read_bytes(), [self.signier_pub.read_text()])
        with self.assertRaises(g.Fehler):
            g.pruefe(neu_pub.read_bytes(), ziel.read_bytes(), [neu_pub.read_text()])

    def test_sammeldatei_enthaelt_signierten_katalog(self):
        leise(g.main, ['signieren', str(self.ordner), '--schluessel', str(self.signier), '--oeffentlich', self.oeff[0]])
        daten = s.erzeuge(self.ordner, ['basis'], None)
        z = zipfile.ZipFile(io.BytesIO(daten))
        self.assertEqual(z.read('katalog.json'), (self.ordner / 'katalog.json').read_bytes(), 'Byte für Byte')
        self.assertEqual(z.read('katalog.sig'), (self.ordner / 'katalog.sig').read_bytes())
        oeff = [self.signier_pub.read_text()]
        self.assertEqual(s.pruefe(daten), [])
        self.assertEqual(s.pruefe(daten, None, oeff), [])
        self.assertTrue(any('passt zu keinem' in f for f in s.pruefe(daten, None, [self.fremd_pub.read_text()])))
        # Ohne Signatur im Katalogordner: keine Kopie, und wer eine Signatur verlangt, bekommt einen Fehler.
        (self.ordner / 'katalog.sig').unlink()
        ohne = s.erzeuge(self.ordner, ['basis'], None)
        self.assertNotIn('katalog.json', zipfile.ZipFile(io.BytesIO(ohne)).namelist())
        self.assertTrue(any('nicht signiert' in f for f in s.pruefe(ohne, None, oeff)))


if __name__ == '__main__':
    unittest.main()
