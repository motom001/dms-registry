#!/usr/bin/env python3
"""
Baut die Katalog-Webseite aus katalog.json und den Paketordnern – Pakete ansehen wie im App Store.

    python3 werkzeuge/webseite.py <ausgabe>      # Ausgabeordner mit katalog.json (nach katalog.py)

Im Ausgabeordner entstehen:

    index.html                   Übersicht: Kacheln je Paket, Suche, Filter (Konfiguration / mit Code)
    paket/<id>/index.html        Detailseite: README, was angelegt wird, Rechte, Changelog, Versionen
    stil.css, dms.js             Aussehen wie die Handbücher; „In meinem DMS installieren“

Die Adresse des eigenen DMS merkt sich die Seite nur im Browser (localStorage); sie sendet nichts an
das DMS und speichert keine Zugangsdaten. Der Knopf öffnet <dms>/werkbank/pakete?installieren=<id>@<version>.

Braucht: pip install pyyaml markdown
"""
import html, json, sys
from datetime import datetime
from pathlib import Path

import markdown
import yaml

WURZEL = Path(__file__).resolve().parent.parent
FELDTYPEN = {'text': 'Text', 'langtext': 'Langtext', 'formatiert': 'Formatierter Text', 'zahl': 'Zahl', 'betrag': 'Betrag', 'datum': 'Datum',
             'janein': 'Ja/Nein', 'auswahl': 'Auswahl', 'referenz': 'Verweis', 'passwort': 'Passwort'}
e = html.escape


def md(text: str) -> str:
    """Markdown ohne die eigene Hauptüberschrift; Überschriften eine Ebene tiefer (die Seite hat schon h1/h2)."""
    import re
    text = re.sub(r'\A\s*# [^\n]*\n', '', text)
    text = re.sub(r'^(#{1,5}) ', r'#\1 ', text, flags=re.M)
    return markdown.markdown(text, extensions=['tables', 'fenced_code'], output_format='html')


def datum(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace('Z', '+00:00')).strftime('%d.%m.%Y')
    except ValueError:
        return iso


def seite(titel: str, inhalt: str, tiefe: int, beschreibung: str = '') -> str:
    vor = '../' * tiefe
    return f'''<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titel)}</title>
  <meta name="description" content="{e(beschreibung or 'Pakete für das DMS: fertige Mappentypen und Sichten')}">
  <link rel="stylesheet" href="{vor}stil.css">
  <script src="{vor}dms.js" defer></script>
</head>
<body>
  <header class="kopf"><a href="{vor}index.html" class="marke">DMS-Pakete</a>
    <nav><a href="https://motom001.github.io/dms/">Handbücher</a><a href="https://github.com/motom001/dms-registry">Registry</a>
    <button type="button" class="textknopf" data-dms-adresse>DMS-Adresse</button></nav></header>
  <main>
{inhalt}
  </main>
  <dialog id="dms-dialog">
    <form method="dialog" class="stapel">
      <h2>Adresse deines DMS</h2>
      <p class="leise">Zum Beispiel <code>https://dms.example.de</code> oder <code>http://192.168.1.20:3000</code>. Die Adresse bleibt nur in diesem Browser; die Seite sendet nichts an dein DMS.</p>
      <input type="url" id="dms-url" required placeholder="https://…" autocomplete="url">
      <p class="fehler" id="dms-fehler" hidden>Bitte eine Adresse mit http:// oder https:// angeben.</p>
      <div class="knoepfe"><button value="ok" class="knopf primaer">Speichern und öffnen</button><button value="abbruch" class="textknopf" formnovalidate>Abbrechen</button></div>
    </form>
  </dialog>
  <footer><a href="https://github.com/motom001/dms-registry/blob/main/REGELN.md">Regeln für Pakete</a> · <a href="{vor}katalog.json">katalog.json</a></footer>
</body>
</html>
'''


def lies_yaml(ordner: Path, rel: str | None):
    if not rel or not (ordner / rel).exists():
        return []
    return yaml.safe_load((ordner / rel).read_text(encoding='utf-8')) or []


def kachel(p: dict) -> str:
    v = p['versionen'][0]
    code = 'code' if v['code'] else 'konfiguration'
    suche = ' '.join([p['id'], p['name'], p['beschreibung'], p['autor']['name']]).lower()
    return f'''      <a class="kachel" href="paket/{e(p['id'])}/" data-art="{code}" data-suche="{e(suche)}">
        <span class="symbol" aria-hidden="true">{e(p['name'][:1].upper())}</span>
        <span class="name">{e(p['name'])}</span>
        <span class="text">{e(p['beschreibung'])}</span>
        <span class="unter">{e(p['aktuell'])} · {e(p['autor']['name'])}{' · mit Code' if v['code'] else ''}</span>
      </a>'''


def rechte_text(code: dict) -> str:
    """Rechte und Netzadressen eines Pakets mit Code, verständlich formuliert."""
    r = code.get('rechte') or {}
    zeilen = []
    for t in r.get('lesen') or []:
        zeilen.append(f'darf Mappen vom Typ <code>{e(t)}</code> lesen')
    for t in r.get('schreiben') or []:
        zeilen.append(f'darf Mappen vom Typ <code>{e(t)}</code> ändern')
    dok = r.get('dokumente', 'keine')
    zeilen.append({'keine': 'sieht keine Dokumente', 'lesen': 'darf Dokumente lesen', 'schreiben': 'darf Dokumente lesen und ändern'}.get(dok, dok))
    netz = code.get('netz') or []
    zeilen.append('verbindet sich mit ' + ', '.join(f'<code>{e(n)}</code>' for n in netz) if netz else 'verbindet sich mit keiner Adresse im Internet')
    ereignisse = code.get('ereignisse') or []
    if ereignisse:
        zeilen.append('reagiert auf ' + ', '.join(f'<code>{e(x)}</code>' for x in ereignisse))
    return '<ul>' + ''.join(f'<li>{z}</li>' for z in zeilen) + '</ul>'


def detail(p: dict) -> str:
    v = p['versionen'][0]
    ordner = WURZEL / 'pakete' / p['id']
    vorhanden = (ordner / 'manifest.yaml').exists()
    m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8')) if vorhanden else {}
    readme = md((ordner / 'README.md').read_text(encoding='utf-8')) if (ordner / 'README.md').exists() else f'<p>{e(p["beschreibung"])}</p>'
    changelog = md((ordner / 'CHANGELOG.md').read_text(encoding='utf-8')) if (ordner / 'CHANGELOG.md').exists() else ''
    typen = lies_yaml(ordner, (m.get('inhalt') or {}).get('mappentypen')) if vorhanden else []
    sichten = lies_yaml(ordner, (m.get('inhalt') or {}).get('sichten')) if vorhanden else []
    if typen:
        typ_html = ''.join(
            f'<details><summary><strong>{e(t["name"])}</strong> – {len(t.get("felder", []))} Felder</summary><ul>'
            + ''.join(f'<li>{e(f["label"])} <span class="leise">({FELDTYPEN.get(f["typ"], f["typ"])}{", Pflicht" if f.get("pflicht") else ""})</span></li>' for f in t.get('felder', []))
            + '</ul></details>' for t in typen)
    else:
        typ_html = '<ul>' + ''.join(f'<li>{e(t["name"])}</li>' for t in v['inhalt']['mappentypen']) + '</ul>'
    namen = {s['schluessel']: s['name'] for s in sichten}
    sicht_html = '<ul>' + ''.join(f'<li>{e(s["name"])}' + (f' <span class="leise">(unter {e(namen.get(s["eltern"], s["eltern"]))})</span>' if s.get('eltern') else '') + '</li>' for s in sichten) + '</ul>' if sichten \
        else '<ul>' + ''.join(f'<li>{e(s["name"])}</li>' for s in v['inhalt']['sichten']) + '</ul>'
    abh = ', '.join(f'<a href="../{e(k)}/">{e(k)}</a> {e(b)}' for k, b in v['abhaengigkeiten'].items()) or 'keine'
    versionen = ''.join(
        f'<tr><td>{e(x["version"])}</td><td>{datum(x["veroeffentlicht"])}</td><td>{e(x["dms"])}</td>'
        f'<td><a href="../../{e(x["archiv"])}">Archiv</a></td><td><button type="button" class="textknopf" data-installieren="{e(p["id"])}@{e(x["version"])}">installieren</button></td></tr>'
        for x in p['versionen'])
    rechte = rechte_text(m['code']) if vorhanden and m.get('code') else '<p>Kein Code: Das Paket legt nur Mappentypen, Sichten und auf Wunsch Beispiele an.</p>'
    inhalt = f'''    <p class="zurueck"><a href="../../index.html">← Alle Pakete</a></p>
    <div class="paketkopf">
      <span class="symbol gross" aria-hidden="true">{e(p['name'][:1].upper())}</span>
      <div><h1>{e(p['name'])}</h1><p class="leise">{e(p['beschreibung'])}</p></div>
    </div>
    <div class="knoepfe"><button type="button" class="knopf primaer" data-installieren="{e(p['id'])}@{e(v['version'])}">In meinem DMS installieren</button>
      <a class="knopf" href="{e(v['quelle'])}">Quellcode</a></div>
    <dl class="eckdaten">
      <dt>Version</dt><dd>{e(v['version'])} vom {datum(v['veroeffentlicht'])}</dd>
      <dt>Autor</dt><dd>{e(p['autor']['name'])} (<a href="https://github.com/{e(p['autor']['github'])}">@{e(p['autor']['github'])}</a>)</dd>
      <dt>Lizenz</dt><dd>{e(p['lizenz'])}</dd>
      <dt>Nötige DMS-Version</dt><dd>{e(v['dms'])}</dd>
      <dt>Abhängigkeiten</dt><dd>{abh}</dd>
    </dl>
    <section><h2>Was angelegt wird</h2>
      <h3>Mappentypen</h3>{typ_html}
      <h3>Sichten</h3>{sicht_html}
      <p>{v['inhalt']['beispiele']} Beispiel-Mappen mit erfundenen Daten – nur, wenn du sie bei der Installation auswählst.</p>
    </section>
    <section><h2>Rechte und Netz</h2>{rechte}</section>
    <section class="readme"><h2>Beschreibung</h2>{readme}</section>
    {f'<section class="changelog"><h2>Änderungen</h2>{changelog}</section>' if changelog else ''}
    <section><h2>Versionen</h2>
      <div class="tabelle"><table><thead><tr><th>Version</th><th>Datum</th><th>DMS</th><th>Download</th><th></th></tr></thead><tbody>{versionen}</tbody></table></div>
    </section>
'''
    return seite(f'{p["name"]} – DMS-Pakete', inhalt, 2, p['beschreibung'])


STIL = '''
:root { --grund: #f6f7f8; --flaeche: #fff; --tinte: #1c2328; --leise: #5b6670; --linie: #dde2e6; --a: #00796b; --warn: #b26a00; }
@media (prefers-color-scheme: dark) { :root { --grund: #14181b; --flaeche: #1d2226; --tinte: #e8ecef; --leise: #9aa5ae; --linie: #2e353a; --a: #4db6ac; --warn: #ffb74d; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--grund); color: var(--tinte); font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
a { color: var(--a); }
.kopf { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; max-width: 980px; margin: 0 auto; padding: 14px 16px; }
.kopf nav { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.marke { font-weight: 700; font-size: 1.1rem; color: var(--tinte); text-decoration: none; }
main { max-width: 980px; margin: 0 auto; padding: 16px 16px 40px; }
h1 { font-size: 1.9rem; margin: 0 0 4px; }
.leise { color: var(--leise); }
.werkzeuge { display: flex; gap: 10px; flex-wrap: wrap; margin: 20px 0; }
.werkzeuge input, .werkzeuge select, dialog input { font: inherit; padding: 8px 10px; border: 1px solid var(--linie); border-radius: 8px; background: var(--flaeche); color: var(--tinte); min-width: 0; }
.werkzeuge input { flex: 1 1 240px; }
.kacheln { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
a.kachel { display: grid; grid-template-columns: auto 1fr; gap: 2px 12px; background: var(--flaeche); border: 1px solid var(--linie); border-radius: 12px; padding: 16px; color: inherit; text-decoration: none; }
a.kachel:hover, a.kachel:focus-visible { border-color: var(--a); }
.kachel .symbol { grid-row: span 3; }
.kachel .name { font-weight: 700; }
.kachel .text, .kachel .unter { grid-column: 2; color: var(--leise); font-size: .92rem; }
.symbol { display: inline-grid; place-items: center; width: 44px; height: 44px; border-radius: 12px; background: var(--a); color: #fff; font-weight: 700; font-size: 1.3rem; }
.symbol.gross { width: 64px; height: 64px; font-size: 1.8rem; border-radius: 16px; flex: none; }
.paketkopf { display: flex; gap: 16px; align-items: center; margin: 8px 0 16px; }
.knoepfe { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin: 12px 0; }
.knopf { display: inline-block; font: inherit; font-weight: 600; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--linie); background: var(--flaeche); color: var(--tinte); text-decoration: none; cursor: pointer; }
.knopf.primaer { background: var(--a); border-color: var(--a); color: #fff; }
.textknopf { font: inherit; background: none; border: 0; padding: 0; color: var(--a); cursor: pointer; font-weight: 600; }
.eckdaten { display: grid; grid-template-columns: max-content 1fr; gap: 6px 16px; background: var(--flaeche); border: 1px solid var(--linie); border-radius: 12px; padding: 16px; }
.eckdaten dt { color: var(--leise); }
.eckdaten dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
section { margin-top: 28px; }
section h2 { font-size: 1.3rem; border-bottom: 1px solid var(--linie); padding-bottom: 4px; }
details { background: var(--flaeche); border: 1px solid var(--linie); border-radius: 8px; padding: 8px 12px; margin: 6px 0; }
.tabelle { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--linie); }
.readme img { max-width: 100%; }
.readme table { display: block; overflow-x: auto; }
code { font-size: .92em; overflow-wrap: anywhere; }
.leerhinweis { color: var(--leise); }
dialog { border: 1px solid var(--linie); border-radius: 12px; background: var(--flaeche); color: var(--tinte); max-width: min(520px, calc(100vw - 32px)); }
dialog input { width: 100%; }
.stapel { display: flex; flex-direction: column; gap: 10px; }
.fehler { color: #c62828; margin: 0; }
footer { max-width: 980px; margin: 0 auto; padding: 16px; color: var(--leise); font-size: .9rem; }
@media (max-width: 560px) { .eckdaten { grid-template-columns: 1fr; } .eckdaten dt { margin-top: 6px; } }
'''

SKRIPT = '''
// Katalog-Webseite der DMS-Registry: Suche/Filter und „In meinem DMS installieren“.
// Die Adresse des eigenen DMS bleibt nur in diesem Browser (localStorage).
(function () {
  var SCHLUESSEL = 'dms-adresse';
  function lies() { try { return localStorage.getItem(SCHLUESSEL) || ''; } catch (e) { return ''; } }
  function merke(a) { try { localStorage.setItem(SCHLUESSEL, a); } catch (e) { /* nur jetzt */ } }
  function gueltig(a) { try { var u = new URL(a); return (u.protocol === 'http:' || u.protocol === 'https:') && !!u.host; } catch (e) { return false; } }
  function frage(danach) {
    var d = document.getElementById('dms-dialog'), i = document.getElementById('dms-url'), f = document.getElementById('dms-fehler');
    i.value = lies(); f.hidden = true;
    d.onclose = function () {
      if (d.returnValue !== 'ok') return;
      var a = i.value.trim().replace(/\\/+$/, '');
      if (!gueltig(a)) { f.hidden = false; d.showModal(); return; }
      merke(a); if (danach) danach(a);
    };
    d.showModal();
  }
  function oeffne(was) {
    var los = function (a) { location.href = a + '/werkbank/pakete?installieren=' + encodeURIComponent(was); };
    var a = lies();
    if (gueltig(a)) los(a); else frage(los);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-installieren]');
    if (b) { e.preventDefault(); oeffne(b.getAttribute('data-installieren')); return; }
    if (e.target.closest('[data-dms-adresse]')) { e.preventDefault(); frage(null); }
  });
  var suche = document.getElementById('suche'), art = document.getElementById('art');
  function filtern() {
    var q = (suche.value || '').trim().toLowerCase(), a = art.value, n = 0;
    document.querySelectorAll('.kachel').forEach(function (k) {
      var ok = (!q || k.dataset.suche.indexOf(q) >= 0) && (!a || k.dataset.art === a);
      k.hidden = !ok; if (ok) n++;
    });
    document.getElementById('keine').hidden = n > 0;
  }
  if (suche) { suche.addEventListener('input', filtern); art.addEventListener('change', filtern); }
})();
'''


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    ausgabe = Path(sys.argv[1]).resolve()
    katalog = json.loads((ausgabe / 'katalog.json').read_text(encoding='utf-8'))
    pakete = sorted(katalog['pakete'], key=lambda p: p['name'].lower())
    kacheln = '\n'.join(kachel(p) for p in pakete)
    index = f'''    <h1>Pakete für das DMS</h1>
    <p class="leise">Fertige Mappentypen und Sichten für dein <a href="https://github.com/motom001/dms">DMS</a> – Open Source und vom DMS-Projekt freigegeben. Installieren unter <strong>Werkbank → Pakete</strong> oder direkt von hier.</p>
    <div class="werkzeuge">
      <input type="search" id="suche" placeholder="Paket suchen …" aria-label="Pakete durchsuchen">
      <select id="art" aria-label="Art"><option value="">Alle Pakete</option><option value="konfiguration">Konfiguration</option><option value="code">Mit Code</option></select>
    </div>
    <div class="kacheln">
{kacheln}
    </div>
    <p id="keine" class="leerhinweis" {'hidden' if pakete else ''}>Kein Paket gefunden.</p>
    <p class="leise">Stand: {datum(katalog.get('erstellt', ''))} · {len(pakete)} {'Paket' if len(pakete) == 1 else 'Pakete'}</p>
'''
    (ausgabe / 'index.html').write_text(seite('DMS-Pakete', index, 0), encoding='utf-8')
    for p in pakete:
        ziel = ausgabe / 'paket' / p['id']
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / 'index.html').write_text(detail(p), encoding='utf-8')
    (ausgabe / 'stil.css').write_text(STIL.lstrip(), encoding='utf-8')
    (ausgabe / 'dms.js').write_text(SKRIPT.lstrip(), encoding='utf-8')
    print(f'Webseite: {len(pakete)} Pakete')


if __name__ == '__main__':
    main()
