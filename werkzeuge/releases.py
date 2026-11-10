#!/usr/bin/env python3
"""
Paketversionen als GitHub-Releases (#156) und GitHub Pages schlank halten (#133). Läuft im Workflow „Katalog
veröffentlichen“ nach werkzeuge/katalog.py und vor dem Signieren.

    python3 werkzeuge/releases.py anlegen <ausgabe>      fehlende Releases anlegen, Archive hochladen
    python3 werkzeuge/releases.py zaehlen <ausgabe>      Downloads je Version und Paket in katalog.json schreiben
    python3 werkzeuge/releases.py ausduennen <ausgabe>   auf Pages nur die Archive mit `spiegel` behalten
    python3 werkzeuge/releases.py groesse <ausgabe>      Größe der Seite melden, Fehler ab GRENZE_MB

Je Paketversion ein Release mit Tag <id>-v<version> und genau einer Datei <id>-<version>.zip – Byte für Byte das
Archiv aus dem Katalog. Im Repository ist „Immutable releases“ eingeschaltet: Ein veröffentlichtes Release lässt sich
nicht mehr ändern, sein Tag nie wiederverwenden. Deshalb erst als Entwurf anlegen, Datei hochladen und prüfen, dann
veröffentlichen; ein liegengebliebener Entwurf wird beim nächsten Lauf weiterverwendet. Je Lauf höchstens
RELEASES_HOECHSTENS neue Releases (Umgebung, Vorgabe 20) – Versionen ohne Release laden bis dahin weiter von Pages.
Releases ändern sich nie: Gibt es die Datei schon, muss sie zu Größe und Prüfsumme im Katalog
passen, sonst bricht das Werkzeug ab. Ablago lädt von dort (Feld `archiv`), GitHub zählt die Downloads selbst
(`download_count`); Ablago sendet dafür nichts. Ein Archiv auf Pages wird erst gelöscht, wenn seine Release-Datei da
ist.

`zaehlen` meldet außerdem einen Fehler, wenn es ein veröffentlichtes Release gibt, dessen Version im Katalog fehlt
(Schutz vor einem Lauf, der Versionen verliert – gh-pages hat keine Historie). Bewusst zurückgezogene Versionen stehen
in werkzeuge/zurueckgezogen.yaml; ihr Release wird von Hand gelöscht.

Braucht GITHUB_TOKEN (contents: write) und GITHUB_REPOSITORY; ohne Token: nur `groesse`.
"""
import hashlib, json, os, sys, time, urllib.parse, urllib.request

import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import katalog as k  # noqa: E402

API = 'https://api.github.com'
UPLOADS = 'https://uploads.github.com'
# GitHub Pages erlaubt 1 GB je Seite; vorher abbrechen (#133).
GRENZE_MB = 900


class GitHub:
    """Die paar Aufrufe der REST-API, die das Werkzeug braucht."""

    def __init__(self, repo: str, token: str, commit: str = 'main'):
        self.repo, self.token, self.commit = repo, token, commit

    # GitHub begrenzt Anfragen, die etwas anlegen (etwa 80 je Minute): beim ersten Lauf sind es über 270.
    PAUSE = 1.0

    def _anfrage(self, methode: str, url: str, daten: bytes | None = None, typ: str = 'application/json'):
        if methode != 'GET':
            time.sleep(self.PAUSE)
        r = urllib.request.Request(url, data=daten, method=methode, headers={
            'Authorization': f'Bearer {self.token}', 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'dms-registry-releases', 'Content-Type': typ})
        with urllib.request.urlopen(r, timeout=300) as a:
            return json.loads(a.read() or b'null')

    def releases(self) -> list[dict]:
        alle, seite = [], 1
        while True:
            teil = self._anfrage('GET', f'{API}/repos/{self.repo}/releases?per_page=100&page={seite}')
            alle += teil
            if len(teil) < 100:
                return alle
            seite += 1

    def anlegen(self, tag: str, name: str, text: str) -> dict:
        """Als Entwurf – erst `veroeffentlichen` macht das Release (unveränderlich) sichtbar."""
        body = {'tag_name': tag, 'target_commitish': self.commit, 'name': name, 'body': text, 'draft': True,
                'prerelease': False}
        return self._anfrage('POST', f'{API}/repos/{self.repo}/releases', json.dumps(body).encode())

    def veroeffentlichen(self, release: dict) -> dict:
        body = {'draft': False, 'make_latest': 'false'}
        return self._anfrage('PATCH', f'{API}/repos/{self.repo}/releases/{release["id"]}', json.dumps(body).encode())

    def hochladen(self, release: dict, name: str, daten: bytes) -> dict:
        url = f'{UPLOADS}/repos/{self.repo}/releases/{release["id"]}/assets?name={urllib.parse.quote(name)}'
        return self._anfrage('POST', url, daten, 'application/zip')


def lies_katalog(ausgabe: Path) -> dict:
    return json.loads((ausgabe / 'katalog.json').read_text(encoding='utf-8'))


def schreib_katalog(ausgabe: Path, katalog: dict):
    (ausgabe / 'katalog.json').write_text(json.dumps(katalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def versionen(katalog: dict):
    for p in katalog['pakete']:
        for v in p['versionen']:
            yield p, v, f'{p["id"]}-{v["version"]}.zip', k.tag(p['id'], v['version'])


def datei_passt(asset: dict, v: dict) -> bool:
    """Release-Datei gleich dem Archiv im Katalog? Größe immer, SHA-256, wenn GitHub sie nennt (`digest`)."""
    d = asset.get('digest') or ''
    return asset.get('size') == v['groesse'] and (not d.startswith('sha256:') or d[7:] == v['sha256'])


def anlegen(ausgabe: Path, gh, hoechstens: int | None = None) -> list[str]:
    """Fehlende Releases anlegen: Entwurf → Datei hochladen und prüfen → veröffentlichen. Versionen, die in diesem
    Lauf kein Release mehr bekommen, zeigen in katalog.json vorerst auf ihr Archiv auf Pages."""
    fehler: list[str] = []
    katalog = lies_katalog(ausgabe)
    vorhanden = {r['tag_name']: r for r in gh.releases()}
    neu = verschoben = 0
    for p, v, name, t in versionen(katalog):
        r = vorhanden.get(t)
        asset = next((a for a in (r or {}).get('assets') or [] if a['name'] == name), None)
        if r is not None and not r.get('draft'):
            # Veröffentlicht und damit unveränderlich: muss passen, nachbessern geht nicht.
            if not asset or not datei_passt(asset, v):
                fehler.append(f'{name}: veröffentlichtes Release ohne passende Datei (Größe/Prüfsumme) – lässt sich nicht mehr ändern, bitte von Hand prüfen')
            continue
        datei = ausgabe / 'archive' / name
        if hoechstens is not None and neu >= hoechstens:
            # Später weiter; bis dahin lädt Ablago diese Version von Pages (relative Adresse wie früher).
            if datei.exists():
                v['archiv'] = f'archive/{name}'
                v['spiegel'] = f'archive/{name}'
                verschoben += 1
            else:
                fehler.append(f'{name}: weder Release noch Archiv auf Pages')
            continue
        if asset and not datei_passt(asset, v):
            fehler.append(f'{name}: Entwurf mit falscher Datei – Entwurf {t} bitte von Hand löschen')
            continue
        if not asset:
            if not datei.exists():
                fehler.append(f'{name}: weder Release-Datei noch Archiv auf Pages – kann das Release nicht anlegen')
                continue
            daten = datei.read_bytes()
            if hashlib.sha256(daten).hexdigest() != v['sha256'] or len(daten) != v['groesse']:
                fehler.append(f'{name}: Archiv auf Pages passt nicht zu katalog.json')
                continue
            if r is None:
                text = (f'{p["name"]} {v["version"]} – Paket für Ablago (braucht Ablago {v["dms"]}).\n\n'
                        f'Installieren: Werkbank → Pakete → Dazuholen, oder https://catalog.ablago.app/paket/{p["id"]}/ · '
                        f'Änderungen: {v["changelog"]}\n\nDie Datei ist Byte für Byte das Archiv aus dem signierten Katalog '
                        f'(SHA-256 {v["sha256"]}).')
                r = gh.anlegen(t, f'{p["name"]} {v["version"]}', text)
                vorhanden[t] = r
            asset = gh.hochladen(r, name, daten)
            if not datei_passt(asset, v):
                fehler.append(f'{name}: hochgeladene Datei passt nicht (Größe/Prüfsumme) – Entwurf bleibt unveröffentlicht')
                continue
        gh.veroeffentlichen(r)
        neu += 1
    if verschoben:
        schreib_katalog(ausgabe, katalog)
    print(f'Releases: {neu} veröffentlicht, {verschoben} auf den nächsten Lauf verschoben (laden solange von Pages)')
    return fehler


def zurueckgezogen() -> set[str]:
    pfad = Path(__file__).resolve().parent / 'zurueckgezogen.yaml'
    return {str(x) for x in (yaml.safe_load(pfad.read_text(encoding='utf-8')) or [])} if pfad.exists() else set()


def zaehlen(ausgabe: Path, gh) -> list[str]:
    """Downloads je Version (Release-Datei) und je Paket (Summe) in katalog.json – vor dem Signieren."""
    katalog = lies_katalog(ausgabe)
    alle = gh.releases()
    zahl = {a['name']: int(a.get('download_count') or 0) for r in alle for a in r.get('assets') or []}
    # Sicherheit (PR #177): Ein veröffentlichtes Release, dessen Version im Katalog fehlt, heißt meist, dass ein Lauf
    # Versionen verloren hat – gh-pages hat keine Historie, aus der man sie zurückholen könnte.
    im_katalog = {t for _, _, _, t in versionen(katalog)}
    weg = sorted(r['tag_name'] for r in alle if not r.get('draft') and r['tag_name'] not in im_katalog and r['tag_name'] not in zurueckgezogen())
    if weg:
        return [f'Releases ohne Version im Katalog: {", ".join(weg)} – Version verloren? Bewusst zurückgezogen: in werkzeuge/zurueckgezogen.yaml eintragen']
    for p in katalog['pakete']:
        summe = 0
        for v in p['versionen']:
            n = zahl.get(f'{p["id"]}-{v["version"]}.zip')
            if n is None:
                v.pop('downloads', None)
            else:
                v['downloads'] = n
                summe += n
        p['downloads'] = summe
    schreib_katalog(ausgabe, katalog)
    print(f'Downloads: {sum(p["downloads"] for p in katalog["pakete"])} zusammen')
    return []


def ausduennen(ausgabe: Path, gh, hole=k.hole) -> list[str]:
    """Auf Pages nur Archive mit `spiegel` behalten; fehlende Spiegel vom Release zurückholen."""
    fehler: list[str] = []
    katalog = lies_katalog(ausgabe)
    dateien = {a['name']: a for r in gh.releases() for a in r.get('assets') or []}
    behalten, nach_name = set(), {}
    for p, v, name, _ in versionen(katalog):
        nach_name[name] = v
        if v.get('spiegel'):
            behalten.add(name)
            ziel = ausgabe / v['spiegel']
            if not ziel.exists():
                daten = hole(v['archiv'])
                if hashlib.sha256(daten).hexdigest() != v['sha256']:
                    fehler.append(f'{name}: Release-Datei passt nicht zur Prüfsumme – Spiegel nicht angelegt')
                    continue
                ziel.parent.mkdir(parents=True, exist_ok=True)
                ziel.write_bytes(daten)
    weg = 0
    for datei in sorted((ausgabe / 'archive').glob('*.zip')) if (ausgabe / 'archive').exists() else []:
        if datei.name in behalten:
            continue
        v = nach_name.get(datei.name)
        if v is None or datei.name not in dateien or not datei_passt(dateien[datei.name], v):
            # Kein Fehler: Lieber ein Archiv zu viel auf Pages als eines, das nirgends mehr liegt.
            print(f'Hinweis: {datei.name} hat keine passende Release-Datei – bleibt auf Pages')
            if 'GITHUB_ACTIONS' in os.environ:
                print(f'::warning title=Releases::{datei.name} hat keine passende Release-Datei – bleibt auf Pages')
            continue
        datei.unlink()
        weg += 1
    print(f'Pages: {len(behalten)} Archive behalten, {weg} entfernt (liegen am Release)')
    return fehler


def groesse(ausgabe: Path, grenze_mb: int = GRENZE_MB) -> list[str]:
    summe = sum(p.stat().st_size for p in ausgabe.rglob('*') if p.is_file() and '.git' not in p.relative_to(ausgabe).parts)
    print(f'Seite: {summe / 1048576:.1f} MB (Grenze {grenze_mb} MB, GitHub Pages höchstens 1 GB)')
    if summe > grenze_mb * 1048576:
        return [f'Die Seite ist {summe / 1048576:.0f} MB groß – mehr als {grenze_mb} MB. Weniger Spiegel behalten (SPIEGEL_VERSIONEN) oder Pakete verkleinern (#133).']
    return []


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ('anlegen', 'zaehlen', 'ausduennen', 'groesse'):
        print(__doc__)
        sys.exit(2)
    was, ausgabe = sys.argv[1], Path(sys.argv[2]).resolve()
    if was == 'groesse':
        fehler = groesse(ausgabe)
    else:
        token = os.environ.get('GITHUB_TOKEN')
        if not token:
            print('GITHUB_TOKEN fehlt')
            sys.exit(2)
        gh = GitHub(os.environ.get('GITHUB_REPOSITORY', 'motom001/dms-registry'), token, os.environ.get('GITHUB_SHA', 'main'))
        if was == 'anlegen':
            fehler = anlegen(ausgabe, gh, int(os.environ.get('RELEASES_HOECHSTENS') or 20) or None)
        else:
            fehler = {'zaehlen': zaehlen, 'ausduennen': ausduennen}[was](ausgabe, gh)
    for f in fehler:
        print(f'✗ {f}')
        if 'GITHUB_ACTIONS' in os.environ:
            print(f'::error title=Releases::{f}')
    sys.exit(1 if fehler else 0)


if __name__ == '__main__':
    main()
