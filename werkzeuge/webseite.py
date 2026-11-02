#!/usr/bin/env python3
"""
Baut die Katalog-Webseite aus katalog.json und den Paketordnern – Pakete ansehen wie im App Store.

    python3 werkzeuge/webseite.py <ausgabe>      # Ausgabeordner mit katalog.json (nach katalog.py)

Im Ausgabeordner entstehen:

    index.html                   Übersicht: Kacheln je Paket, Suche, Filter (Konfiguration / mit Code)
    en/index.html                dieselbe Übersicht auf Englisch (Umschalter „Deutsch · English“ oben)
    paket/<id>/index.html        Detailseite: README, was angelegt wird, Rechte, Changelog, Versionen
    stil.css, dms.js             Aussehen wie die Handbücher; „In meinem DMS installieren“

Die Adresse des eigenen DMS merkt sich die Seite nur im Browser (localStorage); sie sendet nichts an
das DMS und speichert keine Zugangsdaten. Der Knopf öffnet <dms>/werkbank/pakete?installieren=<id>@<version>.

Sprachen (#54): Die festen Texte von Übersicht und Seitenrahmen stehen gebündelt in TEXTE (deutsch und englisch).
Paketseiten und Pakettexte aus den Manifesten bleiben vorerst deutsch (Mehrsprachigkeit: dms #357). Ohne
JavaScript lesbar: Jede Sprache ist eine eigene erzeugte Seite, der Umschalter ist ein normaler Link.

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


# Feste Texte der Übersicht und des Seitenrahmens, je Sprache an einer Stelle (#54). Werte mit HTML sind als
# solches markiert (*_html); alle anderen werden beim Einsetzen maskiert. Deutsch ist führend.
REGISTRY = 'https://github.com/motom001/dms-registry'
SPRACHEN = {'de': '', 'en': 'en/'}  # Sprache → Ordner ihrer Übersicht (relativ zur Wurzel der Webseite)
TEXTE = {
    'de': {
        'name': 'Deutsch',
        'sprachwahl': 'Sprache',
        'marke': 'DMS-Pakete',
        'beschreibung': 'Pakete für das DMS: fertige Mappentypen und Sichten',
        'handbuecher': 'Handbücher',
        'registry': 'Registry',
        'registry_url': REGISTRY,
        'dms_adresse': 'DMS-Adresse',
        'dialog_titel': 'Adresse deines DMS',
        'dialog_html': 'Zum Beispiel <code>https://dms.example.de</code> oder <code>http://192.168.1.20:3000</code>. Die Adresse bleibt nur in diesem Browser; die Seite sendet nichts an dein DMS.',
        'dialog_fehler': 'Bitte eine Adresse mit http:// oder https:// angeben.',
        'speichern': 'Speichern und öffnen',
        'abbrechen': 'Abbrechen',
        'regeln': 'Regeln für Pakete',
        'regeln_url': f'{REGISTRY}/blob/main/REGELN.md',
        'titel': 'Pakete für das DMS',
        'einleitung_html': 'Fertige Mappentypen und Sichten für dein <a href="https://github.com/motom001/dms">DMS</a> – Open Source und vom DMS-Projekt freigegeben. Installieren unter <strong>Werkbank → Pakete</strong> oder direkt von hier.',
        'hinweis_html': '',
        'suche': 'Paket suchen …',
        'suche_label': 'Pakete durchsuchen',
        'art': 'Art',
        'alle': 'Alle Pakete',
        'konfiguration': 'Konfiguration',
        'mit_code': 'Mit Code',
        'kachel_code': 'mit Code',
        'keine': 'Kein Paket gefunden.',
        'stand': 'Stand',
        'anzahl': ('Paket', 'Pakete'),
        'datum': '%d.%m.%Y',
    },
    'en': {
        'name': 'English',
        'sprachwahl': 'Language',
        'marke': 'DMS packages',
        'beschreibung': 'Packages for the DMS: ready-made Mappe types and views',
        'handbuecher': 'Manuals',
        'registry': 'Registry',
        'registry_url': f'{REGISTRY}/blob/main/README.en.md',
        'dms_adresse': 'DMS address',
        'dialog_titel': 'Address of your DMS',
        'dialog_html': 'For example <code>https://dms.example.com</code> or <code>http://192.168.1.20:3000</code>. The address stays in this browser only; this page sends nothing to your DMS.',
        'dialog_fehler': 'Please enter an address starting with http:// or https://.',
        'speichern': 'Save and open',
        'abbrechen': 'Cancel',
        'regeln': 'Rules for packages',
        'regeln_url': f'{REGISTRY}/blob/main/REGELN.en.md',
        'titel': 'Packages for the DMS',
        'einleitung_html': 'Ready-made Mappe types and views for your <a href="https://github.com/motom001/dms">DMS</a> – open source and approved by the DMS project. Install them in the DMS under <strong>Werkbank → Pakete</strong> (Workbench → Packages) or right from here.',
        'hinweis_html': '<strong>Note:</strong> Package names and descriptions come from the packages themselves and are in German for now, as are the package pages (multilingual package content will follow). Where the German and English wording differ, the German one applies.',
        'suche': 'Search packages …',
        'suche_label': 'Search packages',
        'art': 'Type',
        'alle': 'All packages',
        'konfiguration': 'Configuration',
        'mit_code': 'With code',
        'kachel_code': 'with code',
        'keine': 'No package found.',
        'stand': 'As of',
        'anzahl': ('package', 'packages'),
        'datum': '%Y-%m-%d',
    },
}


def datum(iso: str, sprache: str = 'de') -> str:
    try:
        return datetime.fromisoformat(iso.replace('Z', '+00:00')).strftime(TEXTE[sprache]['datum'])
    except ValueError:
        return iso


def seite(titel: str, inhalt: str, tiefe: int, beschreibung: str = '', sprache: str = 'de', umschalter: bool = False) -> str:
    """Seitenrahmen. Mit umschalter=True gibt es die Seite in allen SPRACHEN (die Übersicht): Links „Deutsch · English“."""
    vor = '../' * tiefe
    t = TEXTE[sprache]
    alternativ = wahl = ''
    if umschalter:
        alternativ = ''.join(f'\n  <link rel="alternate" hreflang="{s}" href="{vor}{o}index.html">' for s, o in SPRACHEN.items())
        wahl = (f'\n  <nav class="sprachen" aria-label="{e(t["sprachwahl"])}">' + ' · '.join(
            f'<a href="{vor}{o}index.html" lang="{s}" hreflang="{s}"' + (' aria-current="page"' if s == sprache else '') + f'>{e(TEXTE[s]["name"])}</a>'
            for s, o in SPRACHEN.items()) + '</nav>')
    start = f'{vor}{SPRACHEN[sprache]}index.html'
    return f'''<!doctype html>
<html lang="{sprache}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titel)}</title>
  <meta name="description" content="{e(beschreibung or t['beschreibung'])}">{alternativ}
  <link rel="stylesheet" href="{vor}stil.css">
  <script src="{vor}dms.js" defer></script>
</head>
<body>
  <header class="kopf"><a href="{start}" class="marke">{e(t['marke'])}</a>
    <nav><a href="https://motom001.github.io/dms/">{e(t['handbuecher'])}</a><a href="{t['registry_url']}">{e(t['registry'])}</a>
    <button type="button" class="textknopf" data-dms-adresse>{e(t['dms_adresse'])}</button></nav>{wahl}</header>
  <main>
{inhalt}
  </main>
  <dialog id="dms-dialog">
    <form method="dialog" class="stapel">
      <h2>{e(t['dialog_titel'])}</h2>
      <p class="leise">{t['dialog_html']}</p>
      <input type="url" id="dms-url" required placeholder="https://…" autocomplete="url">
      <p class="fehler" id="dms-fehler" hidden>{e(t['dialog_fehler'])}</p>
      <div class="knoepfe"><button value="ok" class="knopf primaer">{e(t['speichern'])}</button><button value="abbruch" class="textknopf" formnovalidate>{e(t['abbrechen'])}</button></div>
    </form>
  </dialog>
  <footer><a href="{t['regeln_url']}">{e(t['regeln'])}</a> · <a href="{vor}katalog.json">katalog.json</a></footer>
</body>
</html>
'''


def lies_yaml(ordner: Path, rel: str | None):
    if not rel or not (ordner / rel).exists():
        return []
    return yaml.safe_load((ordner / rel).read_text(encoding='utf-8')) or []


def kachel(p: dict, sprache: str = 'de') -> str:
    v = p['versionen'][0]
    code = 'code' if v['code'] else 'konfiguration'
    suche = ' '.join([p['id'], p['name'], p['beschreibung'], p['autor']['name']]).lower()
    vor = '../' * SPRACHEN[sprache].count('/')
    # Pakettexte sind deutsch – auch auf der englischen Übersicht als lang="de" ausgezeichnet (Vorlesen, Silbentrennung).
    de = '' if sprache == 'de' else ' lang="de"'
    mit_code = f' · {e(TEXTE[sprache]["kachel_code"])}' if v['code'] else ''
    return f'''      <a class="kachel" href="{vor}paket/{e(p['id'])}/" data-art="{code}" data-suche="{e(suche)}">
        <span class="symbol" aria-hidden="true">{e(p['name'][:1].upper())}</span>
        <span class="name"{de}>{e(p['name'])}</span>
        <span class="text"{de}>{e(p['beschreibung'])}</span>
        <span class="unter">{e(p['aktuell'])} · {e(p['autor']['name'])}{mit_code}</span>
      </a>'''


def uebersicht(katalog: dict, pakete: list, sprache: str) -> str:
    """Startseite (Übersicht) in einer Sprache; Texte aus TEXTE."""
    t = TEXTE[sprache]
    kacheln = '\n'.join(kachel(p, sprache) for p in pakete)
    hinweis = f'\n    <p class="hinweis">{t["hinweis_html"]}</p>' if t['hinweis_html'] else ''
    inhalt = f'''    <h1>{e(t['titel'])}</h1>
    <p class="leise">{t['einleitung_html']}</p>{hinweis}
    <div class="werkzeuge">
      <input type="search" id="suche" placeholder="{e(t['suche'])}" aria-label="{e(t['suche_label'])}">
      <select id="art" aria-label="{e(t['art'])}"><option value="">{e(t['alle'])}</option><option value="konfiguration">{e(t['konfiguration'])}</option><option value="code">{e(t['mit_code'])}</option></select>
    </div>
    <div class="kacheln">
{kacheln}
    </div>
    <p id="keine" class="leerhinweis" {'hidden' if pakete else ''}>{e(t['keine'])}</p>
    <p class="leise">{e(t['stand'])}: {datum(katalog.get('erstellt', ''), sprache)} · {len(pakete)} {e(t['anzahl'][0 if len(pakete) == 1 else 1])}</p>
'''
    return seite(t['marke'], inhalt, SPRACHEN[sprache].count('/'), sprache=sprache, umschalter=True)


# Wie im DMS (shared/src/pakete.ts, #449): dieselben Formulierungen in der Rechte-Vorschau vor der Installation.
HANDBUCH_PAKETE = 'https://motom001.github.io/dms/admin/aktuell/pakete/'
DMS_TYPEN = {'dms:ablageort': 'Ablageort', 'dms:rolle': 'Rolle', 'dms:post': 'Post'}
EREIGNISSE = {
    'post.angelegt': ('Neue Post ist angelegt', 'ereignis-post-angelegt'),
    'dokument.hochgeladen': ('Ein Dokument wurde hochgeladen', 'ereignis-dokument-hochgeladen'),
    'texterkennung.fertig': ('Die Texterkennung eines Dokuments ist fertig', 'ereignis-texterkennung-fertig'),
    'volltext.fertig': ('Der Volltext eines Dokuments ist da', 'ereignis-volltext-fertig'),
    'paket.einstellungen_geaendert': ('Die Einstellungen des Pakets wurden geändert', 'ereignis-einstellungen-geandert'),
}
DOKUMENT_RECHTE = {'lesen': 'Dokumente lesen', 'schreiben': 'Dokumente lesen und Volltext schreiben'}
SCHNITTSTELLEN = {
    'dms:vektoren': ('Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)', 'recht-vektoren', 'Vektoren zu Dokumenten'),
    # DMS #444, ab 0.124.0
    'dms:antworten': ('Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die das DMS mitgibt (dms:antworten)', 'recht-antworten', 'Fragen an die Ablage beantworten'),
}


def adressen(code: dict) -> list[str]:
    """Namen der Einstellungen vom Typ adresse (Dienst-Adresse, DMS #444) in den Abschnitten."""
    return [str(f.get('name') or f.get('schluessel')) for b in code.get('einstellungen') or [] if isinstance(b, dict) and 'liste' not in b
            for f in (b.get('felder') or []) if isinstance(f, dict) and f.get('typ') == 'adresse']


def netz_text(netz: list, adresse: list | None = None) -> str:
    """Netzwerkzugriff wie im DMS (#449, #444), Adressen als Code."""
    einst = [f'der Adresse aus der Einstellung „{e(a)}“ (trägst du ein und bestätigst sie)' for a in adresse or []]
    if not netz and not einst:
        return 'kein Zugriff auf Netzwerk und Internet'
    return 'Zugriff auf Netzwerk/Internet nur zu: ' + ', '.join([f'<code>{e(n)}</code>' for n in netz] + einst)


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
    for x in r.get('schnittstellen') or []:
        if x in SCHNITTSTELLEN:
            zeilen.append(e(SCHNITTSTELLEN[x][0]) + hilfe(SCHNITTSTELLEN[x][1], SCHNITTSTELLEN[x][2]))
    a = adressen(code)
    zeilen.append(netz_text(code.get('netz') or [], a)
                  + (hilfe('dienst-adresse', 'Dienst-Adresse') if a else hilfe('recht-netzwerk-und-internet', 'Zugriff auf Netzwerk und Internet')))
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
.sprachen { flex-basis: 100%; color: var(--leise); font-size: .92rem; }
.sprachen a[aria-current] { color: var(--tinte); font-weight: 600; text-decoration: none; }
.hinweis { background: var(--flaeche); border: 1px solid var(--linie); border-left: 4px solid var(--a); border-radius: 8px; padding: 10px 14px; }
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


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    ausgabe = Path(sys.argv[1]).resolve()
    katalog = json.loads((ausgabe / 'katalog.json').read_text(encoding='utf-8'))
    pakete = sorted(katalog['pakete'], key=lambda p: p['name'].lower())
    for sprache, ordner in SPRACHEN.items():
        (ausgabe / ordner).mkdir(parents=True, exist_ok=True)
        (ausgabe / ordner / 'index.html').write_text(uebersicht(katalog, pakete, sprache), encoding='utf-8')
    for p in pakete:
        ziel = ausgabe / 'paket' / p['id']
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / 'index.html').write_text(detail(p), encoding='utf-8')
    (ausgabe / 'stil.css').write_text(STIL.lstrip(), encoding='utf-8')
    (ausgabe / 'dms.js').write_text(SKRIPT.lstrip(), encoding='utf-8')
    print(f'Webseite: {len(pakete)} Pakete')


if __name__ == '__main__':
    main()
