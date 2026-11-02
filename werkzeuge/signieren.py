#!/usr/bin/env python3
"""
Signiert den Katalog (Ed25519 über die exakten Bytes von katalog.json) und prüft Signaturen (#74, motom001/dms#594).

    python3 werkzeuge/signieren.py signieren <ordner> --schluessel <privat.pem> [--oeffentlich <x.pub> …]
    python3 werkzeuge/signieren.py signieren <ordner> --schluessel-env KATALOG_SIGNIERSCHLUESSEL   # in der CI
    python3 werkzeuge/signieren.py pruefen <ordner> [--oeffentlich <x.pub> …]
    python3 werkzeuge/signieren.py signieren-datei <datei> --schluessel <privat.pem> --ziel <datei.sig>
    python3 werkzeuge/signieren.py fingerabdruck <x.pub> [<y.pub> …]

signieren schreibt <ordner>/katalog.sig und prüft sie sofort mit den öffentlichen Schlüsseln – ohne --oeffentlich
mit schluessel/*.pub dieses Repositorys. Der Signierschlüssel muss zu einem davon passen; liegen dort noch keine,
prüft es mit dem zum Signierschlüssel gehörenden öffentlichen Schlüssel und warnt.

Mit --schluessel-env ohne Inhalt (kein Secret, z. B. in Forks) signiert es nicht, löscht eine alte katalog.sig
(sie passte nicht mehr zum neuen Katalog), warnt deutlich und endet ohne Fehler.

katalog.sig:  {"format": 1, "verfahren": "ed25519", "schluessel": "<kennung>", "signatur": "<base64>", "erstellt": "<ISO>"}

Kennung und Fingerabdruck: SHA-256 über die 32 Bytes des öffentlichen Schlüssels, hexadezimal; Kennung = die ersten
16 Zeichen, Fingerabdruck = alle 64 in Vierergruppen. Das DMS rechnet genauso (server/src/katalogsignatur.ts).

Braucht: openssl (ab 3.0; auf den GitHub-Runnern vorhanden). Der private Schlüssel wird nie ausgegeben.
"""
import base64, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
SCHLUESSEL_ORDNER = WURZEL / 'schluessel'
KATALOG, SIGNATUR = 'katalog.json', 'katalog.sig'
# SPKI-Kopf eines öffentlichen Ed25519-Schlüssels; danach folgen die 32 Bytes des Schlüssels.
SPKI_KOPF = bytes.fromhex('302a300506032b6570032100')


class Fehler(Exception):
    pass


def roh(pem: str) -> bytes:
    """Die 32 Bytes eines öffentlichen Ed25519-Schlüssels (PEM, SPKI)."""
    zeilen = [z.strip() for z in pem.strip().splitlines()]
    if not zeilen or zeilen[0] != '-----BEGIN PUBLIC KEY-----' or zeilen[-1] != '-----END PUBLIC KEY-----':
        raise Fehler('kein öffentlicher Schlüssel im PEM-Format')
    der = base64.b64decode(''.join(zeilen[1:-1]))
    if len(der) != 44 or not der.startswith(SPKI_KOPF):
        raise Fehler('kein Ed25519-Schlüssel')
    return der[12:]


def kennung(pem: str) -> str:
    return hashlib.sha256(roh(pem)).hexdigest()[:16]


def fingerabdruck(pem: str) -> str:
    h = hashlib.sha256(roh(pem)).hexdigest()
    return ' '.join(h[i:i + 4] for i in range(0, 64, 4))


def openssl(*args: str, eingabe: bytes | None = None) -> bytes:
    try:
        r = subprocess.run(['openssl', *args], input=eingabe, capture_output=True, check=False)
    except FileNotFoundError as e:
        raise Fehler('openssl fehlt') from e
    if r.returncode != 0:
        # Nur die Meldung von openssl, nie Schlüsselinhalt.
        raise Fehler(f'openssl {args[0]}: {r.stderr.decode(errors="replace").strip().splitlines()[-1] if r.stderr else r.returncode}')
    return r.stdout


def oeffentlich_aus(privat: Path) -> str:
    return openssl('pkey', '-in', str(privat), '-pubout').decode()


def signiere_bytes(daten: bytes, privat: Path) -> bytes:
    with tempfile.TemporaryDirectory() as t:
        ein, aus = Path(t) / 'daten', Path(t) / 'sig'
        ein.write_bytes(daten)
        openssl('pkeyutl', '-sign', '-inkey', str(privat), '-rawin', '-in', str(ein), '-out', str(aus))
        sig = aus.read_bytes()
    if len(sig) != 64:
        raise Fehler('openssl hat keine Ed25519-Signatur geliefert')
    return sig


def gueltig(daten: bytes, sig: bytes, pem: str) -> bool:
    with tempfile.TemporaryDirectory() as t:
        d, s, k = Path(t) / 'daten', Path(t) / 'sig', Path(t) / 'pub.pem'
        d.write_bytes(daten); s.write_bytes(sig); k.write_text(pem)
        r = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(k), '-rawin', '-in', str(d), '-sigfile', str(s)], capture_output=True)
        return r.returncode == 0


def signaturdatei(daten: bytes, privat: Path, erstellt: str = '') -> tuple[bytes, str]:
    """Inhalt einer .sig-Datei und der zugehörige öffentliche Schlüssel."""
    pem = oeffentlich_aus(privat)
    sig = signiere_bytes(daten, privat)
    inhalt = {'format': 1, 'verfahren': 'ed25519', 'schluessel': kennung(pem), 'signatur': base64.b64encode(sig).decode(), 'erstellt': erstellt}
    return (json.dumps(inhalt, ensure_ascii=False, indent=2) + '\n').encode(), pem


def lies_signatur(roh_sig: bytes) -> dict:
    try:
        j = json.loads(roh_sig.decode('utf-8'))
        sig = base64.b64decode(j['signatur'], validate=True)
    except (ValueError, KeyError, TypeError) as e:
        raise Fehler(f'{SIGNATUR} ist kein gültiges Signaturformat') from e
    if j.get('format', 1) != 1 or j.get('verfahren', 'ed25519') != 'ed25519' or len(sig) != 64:
        raise Fehler(f'{SIGNATUR}: Format, Verfahren oder Länge stimmt nicht')
    return {**j, 'roh': sig}


def pruefe(daten: bytes, roh_sig: bytes, schluessel: list[str]) -> str:
    """Prüft eine Signatur gegen die erlaubten Schlüssel; liefert den Fingerabdruck des passenden, wirft sonst."""
    s = lies_signatur(roh_sig)
    for pem in sorted(schluessel, key=lambda p: kennung(p) != s.get('schluessel')):
        if gueltig(daten, s['roh'], pem):
            return fingerabdruck(pem)
    raise Fehler('Signatur passt zu keinem der öffentlichen Schlüssel')


def veroeffentlichte(dateien: list[str] | None) -> list[str]:
    pfade = [Path(d) for d in dateien] if dateien else sorted(SCHLUESSEL_ORDNER.glob('*.pub'))
    return [p.read_text(encoding='utf-8') for p in pfade]


def warnung(text: str):
    # GitHub zeigt ::warning:: als gelben Hinweis im Lauf; lokal ist es eine normale Zeile.
    print(f'::warning title=Katalog nicht signiert::{text}' if os.environ.get('GITHUB_ACTIONS') else f'! {text}')


def signieren(ordner: Path, privat: Path, oeffentlich: list[str] | None) -> str:
    daten = (ordner / KATALOG).read_bytes()
    erstellt = json.loads(daten).get('erstellt', '')
    if not erstellt:
        raise Fehler(f'{KATALOG} hat kein Feld „erstellt“ – das DMS braucht es gegen das Zurückdrehen auf ältere Kataloge')
    inhalt, eigener = signaturdatei(daten, privat, erstellt)
    erlaubt = veroeffentlichte(oeffentlich)
    if not erlaubt:
        warnung('Noch keine öffentlichen Schlüssel unter schluessel/*.pub – geprüft nur mit dem Schlüssel aus dem Secret.')
        erlaubt = [eigener]
    elif kennung(eigener) not in {kennung(p) for p in erlaubt}:
        raise Fehler('Der Signierschlüssel passt zu keinem veröffentlichten öffentlichen Schlüssel (schluessel/*.pub)')
    fp = pruefe(daten, inhalt, erlaubt)
    (ordner / SIGNATUR).write_bytes(inhalt)
    return fp


def signieren_aus_env(ordner: Path, name: str, oeffentlich: list[str] | None) -> str | None:
    wert = os.environ.get(name, '')
    if not wert.strip():
        alt = ordner / SIGNATUR
        if alt.exists():
            alt.unlink()
        warnung(f'Secret {name} fehlt (z. B. in einem Fork oder bevor der Maintainer es angelegt hat): Der Katalog wird OHNE Signatur veröffentlicht. '
                'Das DMS zeigt dann „nicht signiert“. Anleitung: README, Abschnitt „Katalog signieren“.')
        return None
    with tempfile.TemporaryDirectory() as t:
        datei = Path(t) / 'signier.pem'
        fd = os.open(datei, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(wert if wert.endswith('\n') else wert + '\n')
        try:
            return signieren(ordner, datei, oeffentlich)
        finally:
            datei.unlink(missing_ok=True)


def wert(args: list[str], name: str) -> str | None:
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args):
        raise Fehler(f'{name} braucht einen Wert')
    v = args[i + 1]
    del args[i:i + 2]
    return v


def werte(args: list[str], name: str) -> list[str]:
    erg = []
    while (v := wert(args, name)) is not None:
        erg.append(v)
    return erg


def main(argv: list[str]) -> int:
    args = list(argv)
    if not args:
        print(__doc__)
        return 2
    befehl = args.pop(0)
    try:
        oeffentlich = werte(args, '--oeffentlich') or None
        if befehl == 'signieren' and len(args) >= 1:
            privat, env = wert(args, '--schluessel'), wert(args, '--schluessel-env')
            if len(args) != 1 or bool(privat) == bool(env):
                print(__doc__)
                return 2
            ordner = Path(args[0])
            fp = signieren_aus_env(ordner, env, oeffentlich) if env else signieren(ordner, Path(privat), oeffentlich)
            if fp:
                print(f'✓ {ordner / SIGNATUR} geschrieben und geprüft (Schlüssel {fp})')
            return 0
        if befehl == 'pruefen' and len(args) == 1:
            ordner = Path(args[0])
            if not (ordner / SIGNATUR).exists():
                print(f'✗ {ordner / SIGNATUR} fehlt')
                return 1
            erlaubt = veroeffentlichte(oeffentlich)
            if not erlaubt:
                raise Fehler('keine öffentlichen Schlüssel (schluessel/*.pub oder --oeffentlich)')
            print(f'✓ Signatur gültig (Schlüssel {pruefe((ordner / KATALOG).read_bytes(), (ordner / SIGNATUR).read_bytes(), erlaubt)})')
            return 0
        if befehl == 'signieren-datei' and len(args) >= 1:
            privat, ziel = wert(args, '--schluessel'), wert(args, '--ziel')
            if len(args) != 1 or not privat or not ziel:
                print(__doc__)
                return 2
            daten = Path(args[0]).read_bytes()
            inhalt, pem = signaturdatei(daten, Path(privat))
            pruefe(daten, inhalt, [pem])
            Path(ziel).write_bytes(inhalt)
            print(f'✓ {ziel} geschrieben (signiert mit Schlüssel {fingerabdruck(pem)})')
            return 0
        if befehl == 'fingerabdruck' and args:
            for d in args:
                pem = Path(d).read_text(encoding='utf-8')
                print(f'{d}: Kennung {kennung(pem)}, Fingerabdruck {fingerabdruck(pem)}')
            return 0
    except (Fehler, OSError, ValueError) as e:
        print(f'✗ {e}')
        return 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
