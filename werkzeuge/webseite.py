#!/usr/bin/env python3
"""
Baut die Katalog-Webseite aus katalog.json und den Paketordnern – Pakete ansehen wie im App Store.

    python3 werkzeuge/webseite.py <ausgabe>      # Ausgabeordner mit katalog.json (nach katalog.py)

Im Ausgabeordner entstehen:

    index.html                   Übersicht: Kacheln je Paket, Suche, Filter (Konfiguration / mit Code)
    paket/<id>/index.html        Detailseite: README, was angelegt wird, Rechte, Changelog, Versionen
    sammeldatei.html             mehrere Pakete als eine Sammeldatei für ein DMS ohne Internet (motom001/dms#461)
    stil.css, dms.js             Aussehen wie die Handbücher; „In meinem DMS installieren“
    sammeldatei.js               stellt die Sammeldatei im Browser zusammen (nur aus katalog.json und archive/)

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


def seite(titel: str, inhalt: str, tiefe: int, beschreibung: str = '', skripte: tuple[str, ...] = ()) -> str:
    vor = '../' * tiefe
    mehr = ''.join(f'\n  <script src="{vor}{x}" defer></script>' for x in skripte)
    return f'''<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titel)}</title>
  <meta name="description" content="{e(beschreibung or 'Pakete für das DMS: fertige Mappentypen und Sichten')}">
  <link rel="stylesheet" href="{vor}stil.css">
  <script src="{vor}dms.js" defer></script>{mehr}
</head>
<body>
  <header class="kopf"><a href="{vor}index.html" class="marke">DMS-Pakete</a>
    <nav><a href="{vor}sammeldatei.html">Ohne Internet</a><a href="https://motom001.github.io/dms/">Handbücher</a><a href="https://github.com/motom001/dms-registry">Registry</a>
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


# Wie im DMS (shared/src/pakete.ts, #449): dieselben Formulierungen in der Rechte-Vorschau vor der Installation.
HANDBUCH_PAKETE = 'https://motom001.github.io/dms/admin/aktuell/pakete/'
DMS_TYPEN = {'dms:ablageort': 'Ablageort', 'dms:rolle': 'Rolle', 'dms:post': 'Post'}
EREIGNISSE = {
    'post.angelegt': ('Neue Post ist angelegt', 'ereignis-post-angelegt'),
    'dokument.hochgeladen': ('Ein Dokument wurde hochgeladen', 'ereignis-dokument-hochgeladen'),
    'texterkennung.fertig': ('Die Texterkennung eines Dokuments ist fertig', 'ereignis-texterkennung-fertig'),
    'paket.einstellungen_geaendert': ('Die Einstellungen des Pakets wurden geändert', 'ereignis-einstellungen-geandert'),
}
DOKUMENT_RECHTE = {'lesen': 'Dokumente lesen', 'schreiben': 'Dokumente lesen und Volltext schreiben'}


def netz_text(netz: list) -> str:
    """Netzwerkzugriff wie im DMS (#449), Adressen als Code."""
    if not netz:
        return 'kein Zugriff auf Netzwerk und Internet'
    return 'Zugriff auf Netzwerk/Internet nur zu: ' + ', '.join(f'<code>{e(n)}</code>' for n in netz)


def hilfe(anker: str, titel: str) -> str:
    """„?“ zur Erklärung im Administratorhandbuch des DMS."""
    return f' <a class="hilfe" href="{HANDBUCH_PAKETE}#{anker}" title="Erklärung: {e(titel)}" aria-label="Erklärung: {e(titel)} (Administratorhandbuch)">?</a>'


def rechte_text(code: dict, typen: dict | None = None) -> str:
    """Rechte und Netzwerkzugriff eines Pakets mit Code – so formuliert wie die Vorschau im DMS (#449)."""
    typen = typen or {}

    def name(t: str) -> str:
        if t == '*':
            return 'alle Mappentypen'
        if t in DMS_TYPEN:
            return DMS_TYPEN[t]
        if t in typen:
            return e(typen[t])
        return f'<code>{e(t)}</code>'

    r = code.get('rechte') or {}
    schreiben = list(dict.fromkeys(r.get('schreiben') or []))
    lesen = list(dict.fromkeys((r.get('lesen') or []) + schreiben))  # Schreiben setzt Lesen voraus (wie im DMS).
    zeilen = []
    if lesen:
        zeilen.append('Mappen lesen: ' + ', '.join(name(t) for t in lesen) + hilfe('recht-mappen-lesen', 'Mappen lesen'))
    if schreiben:
        zeilen.append('Mappen anlegen und ändern: ' + ', '.join(name(t) for t in schreiben) + hilfe('recht-mappen-anlegen-und-andern', 'Mappen anlegen und ändern'))
    dok = r.get('dokumente', 'keine')
    if dok in DOKUMENT_RECHTE:
        zeilen.append(DOKUMENT_RECHTE[dok] + hilfe('recht-dokumente', DOKUMENT_RECHTE[dok]))
    zeilen.append(netz_text(code.get('netz') or []) + hilfe('recht-netzwerk-und-internet', 'Zugriff auf Netzwerk und Internet'))
    ereignisse = code.get('ereignisse') or []
    if ereignisse:
        unter = ''.join(
            f'<li>{e(EREIGNISSE[x][0])}{hilfe(EREIGNISSE[x][1], EREIGNISSE[x][0])}</li>' if x in EREIGNISSE else f'<li><code>{e(x)}</code></li>'
            for x in ereignisse)
        zeilen.append(f'Reagiert auf diese Ereignisse:{hilfe("ereignisse", "Ereignisse")}<ul>{unter}</ul>')
    return '<ul class="rechte">' + ''.join(f'<li>{z}</li>' for z in zeilen) + '</ul>'


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
    rechte = rechte_text(m['code'], {t['schluessel']: t['name'] for t in typen if 'schluessel' in t}) if vorhanden and m.get('code') else '<p>Kein Code: Das Paket legt nur Mappentypen, Sichten und auf Wunsch Beispiele an.</p>'
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
    <section><h2>Rechte und Netzwerkzugriff</h2>{rechte}</section>
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
a.hilfe { display: inline-grid; place-items: center; width: 1.3em; height: 1.3em; margin-left: .3em; border: 1px solid var(--linie); border-radius: 50%; font-size: .8em; font-weight: 700; line-height: 1; color: var(--leise); text-decoration: none; vertical-align: .1em; }
a.hilfe:hover, a.hilfe:focus-visible { color: var(--a); border-color: var(--a); }
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


# Sammeldatei (motom001/dms#461): Auswahl, Abhängigkeiten und ZIP – alles im Browser aus katalog.json und archive/.
# Format und Prüfung wie werkzeuge/sammeldatei.py (Referenz) und schema/sammeldatei.schema.json.
SAMMEL_INHALT = r'''    <h1>Pakete ohne Internet</h1>
    <p class="leise">Kommt dein DMS nicht ins Internet? Wähle hier die Pakete aus und lade sie als <strong>eine Sammeldatei</strong> herunter.
      Im DMS lädst du sie unter <strong>Werkbank → Pakete → „Ohne Internet …“</strong> hoch (oder im Einrichtungsassistenten, Schritt „Pakete dazuholen“).
      Das DMS prüft jedes Paket gegen seine Prüfsumme und installiert dann eins nach dem anderen.</p>
    <noscript><p class="fehler">Die Sammeldatei entsteht in deinem Browser – dafür braucht die Seite JavaScript.</p></noscript>
    <form id="sammel" class="stapel" hidden>
      <div class="sammel-dms">
        <label for="dms-version"><strong>DMS-Version</strong> <span class="leise">– dazu passende Paketversionen</span></label>
        <input id="dms-version" inputmode="decimal" placeholder="z. B. 0.107.1" pattern="\d+\.\d+\.\d+" autocomplete="off" aria-describedby="dms-version-hilfe">
        <p id="dms-version-hilfe" class="leise klein">Steht im DMS unter „Über das DMS“. Vorgabe: die neueste Version. Leer: die neueste Version jedes Pakets.</p>
      </div>
      <fieldset class="sammel-pakete"><legend><strong>Pakete</strong> <span class="leise">– Abhängigkeiten kommen automatisch mit</span></legend>
        <ul id="sammel-liste" class="sammel-liste"></ul>
      </fieldset>
      <div id="sammel-probleme" class="hinweis-warn" role="status" hidden></div>
      <div class="knoepfe"><button type="submit" class="knopf primaer" id="sammel-los">Sammeldatei herunterladen</button><span id="sammel-zusammenfassung" class="leise"></span></div>
      <div id="sammel-ergebnis" role="status" aria-live="polite"></div>
    </form>
    <p id="sammel-laden" class="leise">Lade den Katalog …</p>
    <section><h2>So prüft das DMS die Sammeldatei</h2>
      <ul>
        <li>Die Sammeldatei enthält die Archive aus diesem Katalog Byte für Byte unverändert, dazu das Verzeichnis <code>sammeldatei.json</code> mit Größe und SHA-256 je Archiv. Diese Seite prüft jedes Archiv schon beim Zusammenstellen gegen <code>katalog.json</code>.</li>
        <li>Das DMS nimmt die Datei nur an, wenn jedes Archiv genau zu seiner Prüfsumme passt, nichts anderes darin liegt und jedes Paket gültig ist – sonst installiert es gar nichts. Kennt es den offiziellen Katalog schon, vergleicht es die Prüfsummen auch damit.</li>
        <li>Die Prüfsummen zeigen, dass die Datei vollständig und unverändert ist – nicht, wer sie zusammengestellt hat. Nimm deshalb nur eine Sammeldatei, die du selbst hier geladen hast. Zum Vergleich zeigt diese Seite den SHA-256 der ganzen Datei, das DMS nach dem Hochladen ebenfalls.</li>
        <li>Rechte von Paketen mit Code bestätigst du im DMS je Paket – eine Sammelbestätigung gibt es nicht.</li>
      </ul>
    </section>
'''


def sammelseite() -> str:
    return seite('Pakete ohne Internet – DMS-Pakete', SAMMEL_INHALT, 0, 'Mehrere Pakete als eine Sammeldatei für ein DMS ohne Internet', ('sammeldatei.js',))


SAMMEL_STIL = '''
[hidden] { display: none !important; }
.knopf:disabled { opacity: .5; cursor: not-allowed; }
.sammel-dms { display: grid; gap: 4px; max-width: 420px; }
.sammel-dms input { font: inherit; padding: 8px 10px; border: 1px solid var(--linie); border-radius: 8px; background: var(--flaeche); color: var(--tinte); min-width: 0; }
.klein { font-size: .9rem; margin: 0; }
fieldset.sammel-pakete { border: 0; padding: 0; margin: 0; min-width: 0; }
.sammel-liste { list-style: none; padding: 0; margin: 8px 0 0; display: grid; gap: 8px; }
.sammel-liste li { background: var(--flaeche); border: 1px solid var(--linie); border-radius: 10px; padding: 10px 12px; min-width: 0; }
.sammel-liste li.an { border-color: var(--a); }
.sammel-liste label { display: flex; gap: 10px; align-items: flex-start; cursor: pointer; }
.sammel-liste input { margin-top: 5px; flex: none; }
.sammel-liste .unter { display: block; color: var(--leise); font-size: .92rem; overflow-wrap: anywhere; }
.marke-mit { display: inline-block; font-size: .8rem; font-weight: 600; border-radius: 999px; padding: 1px 8px; background: var(--grund); border: 1px solid var(--linie); color: var(--leise); }
.hinweis-warn { border-left: 4px solid var(--warn); background: var(--flaeche); padding: 8px 12px; border-radius: 8px; }
.hinweis-warn ul { margin: 0; padding-left: 18px; }
#sammel-ergebnis code { overflow-wrap: anywhere; word-break: break-all; }
'''

SAMMEL_SKRIPT = r'''
// Sammeldatei im Browser (motom001/dms#461): wie werkzeuge/sammeldatei.py – Auswahl samt Abhängigkeiten,
// passend zur DMS-Version; jedes Archiv gegen katalog.json geprüft; ZIP mit sammeldatei.json, LIESMICH.txt
// und den Archiven unter pakete/. Es wird nichts hochgeladen; die Datei entsteht nur in diesem Browser.
(function () {
  var VORAUSWAHL = ['texterkennung'];
  var KATALOG_URL = 'https://raw.githubusercontent.com/motom001/dms-registry/gh-pages/katalog.json';
  var BEREICH = /^(>=|>|=|\^|~)?(\d+\.\d+\.\d+)( <(\d+\.\d+\.\d+))?$/;
  var VERSION = /^\d+\.\d+\.\d+$/;
  var katalog = null, gewaehlt = [];
  function teile(v) { return v.split('.').map(function (x) { return parseInt(x, 10) || 0; }); }
  function vergleiche(a, b) { var x = teile(a), y = teile(b); for (var i = 0; i < 3; i++) if (x[i] !== y[i]) return x[i] - y[i]; return 0; }
  function passt(v, bereich) {
    var m = BEREICH.exec((bereich || '').trim()); if (!m) return false;
    var op = m[1] || '=', basis = m[2], ober = m[4], c = vergleiche(v, basis), b = teile(basis), ok;
    if (op === '>=') ok = c >= 0; else if (op === '>') ok = c > 0;
    else if (op === '^') ok = c >= 0 && (b[0] > 0 ? vergleiche(v, (b[0] + 1) + '.0.0') < 0 : vergleiche(v, '0.' + (b[1] + 1) + '.0') < 0);
    else if (op === '~') ok = c >= 0 && vergleiche(v, b[0] + '.' + (b[1] + 1) + '.0') < 0;
    else ok = c === 0;
    return ok && (!ober || vergleiche(v, ober) < 0);
  }
  function dmsPasst(dms, bereich) { return !dms || passt(dms, bereich); }
  function paket(id) { return katalog.pakete.filter(function (p) { return p.id === id; })[0]; }
  function neueste(p, bereich, dms) {
    return p.versionen.slice().sort(function (a, b) { return vergleiche(b.version, a.version); })
      .filter(function (v) { return (!bereich || passt(v.version, bereich)) && dmsPasst(dms, v.dms); })[0];
  }
  // Wie auswahlMitAbhaengigkeiten im DMS: neueste passende Version, Abhängigkeiten mit, Abhängigkeiten zuerst.
  function plane(ids, dms) {
    var plan = {}, reihe = [], probleme = [];
    function name(id) { var p = paket(id); return p ? p.name : id; }
    function nimm(id, bereich, von) {
      if (plan[id]) {
        if (!von) plan[id].gewaehlt = true;
        else { if (plan[id].fuer.indexOf(von) < 0) plan[id].fuer.push(von); if (bereich && !passt(plan[id].v.version, bereich)) probleme.push('„' + name(von) + '“ braucht „' + plan[id].name + '“ ' + bereich + ', gewählt ist ' + plan[id].v.version + '.'); }
        return;
      }
      var p = paket(id);
      if (!p) { probleme.push('„' + name(von) + '“ braucht „' + id + '“ – das gibt es im Katalog nicht.'); return; }
      var v = neueste(p, bereich, dms);
      if (!v) { probleme.push(von ? '„' + name(von) + '“ braucht „' + p.name + '“ ' + bereich + '; dazu passt keine Version für DMS ' + dms + '.' : '„' + p.name + '“: keine Version passt zu DMS ' + dms + '.'); return; }
      plan[id] = { id: id, name: p.name, v: v, gewaehlt: !von, fuer: von ? [von] : [] };
      Object.keys(v.abhaengigkeiten || {}).forEach(function (a) { nimm(a, v.abhaengigkeiten[a], id); });
    }
    ids.forEach(function (id) { nimm(id, null, null); });
    var fertig = {}, unterwegs = {};
    function besuche(id) {
      if (fertig[id]) return true; if (unterwegs[id]) return false; unterwegs[id] = true;
      var ok = Object.keys(plan[id].v.abhaengigkeiten || {}).every(function (a) { return !plan[a] || besuche(a); });
      if (!ok) return false; delete unterwegs[id]; fertig[id] = true; reihe.push(plan[id]); return true;
    }
    if (!Object.keys(plan).every(besuche)) probleme.push('Die Abhängigkeiten bilden einen Kreis.');
    return { pakete: reihe, probleme: probleme, plan: plan };
  }
  function el(tag, attr, kinder) {
    var e = document.createElement(tag);
    Object.keys(attr || {}).forEach(function (k) { if (k === 'text') e.textContent = attr[k]; else if (k === 'className') e.className = attr[k]; else e.setAttribute(k, attr[k]); });
    (kinder || []).forEach(function (k) { if (k) e.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); });
    return e;
  }
  function dmsVersion() { var w = document.getElementById('dms-version').value.trim(); return VERSION.test(w) ? w : null; }
  function zeichne() {
    // Gewählte Pakete ohne passende Version für diese DMS-Version zählen nicht (die Wahl bleibt für eine andere Version).
    var dms = dmsVersion(), wirksam = gewaehlt.filter(function (id) { return neueste(paket(id), null, dms); });
    var r = plane(wirksam, dms), liste = document.getElementById('sammel-liste');
    liste.textContent = '';
    katalog.pakete.slice().sort(function (a, b) { return (VORAUSWAHL.indexOf(b.id) >= 0) - (VORAUSWAHL.indexOf(a.id) >= 0) || a.name.localeCompare(b.name, 'de'); }).forEach(function (p) {
      var v = neueste(p, null, dms), im = r.plan[p.id], mit = im && !im.gewaehlt, an = wirksam.indexOf(p.id) >= 0 || mit;
      var box = el('input', { type: 'checkbox', id: 'p-' + p.id });
      box.checked = an; box.disabled = !v || mit;
      box.addEventListener('change', function () { document.getElementById('sammel-ergebnis').textContent = ''; if (box.checked) gewaehlt.push(p.id); else gewaehlt = gewaehlt.filter(function (x) { return x !== p.id; }); zeichne(); });
      var zeige = (im && im.v) || v || p.versionen[0];
      var unter = !v ? 'Braucht DMS ' + p.versionen[0].dms + (dms ? ' – du hast ' + dms + '.' : '.') : (zeige.code ? 'Enthält Code – die Rechte bestätigst du im DMS für dieses Paket einzeln.' : 'Kein Code – legt Mappentypen und Ansichten an.');
      var empfohlen = VORAUSWAHL.indexOf(p.id) >= 0 && v;
      liste.appendChild(el('li', { className: an ? 'an' : '' }, [el('label', { for: 'p-' + p.id }, [box, el('span', {}, [
        el('strong', { text: p.name }), ' ', el('span', { className: 'leise', text: zeige.version }),
        mit ? ' ' : null, mit ? el('span', { className: 'marke-mit', text: 'kommt mit – gebraucht von ' + im.fuer.map(function (f) { return r.plan[f] ? r.plan[f].name : f; }).join(', ') }) : null,
        empfohlen ? ' ' : null, empfohlen ? el('span', { className: 'marke-mit', text: 'empfohlen' }) : null,
        el('span', { className: 'unter', text: p.beschreibung }), el('span', { className: 'unter', text: unter }),
      ])])]));
    });
    var pr = document.getElementById('sammel-probleme');
    pr.hidden = !r.probleme.length; pr.textContent = '';
    if (r.probleme.length) pr.appendChild(el('ul', {}, r.probleme.map(function (x) { return el('li', { text: x }); })));
    var groesse = r.pakete.reduce(function (n, x) { return n + x.v.groesse; }, 0);
    document.getElementById('sammel-zusammenfassung').textContent = r.pakete.length ? r.pakete.length + (r.pakete.length === 1 ? ' Paket' : ' Pakete') + ', etwa ' + (groesse / 1048576).toFixed(1).replace('.', ',') + ' MB' : 'Noch nichts gewählt.';
    document.getElementById('sammel-los').disabled = !r.pakete.length || r.probleme.length > 0;
    return r;
  }
  // ---- ZIP (gespeichert, ohne Kompression; die Archive sind schon komprimiert) ----
  var CRC = (function () { var t = new Uint32Array(256); for (var n = 0; n < 256; n++) { var c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
  function crc32(b) { var c = 0xffffffff; for (var i = 0; i < b.length; i++) c = CRC[(c ^ b[i]) & 0xff] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }
  function zip(dateien) {
    var teile = [], zentral = [], versatz = 0, enc = new TextEncoder();
    dateien.forEach(function (d) {
      var name = enc.encode(d.name), crc = crc32(d.daten), n = d.daten.length;
      var k = new DataView(new ArrayBuffer(30));
      k.setUint32(0, 0x04034b50, true); k.setUint16(4, 20, true); k.setUint16(6, 0x0800, true); k.setUint16(8, 0, true);
      k.setUint16(10, 0, true); k.setUint16(12, 33, true); k.setUint32(14, crc, true); k.setUint32(18, n, true); k.setUint32(22, n, true);
      k.setUint16(26, name.length, true); k.setUint16(28, 0, true);
      var z = new DataView(new ArrayBuffer(46));
      z.setUint32(0, 0x02014b50, true); z.setUint16(4, 20, true); z.setUint16(6, 20, true); z.setUint16(8, 0x0800, true); z.setUint16(10, 0, true);
      z.setUint16(12, 0, true); z.setUint16(14, 33, true); z.setUint32(16, crc, true); z.setUint32(20, n, true); z.setUint32(24, n, true);
      z.setUint16(28, name.length, true); z.setUint32(42, versatz, true);
      teile.push(k.buffer, name, d.daten); zentral.push(z.buffer, name);
      versatz += 30 + name.length + n;
    });
    var groesse = zentral.reduce(function (s, x) { return s + x.byteLength; }, 0);
    var e = new DataView(new ArrayBuffer(22));
    e.setUint32(0, 0x06054b50, true); e.setUint16(8, dateien.length, true); e.setUint16(10, dateien.length, true); e.setUint32(12, groesse, true); e.setUint32(16, versatz, true);
    return new Blob(teile.concat(zentral, [e.buffer]), { type: 'application/zip' });
  }
  function hex(buf) { return Array.prototype.map.call(new Uint8Array(buf), function (x) { return ('0' + x.toString(16)).slice(-2); }).join(''); }
  var LIESMICH = 'Sammeldatei für das DMS\n=======================\n\nDiese Datei enthält mehrere Pakete aus dem Paketkatalog des DMS-Projekts\n(https://motom001.github.io/dms-registry/) – für ein DMS ohne Internet.\n\nSo installierst du sie:\n  Werkbank → Pakete → „Ohne Internet …“ → Sammeldatei wählen\n  (oder im Einrichtungsassistenten, Schritt „Pakete dazuholen“).\n\nDas DMS prüft vorher jedes Paket gegen die Prüfsumme in sammeldatei.json und\ninstalliert dann Paket für Paket; Rechte von Paketen mit Code bestätigst du einzeln.\nEntpacken musst du nichts.\n';
  async function herunterladen(ev) {
    ev.preventDefault();
    var r = zeichne(), aus = document.getElementById('sammel-ergebnis'), knopf = document.getElementById('sammel-los');
    if (!r.pakete.length || r.probleme.length) return;
    if (!window.crypto || !crypto.subtle) { aus.textContent = 'Dein Browser kann hier keine Prüfsummen berechnen (nur über https).'; return; }
    knopf.disabled = true; aus.textContent = 'Lade und prüfe die Pakete …';
    try {
      var dateien = [], eintraege = [];
      for (var i = 0; i < r.pakete.length; i++) {
        var x = r.pakete[i], antwort = await fetch(x.v.archiv, { cache: 'no-store' });
        if (!antwort.ok) throw new Error(x.v.archiv + ': ' + antwort.status);
        var daten = new Uint8Array(await antwort.arrayBuffer());
        if (daten.length !== x.v.groesse || hex(await crypto.subtle.digest('SHA-256', daten)) !== x.v.sha256) throw new Error(x.name + ' ' + x.v.version + ': Prüfsumme passt nicht zum Katalog – abgebrochen.');
        var name = 'pakete/' + x.id + '-' + x.v.version + '.zip';
        dateien.push({ name: name, daten: daten });
        eintraege.push({ id: x.id, version: x.v.version, name: x.name, archiv: name, sha256: x.v.sha256, groesse: x.v.groesse, gewaehlt: x.gewaehlt });
      }
      var jetzt = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
      var vz = { format: 1, art: 'dms-sammeldatei', erstellt: jetzt, quelle: katalog.quelle || 'https://github.com/motom001/dms-registry', katalog: KATALOG_URL, dms: dmsVersion(), pakete: eintraege };
      var enc = new TextEncoder();
      var blob = zip([{ name: 'sammeldatei.json', daten: enc.encode(JSON.stringify(vz, null, 2) + '\n') }, { name: 'LIESMICH.txt', daten: enc.encode(LIESMICH) }].concat(dateien));
      var summe = hex(await crypto.subtle.digest('SHA-256', await blob.arrayBuffer()));
      var dateiname = 'dms-pakete-' + jetzt.slice(0, 10) + '.zip';
      var a = el('a', { href: URL.createObjectURL(blob), download: dateiname, className: 'knopf' }, ['Noch einmal speichern']);
      aus.textContent = '';
      aus.appendChild(el('p', {}, [el('strong', { text: dateiname }), ' mit ' + eintraege.map(function (e) { return e.name + ' ' + e.version; }).join(', ') + ' (' + (blob.size / 1048576).toFixed(1).replace('.', ',') + ' MB).']));
      aus.appendChild(el('p', { className: 'leise' }, ['SHA-256 der Datei: ', el('code', { text: summe }), ' – das DMS zeigt denselben Wert nach dem Hochladen.']));
      aus.appendChild(a);
      a.click();
    } catch (e) { aus.textContent = 'Das hat nicht geklappt: ' + e.message; }
    finally { knopf.disabled = false; zeichne(); }
  }
  async function start() {
    var form = document.getElementById('sammel');
    if (!form) return;
    try { katalog = await (await fetch('katalog.json', { cache: 'no-store' })).json(); }
    catch (e) { document.getElementById('sammel-laden').textContent = 'Der Katalog lässt sich nicht laden: ' + e.message; return; }
    var feld = document.getElementById('dms-version'), q = new URLSearchParams(location.search).get('dms');
    if (q && VERSION.test(q)) feld.value = q;
    else {
      // Vorgabe: die neueste DMS-Version (Releases auf GitHub); klappt das nicht, bleibt das Feld leer.
      fetch('https://api.github.com/repos/motom001/dms/releases/latest').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
        var v = j && String(j.tag_name || '').replace(/^v/, '');
        if (v && VERSION.test(v) && !feld.value) { feld.value = v; zeichne(); }
      }).catch(function () {});
    }
    gewaehlt = VORAUSWAHL.filter(function (id) { return paket(id); });
    feld.addEventListener('input', function () { document.getElementById('sammel-ergebnis').textContent = ''; zeichne(); });
    form.addEventListener('submit', herunterladen);
    document.getElementById('sammel-laden').hidden = true;
    form.hidden = false;
    zeichne();
  }
  start();
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
    (ausgabe / 'stil.css').write_text((STIL + SAMMEL_STIL).lstrip(), encoding='utf-8')
    (ausgabe / 'dms.js').write_text(SKRIPT.lstrip(), encoding='utf-8')
    (ausgabe / 'sammeldatei.html').write_text(sammelseite(), encoding='utf-8')
    (ausgabe / 'sammeldatei.js').write_text(SAMMEL_SKRIPT.lstrip(), encoding='utf-8')
    print(f'Webseite: {len(pakete)} Pakete')


if __name__ == '__main__':
    main()
