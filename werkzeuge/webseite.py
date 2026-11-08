#!/usr/bin/env python3
"""
Baut die Katalog-Webseite aus katalog.json und den Paketordnern – Pakete ansehen wie im App Store.

    python3 werkzeuge/webseite.py <ausgabe>      # Ausgabeordner mit katalog.json (nach katalog.py)

Im Ausgabeordner entstehen:

    index.html                   Übersicht: Kacheln je Paket, Suche, Filter (Konfiguration / mit Code)
    en/index.html                dieselbe Übersicht auf Englisch (Umschalter „Deutsch · English“ oben)
    paket/<id>/index.html        Detailseite: README, was angelegt wird, Rechte, Changelog, Versionen
    sammeldatei.html             mehrere Pakete als eine Sammeldatei für Ablago ohne Internet (motom001/dms#461)
    stil.css, dms.js             Aussehen wie die Handbücher; „In meinem Ablago installieren“
    sammeldatei.js               stellt die Sammeldatei im Browser zusammen (nur aus katalog.json und archive/)

Die Ablago-Version kommt aus Ablago nur im Fragment (#dms=<X.Y.Z>, motom001/dms#622), nie als Query: Das
Fragment geht an keinen Server und landet nicht im Zugriffsprotokoll. dms.js liest es auf jeder Seite (auch
sammeldatei.html), merkt die Version im localStorage (dms-version) und entfernt das Fragment aus der Adresse.

Die Adresse des eigenen Ablago merkt sich die Seite nur im Browser (localStorage); sie sendet nichts an
Ablago und speichert keine Zugangsdaten. Der Knopf öffnet <dms>/werkbank/pakete?installieren=<id>@<version>.

Sprachen (#54): Die festen Texte von Übersicht und Seitenrahmen stehen gebündelt in TEXTE (deutsch und englisch).
Paketseiten und Pakettexte aus den Manifesten bleiben vorerst deutsch (Mehrsprachigkeit: dms #357). Ohne
JavaScript lesbar: Jede Sprache ist eine eigene erzeugte Seite, der Umschalter ist ein normaler Link.

Braucht: pip install pyyaml markdown
"""
import hashlib, html, json, sys
from datetime import datetime
from pathlib import Path

import markdown
import yaml
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vorlagen import lies_kategorien, option as vorlagen_option, symbol_svg  # noqa: E402

KATEGORIEN = {k['kennung']: k for k in lies_kategorien()['kategorien']}
HANDBUCH_AKTUALISIEREN = 'https://help.ablago.app/admin/aktuell/aktualisieren/'

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
# Sprachpakete (Ablago #731, Registry #116): wie man eine Übersetzung verbessert, und die Sprachen mit Namen.
MITMACHEN_SPRACHE = 'https://help.ablago.app/entwickler/aktuell/pakete/#eine-sprache-beitragen'
SPRACHNAMEN = {'fr': 'Französisch', 'nl': 'Niederländisch', 'es': 'Spanisch', 'it': 'Italienisch', 'tr': 'Türkisch', 'pl': 'Polnisch',
               'pt': 'Portugiesisch', 'pt-BR': 'Portugiesisch (Brasilien)', 'da': 'Dänisch', 'sv': 'Schwedisch', 'cs': 'Tschechisch',
               'uk': 'Ukrainisch', 'ru': 'Russisch', 'ar': 'Arabisch', 'el': 'Griechisch', 'hu': 'Ungarisch', 'ro': 'Rumänisch'}


def sprach_hinweis(p: dict) -> str:
    """„Maschinell übersetzt – Verbesserungen willkommen“ mit Link bzw. „Geprüft von …“ (Ablago #731) – wie in Ablago."""
    s = p['versionen'][0].get('sprache') or {}
    if s.get('geprueft_von'):
        return f'<p class="hinweis">Geprüft von {e(s["geprueft_von"])}. Verbesserungen sind trotzdem willkommen: <a href="{e(uebersetzung_melden(p))}">Übersetzung verbessern</a>.</p>'
    if s.get('maschinell'):
        return (f'<p class="hinweis"><strong>Maschinell übersetzt</strong> – <a href="{e(MITMACHEN_SPRACHE)}">Verbesserungen willkommen</a>. '
                f'Einen falschen Text meldest du mit <a href="{e(uebersetzung_melden(p))}">Übersetzung verbessern</a> (auf GitHub).</p>')
    return ''


def uebersetzung_melden(p: dict) -> str:
    return f'{REGISTRY}/issues/new?template=uebersetzung.yml&title={quote("[" + p["name"] + "] ")}'
SPRACHEN = {'de': '', 'en': 'en/'}  # Sprache → Ordner ihrer Übersicht (relativ zur Wurzel der Webseite)
TEXTE = {
    'de': {
        'name': 'Deutsch',
        'sprachwahl': 'Sprache',
        'marke': 'Ablago – Paketkatalog',
        'beschreibung': 'Pakete für Ablago: fertige Mappentypen und Sichten',
        'handbuecher': 'Handbücher',
        'ohne_internet': 'Pakete herunterladen',
        'registry': 'Registry',
        'registry_url': REGISTRY,
        'dms_adresse': 'Ablago-Adresse',
        'dialog_titel': 'Adresse deines Ablago',
        'dialog_html': 'Zum Beispiel <code>https://dms.example.org</code> oder <code>http://192.168.1.20:3000</code>. Die Adresse bleibt nur in diesem Browser; die Seite sendet nichts an dein Ablago.',
        'dialog_fehler': 'Bitte eine Adresse mit http:// oder https:// angeben.',
        'speichern': 'Speichern und öffnen',
        'abbrechen': 'Abbrechen',
        'regeln': 'Regeln für Pakete',
        'regeln_url': f'{REGISTRY}/blob/main/REGELN.md',
        'symbole': 'Symbole: Lucide (ISC-Lizenz)',
        'titel': 'Pakete für Ablago',
        'einleitung_html': 'Fertige Mappentypen und Sichten für dein <a href="https://github.com/motom001/dms">Ablago</a> – Open Source und vom Ablago-Projekt freigegeben. Installieren unter <strong>Werkbank → Pakete</strong> oder direkt von hier.',
        'hinweis_html': '',
        'suche': 'Paket suchen …',
        'suche_label': 'Pakete durchsuchen',
        'art': 'Art',
        'alle': 'Alle Pakete',
        'konfiguration': 'Konfiguration',
        'mit_code': 'Mit Code',
        'kachel_code': 'mit Code',
        'kachel_maschinell': 'maschinell übersetzt',
        'keine': 'Kein Paket gefunden.',
        'kategorie': 'Kategorie',
        'alle_kategorien': 'Alle Kategorien',
        'autor': 'Autor',
        'alle_autoren': 'Alle Autoren',
        'dms_version': 'Deine Ablago-Version',
        'dms_version_platzhalter': 'z. B. 0.144.2',
        'dms_version_hilfe': 'Steht in Ablago unter „Über Ablago“. Bleibt nur in diesem Browser.',
        'nur_passend': 'Nur Pakete, die zu meinem Ablago passen',
        'nur_lokal': 'Nur Pakete, die alles lokal machen',
        'stand': 'Stand',
        'anzahl': ('Paket', 'Pakete'),
        'datum': '%d.%m.%Y',
    },
    'en': {
        'name': 'English',
        'sprachwahl': 'Language',
        'marke': 'Ablago – package catalogue',
        'beschreibung': 'Packages for Ablago: ready-made Mappe types and views',
        'handbuecher': 'Manuals',
        'ohne_internet': 'Download packages',
        'registry': 'Registry',
        'registry_url': f'{REGISTRY}/blob/main/README.en.md',
        'dms_adresse': 'Ablago address',
        'dialog_titel': 'Address of your Ablago',
        'dialog_html': 'For example <code>https://dms.example.com</code> or <code>http://192.168.1.20:3000</code>. The address stays in this browser only; this page sends nothing to your Ablago.',
        'dialog_fehler': 'Please enter an address starting with http:// or https://.',
        'speichern': 'Save and open',
        'abbrechen': 'Cancel',
        'regeln': 'Rules for packages',
        'regeln_url': f'{REGISTRY}/blob/main/REGELN.en.md',
        'symbole': 'Icons: Lucide (ISC licence)',
        'titel': 'Packages for Ablago',
        'einleitung_html': 'Ready-made Mappe types and views for your <a href="https://github.com/motom001/dms">Ablago</a> – open source and approved by the Ablago project. Install them in Ablago under <strong>Werkbank → Pakete</strong> (Workbench → Packages) or right from here.',
        'hinweis_html': '<strong>Note:</strong> Package names and descriptions come from the packages themselves and are in German for now, as are the package pages (multilingual package content will follow). Where the German and English wording differ, the German one applies.',
        'suche': 'Search packages …',
        'suche_label': 'Search packages',
        'art': 'Type',
        'alle': 'All packages',
        'konfiguration': 'Configuration',
        'mit_code': 'With code',
        'kachel_code': 'with code',
        'kachel_maschinell': 'machine-translated',
        'keine': 'No package found.',
        'kategorie': 'Category',
        'alle_kategorien': 'All categories',
        'autor': 'Author',
        'alle_autoren': 'All authors',
        'dms_version': 'Your Ablago version',
        'dms_version_platzhalter': 'e.g. 0.144.2',
        'dms_version_hilfe': 'Shown in Ablago under “About Ablago”. Stays in this browser only.',
        'nur_passend': 'Only packages that fit my Ablago',
        'nur_lokal': 'Only packages that work fully locally',
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


def seite(titel: str, inhalt: str, tiefe: int, beschreibung: str = '', sprache: str = 'de', umschalter: bool = False, skripte: tuple[str, ...] = ()) -> str:
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
    mehr = ''.join(f'\n  <script src="{vor}{x}?v={STAND}" defer></script>' for x in skripte)
    return f'''<!doctype html>
<html lang="{sprache}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(titel)}</title>
  <meta name="description" content="{e(beschreibung or t['beschreibung'])}">{alternativ}
  <link rel="icon" href="{vor}favicon.svg" type="image/svg+xml">
  <link rel="icon" href="{vor}favicon.ico" sizes="48x48">
  <link rel="apple-touch-icon" href="{vor}apple-touch-icon.png">
  <link rel="stylesheet" href="{vor}stil.css?v={STAND}">
  <script src="{vor}dms.js?v={STAND}" defer></script>{mehr}
</head>
<body>
  <header class="kopf"><a href="{start}" class="marke"><img src="{vor}ablago-zeichen-farbig.svg" alt="" width="28" height="28">{e(t['marke'])}</a>
    <nav><a href="{vor}sammeldatei.html">{e(t['ohne_internet'])}</a><a href="https://help.ablago.app/">{e(t['handbuecher'])}</a><a href="{t['registry_url']}">{e(t['registry'])}</a>
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
  <footer><a href="{t['regeln_url']}">{e(t['regeln'])}</a> · <a href="{vor}katalog.json">katalog.json</a> · <a href="{REGISTRY}/blob/main/werkzeuge/symbole/LICENSE">{e(t['symbole'])}</a></footer>
</body>
</html>
'''


def lies_yaml(ordner: Path, rel: str | None):
    if not rel or not (ordner / rel).exists():
        return []
    return yaml.safe_load((ordner / rel).read_text(encoding='utf-8')) or []


def symbol(p: dict, klasse: str = '') -> str:
    """Symbol eines Pakets (#98): Lucide-SVG direkt in der Seite, bei Zusatzsprachen mit Kürzel; ohne Symbol der Anfangsbuchstabe."""
    svg = symbol_svg(p['symbol']) if p.get('symbol') else None
    klassen = ' '.join(['symbol', *([klasse] if klasse else [])])
    if not svg:
        return f'<span class="{klassen}" aria-hidden="true">{e(p["name"][:1].upper())}</span>'
    kuerzel = f'<span class="kuerzel">{e(p["kuerzel"])}</span>' if p.get('kuerzel') else ''
    return f'<span class="{klassen} bild" aria-hidden="true">{svg}{kuerzel}</span>'


def kachel(p: dict, sprache: str = 'de', vor: str | None = None) -> str:
    v = p['versionen'][0]
    code = 'code' if v['code'] else 'konfiguration'
    suche = ' '.join([p['id'], p['name'], p['beschreibung'], p['autor']['name']]).lower()
    if vor is None:
        vor = '../' * SPRACHEN[sprache].count('/')
    # Pakettexte sind deutsch – auch auf der englischen Übersicht als lang="de" ausgezeichnet (Vorlesen, Silbentrennung).
    de = '' if sprache == 'de' else ' lang="de"'
    mit_code = f' · {e(TEXTE[sprache]["kachel_code"])}' if v['code'] else ''
    # Sprachpaket (Ablago #731): maschinell übersetzt schon in der Übersicht erkennbar.
    if (v.get('sprache') or {}).get('maschinell'):
        mit_code += f' · {e(TEXTE[sprache]["kachel_maschinell"])}'
    netz = netz_art(p['id'])
    kats = p.get('kategorien') or []
    chips = ''.join(f'<span class="chip">{e(KATEGORIEN[k][sprache])}</span>' for k in kats if k in KATEGORIEN)
    return f'''      <a class="kachel" href="{vor}paket/{e(p['id'])}/" data-art="{code}" data-suche="{e(suche)}" data-kategorien="{e(' '.join(kats))}" data-autor="{e(p['autor']['github'])}" data-netz="{netz}" data-versionen="{e(versionen_daten(p))}">
        {symbol(p)}
        <span class="name"{de}>{e(p['name'])}</span>
        <span class="text"{de}>{e(p['beschreibung'])}</span>
        <span class="unter">{e(p['aktuell'])} · {e(p['autor']['name'])}{mit_code}</span>
        <span class="chips">{chips}</span>
        <span class="passt-marke" hidden></span>
      </a>'''


def versionen_daten(p: dict) -> str:
    """Versionen mit nötiger Ablago-Version für den Filter „passt zu meinem Ablago“ (#84), neueste zuerst."""
    return json.dumps([[x['version'], x['dms']] for x in p['versionen']], separators=(',', ':'))


def uebersicht(katalog: dict, pakete: list, sprache: str) -> str:
    """Startseite (Übersicht) in einer Sprache; Texte aus TEXTE."""
    t = TEXTE[sprache]
    kacheln = '\n'.join(kachel(p, sprache) for p in pakete)
    zahl = {k: sum(1 for p in pakete if k in (p.get('kategorien') or [])) for k in KATEGORIEN}
    kat_opt = ''.join(f'<option value="{e(k)}">{e(KATEGORIEN[k][sprache])} ({zahl[k]})</option>' for k in KATEGORIEN if zahl[k])
    autoren = sorted({(p['autor']['github'], p['autor']['name']) for p in pakete}, key=lambda a: a[1].lower())
    autor_opt = ''.join(f'<option value="{e(g)}">{e(n)}</option>' for g, n in autoren)
    hinweis = f'\n    <p class="hinweis">{t["hinweis_html"]}</p>' if t['hinweis_html'] else ''
    inhalt = f'''    <h1>{e(t['titel'])}</h1>
    <p class="leise">{t['einleitung_html']}</p>{hinweis}
    <div class="werkzeuge">
      <input type="search" id="suche" placeholder="{e(t['suche'])}" aria-label="{e(t['suche_label'])}">
      <select id="kategorie" aria-label="{e(t['kategorie'])}"><option value="">{e(t['alle_kategorien'])}</option>{kat_opt}</select>
      <select id="autor" aria-label="{e(t['autor'])}"><option value="">{e(t['alle_autoren'])}</option>{autor_opt}</select>
      <select id="art" aria-label="{e(t['art'])}"><option value="">{e(t['alle'])}</option><option value="konfiguration">{e(t['konfiguration'])}</option><option value="code">{e(t['mit_code'])}</option></select>
    </div>
    <div class="dmsversion">
      <label for="dms-version">{e(t['dms_version'])}</label>
      <input id="dms-version" inputmode="decimal" autocomplete="off" placeholder="{e(t['dms_version_platzhalter'])}" aria-describedby="dms-version-hilfe">
      <label class="haken"><input type="checkbox" id="nur-passend" disabled> {e(t['nur_passend'])}</label>
      <label class="haken"><input type="checkbox" id="nur-lokal"> {e(t['nur_lokal'])}</label>
      <span id="dms-version-hilfe" class="leise klein">{e(t['dms_version_hilfe'])}</span>
    </div>
    <div class="kacheln">
{kacheln}
    </div>
    <p id="keine" class="leerhinweis" {'hidden' if pakete else ''}>{e(t['keine'])}</p>
    <p class="leise">{e(t['stand'])}: {datum(katalog.get('erstellt', ''), sprache)} · {len(pakete)} {e(t['anzahl'][0 if len(pakete) == 1 else 1])}</p>
'''
    return seite(t['marke'], inhalt, SPRACHEN[sprache].count('/'), sprache=sprache, umschalter=True)


# Wie im DMS (shared/src/pakete.ts, #449): dieselben Formulierungen in der Rechte-Vorschau vor der Installation.
HANDBUCH_PAKETE = 'https://help.ablago.app/admin/aktuell/pakete/'
DMS_TYPEN = {'dms:ablageort': 'Ablageort', 'dms:rolle': 'Rolle', 'dms:post': 'Post'}
EREIGNISSE = {
    'post.angelegt': ('Neue Post ist angelegt', 'ereignis-post-angelegt'),
    'dokument.hochgeladen': ('Ein Dokument wurde hochgeladen', 'ereignis-dokument-hochgeladen'),
    'texterkennung.fertig': ('Die Texterkennung eines Dokuments ist fertig', 'ereignis-texterkennung-fertig'),
    'volltext.fertig': ('Der Volltext eines Dokuments ist da', 'ereignis-volltext-fertig'),
    'paket.einstellungen_geaendert': ('Die Einstellungen des Pakets wurden geändert', 'ereignis-einstellungen-geandert'),
    # DMS #577, ab 0.137.0
    'datei.umwandeln': ('Eine Datei soll umgewandelt werden (Dateitypen, die Ablago nicht selbst liest)', 'ereignis-datei-umwandeln'),
    # DMS #585, ab 0.142.0
    'sicherung.fertig': ('Eine Sicherung ist fertig (verschlüsselt) und kann außer Haus kopiert werden', 'ereignis-sicherung-fertig'),
    # DMS #614, ab 0.145.0
    'datei.volltext': ('Eine Datei braucht ihren Volltext (Dateitypen, die Ablago nicht selbst liest)', 'ereignis-datei-volltext'),
    # DMS #631, ab 0.149.0
    'datei.archivfassung': ('Ein Dokument mit fertigem Volltext braucht seine Archivfassung (PDF/A)', 'ereignis-datei-archivfassung'),
    # DMS #670, ab 0.153.0 – nur zu den Typen aus code.mappentypen
    'mappe.angelegt': ('Eine Mappe ist angelegt', 'ereignis-mappe'),
    'mappe.geaendert': ('Eine Mappe ist gespeichert und dabei geändert', 'ereignis-mappe'),
    'mappe.geloescht': ('Eine Mappe ist gelöscht (Papierkorb)', 'ereignis-mappe'),
    'mappe.wiederhergestellt': ('Eine Mappe ist wiederhergestellt', 'ereignis-mappe'),
    'frist.erreicht': ('Eine Frist ist erreicht (Erinnerung bzw. Tag selbst)', 'ereignis-frist-erreicht'),
}
DOKUMENT_RECHTE = {'lesen': 'Dokumente lesen', 'schreiben': 'Dokumente lesen und Volltext schreiben'}
SCHNITTSTELLEN = {
    'dms:vektoren': ('Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)', 'recht-vektoren', 'Vektoren zu Dokumenten'),
    # DMS #444, ab 0.124.0
    'dms:antworten': ('Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die Ablago mitgibt (dms:antworten)', 'recht-antworten', 'Fragen an die Ablage beantworten'),
    # DMS #511, ab 0.125.0
    'dms:erkennen': ('Felder aus Dokumenten vorschlagen („Aus Dokument ausfüllen“) – nur aus dem Text, den Ablago mitgibt (dms:erkennen)', 'recht-erkennen', 'Felder aus Dokumenten vorschlagen'),
    # DMS #458, ab 0.133.0
    'dms:texterkennung': ('Texterkennung für Scans und Bilder übernehmen – Ablago meldet Dokumente ohne Text und zeigt „wartet auf Texterkennung“, bis das Paket den Volltext schreibt (dms:texterkennung)', 'recht-texterkennung', 'Texterkennung übernehmen'),
    # DMS #577, ab 0.137.0 – dahinter die Dateitypen aus code.umwandeln
    'dms:umwandeln': ('Dateien umwandeln, die Ablago nicht selbst lesen kann – das Paket liest die Originaldatei und liefert eine Fassung (PDF, PNG oder JPEG) für Vorschaubild und Volltext; das Original bleibt unverändert (dms:umwandeln)', 'recht-umwandeln', 'Dateien umwandeln'),
    # DMS #585, ab 0.142.0
    'dms:sicherung-lesen': ('Die verschlüsselte Sicherung lesen, um sie außer Haus zu kopieren – kann sie nicht öffnen (kein Schlüssel, keine Inhalte) (dms:sicherung-lesen)', 'recht-sicherung-lesen', 'Sicherung lesen'),
    # DMS #614, ab 0.145.0 – dahinter die Dateitypen aus code.volltext
    'dms:volltext': ('Volltext für Dateien liefern, die Ablago nicht selbst lesen kann – das Paket liest die Datei und schreibt nur ihren Volltext; Dokumente ändern, ersetzen oder löschen kann es nicht (dms:volltext)', 'recht-volltext', 'Volltext liefern'),
    # DMS #631, ab 0.149.0 – dahinter die Dateitypen aus code.archivfassung.typen
    'dms:archivfassung': ('Archivfassung (PDF/A) ablegen – das Paket liest Dokumente mit ihrem Volltext und den Wortpositionen und legt daneben ein durchsuchbares PDF/A ab; das Original bleibt unverändert, ändern, ersetzen oder löschen kann es nichts (dms:archivfassung)', 'recht-archivfassung', 'Archivfassung ablegen'),
}
# Kurze Namen der Dateitypen hinter dms:umwandeln, dms:volltext und dms:archivfassung (wie DATEITYP_NAMEN im DMS,
# shared/src/dateiumwandlung.ts).
DATEITYP_NAMEN = {
    'application/pdf': 'PDF', 'image/jpeg': 'JPEG', 'image/png': 'PNG',
    'image/tiff': 'TIFF', 'image/webp': 'WebP', 'image/gif': 'GIF', 'image/bmp': 'BMP', 'image/heic': 'HEIC', 'image/heif': 'HEIF', 'image/avif': 'AVIF',
    'application/msword': 'Word', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word',
    'application/vnd.ms-excel': 'Excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel',
    'application/vnd.ms-powerpoint': 'PowerPoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PowerPoint',
    'application/vnd.oasis.opendocument.text': 'OpenDocument-Text', 'application/vnd.oasis.opendocument.spreadsheet': 'OpenDocument-Tabelle',
    'application/vnd.oasis.opendocument.presentation': 'OpenDocument-Präsentation',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.template': 'Word', 'application/vnd.ms-word.document.macroenabled.12': 'Word',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.template': 'Excel', 'application/vnd.ms-excel.sheet.macroenabled.12': 'Excel',
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow': 'PowerPoint', 'application/vnd.ms-powerpoint.presentation.macroenabled.12': 'PowerPoint',
    'message/rfc822': 'E-Mail', 'application/vnd.ms-outlook': 'Outlook-E-Mail', 'application/rtf': 'RTF', 'text/rtf': 'RTF', 'text/plain': 'Text',
}


def adressen(code: dict) -> list[str]:
    """Namen der Einstellungen vom Typ adresse (Dienst-Adresse, DMS #444) in den Abschnitten."""
    return [str(f.get('name') or f.get('schluessel')) for b in code.get('einstellungen') or [] if isinstance(b, dict) and 'liste' not in b
            for f in (b.get('felder') or []) if isinstance(f, dict) and f.get('typ') == 'adresse']


def netz_art(pid: str) -> str:
    """lokal · dienst · internet – automatisch aus dem Manifest (#95), damit es kein Autor falsch angeben kann."""
    try:
        code = manifest(pid).get('code') or {}
    except FileNotFoundError:
        return 'lokal'
    if code.get('netz'):
        return 'internet'
    return 'dienst' if adressen(code) else 'lokal'


def netz_text(netz: list, adresse: list | None = None) -> str:
    """Netzwerkzugriff wie in Ablago (#449, #444), Adressen als Code."""
    einst = [f'der Adresse aus der Einstellung „{e(a)}“ (trägst du ein und bestätigst sie)' for a in adresse or []]
    if not netz and not einst:
        return 'kein Zugriff auf Netzwerk und Internet'
    return 'Zugriff auf Netzwerk/Internet nur zu: ' + ', '.join([f'<code>{e(n)}</code>' for n in netz] + einst)


def hilfe(anker: str, titel: str) -> str:
    """„?“ zur Erklärung im Administratorhandbuch von Ablago."""
    return f' <a class="hilfe" href="{HANDBUCH_PAKETE}#{anker}" title="Erklärung: {e(titel)}" aria-label="Erklärung: {e(titel)} (Administratorhandbuch)">?</a>'


def rechte_text(code: dict, typen: dict | None = None) -> str:
    """Rechte und Netzwerkzugriff eines Pakets mit Code – so formuliert wie die Vorschau in Ablago (#449)."""
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
    lesen = list(dict.fromkeys((r.get('lesen') or []) + schreiben))  # Schreiben setzt Lesen voraus (wie in Ablago).
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
            feld = {'dms:umwandeln': 'umwandeln', 'dms:volltext': 'volltext', 'dms:archivfassung': 'archivfassung'}.get(x)
            mimes = code.get(feld) if feld != 'archivfassung' else (code.get('archivfassung') or {}).get('typen')
            typen_ = list(dict.fromkeys(DATEITYP_NAMEN.get(m, m) for m in mimes or [])) if feld else []
            zeilen.append(e(SCHNITTSTELLEN[x][0] + (': ' + ', '.join(typen_) if typen_ else '')) + hilfe(SCHNITTSTELLEN[x][1], SCHNITTSTELLEN[x][2]))
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


def manifest(pid: str) -> dict:
    pfad = WURZEL / 'pakete' / pid / 'manifest.yaml'
    return (yaml.safe_load(pfad.read_text(encoding='utf-8')) or {}) if pfad.exists() else {}


def schnittstellen(m: dict) -> set:
    return set(((m.get('code') or {}).get('rechte') or {}).get('schnittstellen') or [])


def beziehungen(p: dict, pakete: list) -> list:
    """„Passt dazu“ (#80) – nur aus Angaben, die es schon gibt: Abhängigkeiten in beide Richtungen und die
    Schnittstellen. Ein Paket mit dms:umwandeln liefert eine Fassung, deren Text bei Scans erst ein Paket mit
    dms:texterkennung liest – das ist die Abgrenzung Bildformate ↔ Texterkennung."""
    nach_id = {x['id']: x for x in pakete}
    eigene = schnittstellen(manifest(p['id']))
    gruppen = []
    gesehen = {p['id']}

    def dazu(titel, ids, hoechstens=None, link=''):
        liste = [nach_id[i] for i in ids if i in nach_id and i not in gesehen]
        liste = liste[:hoechstens] if hoechstens else liste
        gesehen.update(x['id'] for x in liste)
        if liste:
            gruppen.append((titel, liste, link))

    dazu('Braucht', list(p['versionen'][0]['abhaengigkeiten']))
    if 'dms:umwandeln' in eigene:
        dazu('Für durchsuchbaren Text bei Scans zusätzlich', [x['id'] for x in pakete if 'dms:texterkennung' in schnittstellen(manifest(x['id']))])
    # Ergänzungen (motom001/dms#405): je Gruppe eine Überschrift, z. B. „Weitere Sprachen“; der Rest wie bisher.
    ergaenzungen = [x for x in pakete if (x['versionen'][0].get('ergaenzt') or {}).get('paket') == p['id']]
    for gruppe in sorted({(x['versionen'][0]['ergaenzt'].get('gruppe') or 'Ergänzungen') for x in ergaenzungen}):
        dazu(gruppe, [x['id'] for x in ergaenzungen if (x['versionen'][0]['ergaenzt'].get('gruppe') or 'Ergänzungen') == gruppe])
    dazu('Erweiterungen dafür', [x['id'] for x in pakete if p['id'] in x['versionen'][0]['abhaengigkeiten']])
    if 'dms:texterkennung' in eigene:
        dazu('Liest auch Dateien, die diese Pakete umwandeln', [x['id'] for x in pakete if 'dms:umwandeln' in schnittstellen(manifest(x['id']))])
    # Ähnlich = gleiche Kategorie (#84); die Überschrift führt zur gefilterten Liste (wie „Das gefällt dir vielleicht auch ›“).
    kats = p.get('kategorien') or []
    if kats:
        dazu('Ähnliche Pakete', [x['id'] for x in pakete if set(kats) & set(x.get('kategorien') or [])], 3, f'../../?kategorie={quote(kats[0])}')
    else:
        art = p['versionen'][0]['code']
        dazu('Ähnliche Pakete', [x['id'] for x in pakete if x['versionen'][0]['code'] == art], 3)
    g = p['autor']['github']
    dazu(f'Weitere Pakete von {p["autor"]["name"]}', [x['id'] for x in pakete if x['autor']['github'] == g], 3, f'../../autor/{quote(g)}/')
    return gruppen


def mini(x: dict, vor: str) -> str:
    return (f'<a class="mini" href="{vor}paket/{e(x["id"])}/">{symbol(x, "klein")}'
            f'<span><strong>{e(x["name"])}</strong><br><span class="leise kurzfassung">{e(x["beschreibung"])}</span></span></a>')


def autor_link(p: dict, vor: str) -> str:
    g = p['autor']['github']
    # GitHub-Profil steht auf der Autorenseite (Thomas, #80)
    return f'<a href="{vor}autor/{e(g)}/">{e(p["autor"]["name"])}</a>'


def bereich(titel: str, inhalt: str, kurz: str = '', klasse: str = '') -> str:
    """Aufklappbarer Bereich der Paketseite (#80); kurz = Zusammenfassung in der Kopfzeile."""
    k = f' <span class="leise kurz">{e(kurz)}</span>' if kurz else ''
    return f'<details class="bereich {klasse}"><summary><h2>{e(titel)}</h2>{k}</summary><div class="innen">{inhalt}</div></details>'


def mehrzahl(n: int, eins: str, viele: str) -> str:
    return f'{n} {eins if n == 1 else viele}'


OPERATOR_TEXT = {
    'gleich': 'ist gleich', 'enthaelt': 'enthält', 'kleiner': 'liegt vor', 'groesser': 'liegt nach', 'zwischen': 'zwischen',
    'ausserhalb': 'außerhalb von', 'imZeitraum': 'im Zeitraum', 'einerVon': 'ist', 'zeigtAuf': 'zeigt auf',
    'ja': 'ist angehakt', 'nein': 'ist nicht angehakt', 'leer': 'ist leer', 'nichtLeer': 'ist ausgefüllt',
}
EINHEIT_TEXT = {'tage': ('Tag', 'Tage'), 'wochen': ('Woche', 'Wochen'), 'monate': ('Monat', 'Monate'), 'jahre': ('Jahr', 'Jahre')}


def wert_text(w) -> str:
    """Wert einer Bedingung in Alltagssprache (wie beschreibeBedingung in Ablago, Fassung für Einsteiger)."""
    if isinstance(w, list):
        return ' oder '.join(f'„{x}“' if not isinstance(x, dict) else wert_text(x) for x in w)
    if isinstance(w, dict):
        art, n = w.get('art'), int(w.get('versatz') or 0)
        if art == 'heute':
            if not n:
                return 'heute'
            eins, viele = EINHEIT_TEXT.get(w.get('einheit', 'tage'), ('Tag', 'Tage'))
            return f'heute {"+" if n > 0 else "−"} {abs(n)} {eins if abs(n) == 1 else viele}'
        if art in ('jahr', 'monat'):
            wort = 'Jahr' if art == 'jahr' else 'Monat'
            return {0: f'aktuelles {wort}' if art == 'jahr' else 'aktueller Monat', -1: f'letztes {wort}' if art == 'jahr' else 'letzter Monat',
                    1: f'nächstes {wort}' if art == 'jahr' else 'nächster Monat'}.get(n, f'{wort} {n:+d}')
        if art == 'ich':
            return 'du selbst'
        if 'wert' in w:
            return wert_text(w['wert'])
        return art or '…'
    if isinstance(w, bool):
        return 'ja' if w else 'nein'
    return f'„{w}“'


def bedingung_text(b: dict, feldnamen: dict) -> str:
    feld = feldnamen.get(b.get('feld'), b.get('feld'))
    op, w = b.get('operator'), b.get('wert')
    if op in ('ja', 'nein', 'leer', 'nichtLeer'):
        return f'„{feld}“ {OPERATOR_TEXT[op]}'
    if op == 'zwischen' and isinstance(w, list) and len(w) == 2:
        return f'„{feld}“ zwischen {wert_text(w[0])} und {wert_text(w[1])}'
    return f'„{feld}“ {OPERATOR_TEXT.get(op, op)} {wert_text(w)}'


def sicht_baum(sichten: list, typnamen: dict, feldnamen: dict) -> str:
    """Ansichten als Baum wie später in der Ablage; jede Ansicht aufklappbar mit ihren Filtern (#80)."""
    kinder: dict = {}
    for s in sichten:
        kinder.setdefault(s.get('eltern'), []).append(s)

    def eintrag(s: dict) -> str:
        teile = []
        if s.get('beschreibung'):
            teile.append(f'<p>{e(s["beschreibung"])}</p>')
        typen = [typnamen.get(t, t) for t in s.get('typen', [])]
        teile.append(f'<p><span class="leise">Zeigt:</span> {e(", ".join(typen)) if typen else "alle Mappentypen"}</p>')
        bed = s.get('bedingungen') or []
        if bed:
            teile.append('<p class="leise">Nur Mappen, bei denen:</p><ul>' + ''.join(f'<li>{e(bedingung_text(b, feldnamen))}</li>' for b in bed) + '</ul>')
        else:
            teile.append('<p class="leise">Keine weiteren Filter.</p>')
        unter = kinder.get(s['schluessel'])
        rest = ('<ul class="baum">' + ''.join(eintrag(k) for k in unter) + '</ul>') if unter else ''
        return f'<li><details class="sicht"><summary>{e(s["name"])}</summary><div class="filter">{"".join(teile)}</div></details>{rest}</li>'

    oben = [s for s in sichten if not s.get('eltern') or s['eltern'] not in {x['schluessel'] for x in sichten}]
    return ('<p class="leise klein">So erscheinen sie später in der Ablage. Antippen zeigt, was eine Ansicht filtert.</p>'
            '<ul class="baum wurzel">' + ''.join(eintrag(s) for s in oben) + '</ul>')


def detail(p: dict, pakete: list) -> str:
    v = p['versionen'][0]
    ordner = WURZEL / 'pakete' / p['id']
    vorhanden = (ordner / 'manifest.yaml').exists()
    m = manifest(p['id'])
    readme = md((ordner / 'README.md').read_text(encoding='utf-8')) if (ordner / 'README.md').exists() else f'<p>{e(p["beschreibung"])}</p>'
    changelog = md((ordner / 'CHANGELOG.md').read_text(encoding='utf-8')) if (ordner / 'CHANGELOG.md').exists() else ''
    typen = lies_yaml(ordner, (m.get('inhalt') or {}).get('mappentypen')) if vorhanden else []
    sichten = lies_yaml(ordner, (m.get('inhalt') or {}).get('sichten')) if vorhanden else []
    if typen:
        typ_html = ''.join(
            f'<details><summary><strong>{e(t["name"])}</strong> – {len(t.get("felder", []))} Felder</summary><ul>'
            + ''.join(f'<li>{e(f["label"])} <span class="leise">({FELDTYPEN.get(f["typ"], f["typ"])}{", Pflicht" if f.get("pflicht") else ""})</span></li>' for f in t.get('felder', []))
            + '</ul></details>' for t in typen)
        n_typen = len(typen)
    else:
        n_typen = len(v['inhalt']['mappentypen'])
        typ_html = ('<ul>' + ''.join(f'<li>{e(t["name"])}</li>' for t in v['inhalt']['mappentypen']) + '</ul>') if n_typen else '<p class="leise">keine</p>'
    namen = {s['schluessel']: s['name'] for s in sichten}
    if sichten:
        typnamen, feldnamen = {}, {}
        for x in pakete:  # Mappentypen anderer Pakete (z. B. basis:person) mit Namen zeigen
            for t in lies_yaml(WURZEL / 'pakete' / x['id'], (manifest(x['id']).get('inhalt') or {}).get('mappentypen')) if (WURZEL / 'pakete' / x['id'] / 'manifest.yaml').exists() else []:
                typnamen[f'{x["id"]}:{t["schluessel"]}'] = t['name']
        for t in typen:
            typnamen[t['schluessel']] = t['name']
            for f in t.get('felder', []):
                feldnamen.setdefault(f['key'], f['label'])
        sicht_html = sicht_baum(sichten, typnamen, feldnamen)
        n_sichten = len(sichten)
    else:
        n_sichten = len(v['inhalt']['sichten'])
        sicht_html = ('<ul>' + ''.join(f'<li>{e(s["name"])}</li>' for s in v['inhalt']['sichten']) + '</ul>') if n_sichten else '<p class="leise">keine</p>'
    n_bsp = v['inhalt']['beispiele']
    # Beispiel-Dokumente (motom001/dms#878, Registry #137); fehlt bei älteren Katalog-Einträgen.
    n_dok = v['inhalt'].get('beispieldokumente', 0)
    wortlisten = lies_yaml(ordner, (m.get('inhalt') or {}).get('wortlisten')) if vorhanden else []
    n_wort = len(wortlisten)
    wort_html = (f'<h3>Gleichbedeutende Wörter für die Suche</h3><p class="leise klein">Wer eines der Wörter sucht, findet auch die anderen – '
                 f'z. B. „{e(wortlisten[0]["woerter"][1] if len(wortlisten[0]["woerter"]) > 1 else wortlisten[0]["woerter"][0])}“ findet auch „{e(wortlisten[0]["woerter"][0])}“.</p><ul class="woerter">'
                 + ''.join(f'<li>{" · ".join(e(w) for w in g["woerter"])}</li>' for g in wortlisten) + '</ul>') if n_wort else ''
    # Mitgelieferte Automatisierungen (DMS #712, Registry #108): in Klartext, nach der Installation aus.
    autos = lies_yaml(ordner, (m.get('inhalt') or {}).get('automatisierungen')) if vorhanden else []
    n_auto = len(autos)
    auto_html = ('<h3>Vorgefertigte Automatisierungen</h3><p class="leise klein">Nach der Installation aus – beim Installieren fragt Ablago, '
                 'welche gleich eingeschaltet werden. Vorlaufzeit, Empfänger und Text stellst du selbst ein.</p><ul>'
                 + ''.join(f'<li><strong>{e(a.get("name", ""))}</strong>{" – " + e(a["beschreibung"]) if a.get("beschreibung") else ""}</li>' for a in autos) + '</ul>') if n_auto else ''
    sp = m.get('sprache') if vorhanden and isinstance(m.get('sprache'), dict) else None
    if sp:
        # Sprachpaket (Ablago #731): nur Texte; dazu die Pakete, für die es Beschriftungen mitbringt.
        fuer = sorted(x.stem for x in (ordner / 'beschriftungen').glob('*.yaml')) if (ordner / 'beschriftungen').is_dir() else []
        bereiche = sorted(x.stem for x in (ordner / 'texte').glob('*.json')) if (ordner / 'texte').is_dir() else []
        links = ['<a href="../' + e(x) + '/">' + e(x) + '</a>' for x in fuer]
        mitkommt = (f'<p>Ablago auf <strong>{e(SPRACHNAMEN.get(sp["kennung"], sp["kennung"]))}</strong>: Texte der Oberfläche, Meldungen und E-Mails '
                    f'({e(", ".join(bereiche)) or "–"}), gemacht für Ablago {e(str(sp.get("ablago", "")))}. Was fehlt, erscheint auf Englisch.</p>'
                    + (f'<p>Beschriftungen für die Pakete {", ".join(links)} – Mappentypen, Felder, '
                       'Auswahlwerte und Ansichten in dieser Sprache.</p>' if fuer else '')
                    + '<p class="leise klein">Nach der Installation erlaubst du die Sprache unter Werkbank → Sprachen; jede Person wählt sie dann in Mein Konto.</p>')
        kurz_mit = 'Sprachpaket, nur Texte'
    elif n_typen or n_sichten or n_bsp or n_wort or n_auto:
        mit_dok = f' und {mehrzahl(n_dok, "Beispiel-Dokument", "Beispiel-Dokumenten")}' if n_dok else ''
        bsp = (f'<p>{mehrzahl(n_bsp, "Beispielmappe", "Beispielmappen")}{mit_dok} mit erfundenen Daten – nur, wenn du sie bei der Installation auswählst.</p>'
               if n_bsp else '<p class="leise">keine Beispielmappen</p>')
        mitkommt = f'<div class="spalten"><div><h3>Mappentypen</h3>{typ_html}</div><div><h3>Ansichten</h3>{sicht_html}</div></div>{wort_html}{auto_html}{bsp}'
        kurz_mit = ' · '.join(t for t in [mehrzahl(n_typen, 'Mappentyp', 'Mappentypen') if n_typen else '',
                                          mehrzahl(n_sichten, 'Ansicht', 'Ansichten') if n_sichten else '',
                                          (mehrzahl(n_bsp, 'Beispielmappe', 'Beispielmappen') + (f' ({mehrzahl(n_dok, "Dokument", "Dokumente")})' if n_dok else '')) if n_bsp else '',
                                          mehrzahl(n_wort, 'Wortgruppe', 'Wortgruppen') + ' für die Suche' if n_wort else '',
                                          mehrzahl(n_auto, 'Automatisierung', 'Automatisierungen') if n_auto else ''] if t)
    else:
        mitkommt = ('<p>Dieses Paket legt <strong>nichts</strong> in deiner Ablage an – keine Mappentypen, keine Ansichten, '
                    'keine Beispielmappen. Es bringt nur eine Funktion mit (siehe „Was das Paket darf“).</p>')
        kurz_mit = 'legt nichts in der Ablage an'
    rechte = rechte_text(m['code'], {t['schluessel']: t['name'] for t in typen if 'schluessel' in t}) if vorhanden and m.get('code') \
        else '<p>Kein Code: Das Paket bringt nur Texte – kein HTML, keine Programme.</p>' if sp \
        else '<p>Kein Code: Das Paket legt nur Mappentypen, Ansichten und auf Wunsch Beispiele an.</p>'
    if sp:
        kurz_recht = 'nur Texte, kein Code'
    elif m.get('code'):
        kurz_recht = 'mit Zugriff auf Netzwerk/Internet' if ((m['code'].get('netz') or []) or adressen(m['code'])) else 'kein Zugriff auf Netzwerk und Internet'
    else:
        kurz_recht = 'nur Konfiguration, kein Code'
    abh = ', '.join(f'<a href="../{e(k)}/">{e(k)}</a> {e(b)}' for k, b in v['abhaengigkeiten'].items()) or 'keine'
    versionen = ''.join(
        f'<tr><td>{e(x["version"])}</td><td>{datum(x["veroeffentlicht"])}</td><td>{e(x["dms"])}</td>'
        f'<td><a href="../../{e(x["archiv"])}">Archiv</a></td><td><button type="button" class="textknopf" data-installieren="{e(p["id"])}@{e(x["version"])}">installieren</button></td></tr>'
        for x in p['versionen'])
    technik = (f'<dl class="eckdaten"><dt>Version</dt><dd>{e(v["version"])} vom {datum(v["veroeffentlicht"])}</dd>'
               f'<dt>Lizenz</dt><dd>{e(p["lizenz"])}</dd><dt>Nötige Ablago-Version</dt><dd>{e(v["dms"])}</dd>'
               f'<dt>Abhängigkeiten</dt><dd>{abh}</dd><dt>Quellcode</dt><dd><a href="{e(v["quelle"])}">auf GitHub ansehen</a></dd></dl>'
               f'<h3>Alle Versionen</h3><div class="tabelle"><table><thead><tr><th>Version</th><th>Datum</th><th>Ablago</th><th>Download</th><th></th></tr></thead>'
               f'<tbody>{versionen}</tbody></table></div>')
    passt = ''.join((f'<h3><a class="weiter" href="{e(link)}">{e(t)} <span aria-hidden="true">›</span></a></h3>' if link else f'<h3>{e(t)}</h3>')
                    + '<div class="minis">' + ''.join(mini(x, '../../') for x in liste) + '</div>' for t, liste, link in beziehungen(p, pakete))
    melden = (f'{REGISTRY}/issues/new?template=paket-meldung.yml&title={quote("[" + p["name"] + "] ")}'
              f'&paket={quote(vorlagen_option(p))}')
    technik += (f'<p><a href="{e(melden)}">Fehler oder Wunsch zu diesem Paket melden</a> '
                f'<span class="leise">(auf GitHub; übertragen wird nur der Paketname)</span></p>')
    kats = ''.join(f'<a class="chip" href="../../?kategorie={quote(k)}">{e(KATEGORIEN[k]["de"])}</a>' for k in (p.get('kategorien') or []) if k in KATEGORIEN)
    teile = [bereich('Was mitkommt', mitkommt, kurz_mit),
             bereich('Was das Paket darf', rechte, kurz_recht),
             bereich('Beschreibung', readme, 'ausführlich', 'readme')]
    if changelog:
        teile.append(bereich('Änderungen', changelog, f'Version {v["version"]}', 'changelog'))
    teile.append(bereich('Für Fortgeschrittene und Entwickler', technik, 'Version, Lizenz, Quellcode, Downloads', 'klein'))
    passt_html = f'\n    <section class="passt"><h2>Passt dazu</h2>{passt}</section>' if passt else ''
    inhalt = (f'    <p class="zurueck"><a href="../../index.html">← Alle Pakete</a></p>\n'
              f'    <div class="paketkopf" data-paket="{e(p["id"])}" data-versionen="{e(versionen_daten(p))}">\n'
              f'      {symbol(p, "gross")}\n'
              f'      <div class="titel"><h1>{e(p["name"])}</h1>\n'
              f'        <button type="button" class="knopf primaer installieren" data-installieren="{e(p["id"])}@{e(v["version"])}">In meinem Ablago installieren</button>\n'
              f'        <p class="kurztext">{e(p["beschreibung"])}</p>\n'
              f'        <p class="leise klein">Version {e(v["version"])} · von {autor_link(p, "../../")}</p>\n'
              f'        <p class="chips">{kats}</p></div>\n'
              f'    </div>\n'
              f'    <div id="dms-passt" class="dms-passt"></div>\n    ' + (sprach_hinweis(p) + '\n    ' if sprach_hinweis(p) else '') + '\n    '.join(teile) + passt_html + '\n')
    return seite(f'{p["name"]} – Ablago-Pakete', inhalt, 2, p['beschreibung'])


def autorseite(name: str, github: str, liste: list) -> str:
    """Alle Pakete eines Autors (#80): erreichbar über den Namen auf jeder Paketseite."""
    kacheln = '\n'.join(kachel(p, 'de', '../../') for p in liste)
    inhalt = (f'    <p class="zurueck"><a href="../../index.html">← Alle Pakete</a></p>\n'
              f'    <h1>Pakete von {e(name)}</h1>\n'
              f'    <p class="leise">{mehrzahl(len(liste), "Paket", "Pakete")} · <a class="gh" href="https://github.com/{e(github)}">GitHub-Profil @{e(github)} ↗</a></p>\n'
              f'    <div class="kacheln">\n{kacheln}\n    </div>\n')
    return seite(f'Pakete von {name} – Ablago-Pakete', inhalt, 2, f'Alle Ablago-Pakete von {name}')



STIL = '''
:root { --grund: #f6f7f8; --flaeche: #fff; --tinte: #1c2328; --leise: #5b6670; --linie: #dde2e6; --a: #1F4E79; --auf-a: #fff; --warn: #b26a00; }
@media (prefers-color-scheme: dark) { :root { --grund: #14181b; --flaeche: #1d2226; --tinte: #e8ecef; --leise: #9aa5ae; --linie: #2e353a; --a: #8DB8E0; --auf-a: #141A22; --warn: #ffb74d; } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--grund); color: var(--tinte); font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
a { color: var(--a); }
.kopf { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; max-width: 980px; margin: 0 auto; padding: 14px 16px; }
.kopf nav { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.marke { font-weight: 700; font-size: 1.1rem; color: var(--tinte); text-decoration: none; display: inline-flex; align-items: center; gap: .5rem; }
.marke img { flex: none; }
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
.werkzeuge select { flex: 1 1 140px; }
.kacheln { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
a.kachel { display: grid; align-content: start; grid-template-columns: auto 1fr; gap: 2px 12px; background: var(--flaeche); border: 1px solid var(--linie); border-radius: 12px; padding: 16px; color: inherit; text-decoration: none; }
a.kachel:hover, a.kachel:focus-visible { border-color: var(--a); }
.kachel .symbol { grid-row: span 3; }
.kachel .name { font-weight: 700; }
.kachel .text, .kachel .unter { grid-column: 2; color: var(--leise); font-size: .92rem; }
.symbol { display: inline-grid; place-items: center; width: 44px; height: 44px; border-radius: 12px; background: var(--a); color: var(--auf-a); font-weight: 700; font-size: 1.3rem; }
.symbol.gross { width: 64px; height: 64px; font-size: 1.8rem; border-radius: 16px; flex: none; }
/* Symbol je Paket (#98): Lucide, eine Farbe für alle; Kürzel (z. B. Sprache) unten rechts */
.symbol.bild { position: relative; }
.symbol svg { width: 55%; height: 55%; display: block; }
.symbol .kuerzel { position: absolute; right: -5px; bottom: -5px; min-width: 1.9em; padding: 1px 3px; border-radius: 6px; background: var(--flaeche); color: var(--tinte); border: 1.5px solid var(--a); font-size: .62rem; font-weight: 700; line-height: 1.2; letter-spacing: .02em; text-align: center; }
.symbol.gross .kuerzel { font-size: .78rem; right: -6px; bottom: -6px; }
.symbol.klein .kuerzel { font-size: .6rem; min-width: 1.8em; right: -7px; bottom: -7px; padding: 0 2px; border-radius: 5px; }
.paketkopf { display: flex; gap: 16px; align-items: flex-start; margin: 8px 0 20px; }
.paketkopf .titel { flex: 1; min-width: 0; }
.paketkopf .kurztext { font-size: 1.08rem; margin: 4px 0; }
.paketkopf .titel { display: grid; grid-template-columns: 1fr auto; grid-template-areas: 'name knopf' 'text text' 'meta meta'; align-items: center; column-gap: 16px; }
.paketkopf h1 { grid-area: name; }
.paketkopf .installieren { grid-area: knopf; }
.paketkopf .kurztext { grid-area: text; }
.paketkopf .titel > .leise { grid-area: meta; }
.paketkopf .installieren { flex: none; white-space: nowrap; padding: 7px 14px; font-size: .95rem; }
.paketkopf h1 { font-size: 1.6rem; }
p.klein { font-size: .9rem; margin: 2px 0; }
a.gh { color: var(--leise); font-size: .9em; text-decoration: none; }
a.gh:hover, a.gh:focus-visible { color: var(--a); text-decoration: underline; }
details.bereich { padding: 0; margin: 10px 0; border-radius: 12px; }
details.bereich > summary { display: flex; align-items: baseline; column-gap: 8px; gap: 10px; flex-wrap: wrap; padding: 12px 16px; cursor: pointer; list-style: none; }
details.bereich > summary::-webkit-details-marker { display: none; }
details.bereich > summary::before { content: "›"; display: inline-block; width: .8em; transition: transform .15s; color: var(--leise); font-weight: 700; }
details.bereich[open] > summary::before { transform: rotate(90deg); }
details.bereich > summary h2 { display: inline; font-size: 1.05rem; font-weight: 650; border: 0; margin: 0; padding: 0; }
details.bereich .kurz { font-size: .92rem; }
details.bereich > .innen { padding: 4px 16px 14px; border-top: 1px solid var(--linie); }
ul.woerter { margin: 4px 0 10px; }
ul.baum { list-style: none; margin: 0; padding-left: 18px; border-left: 1px solid var(--linie); }
ul.baum.wurzel { padding-left: 0; border-left: 0; }
ul.baum li { margin: 2px 0; }
details.sicht { border: 0; padding: 0; margin: 0; background: none; border-radius: 0; }
details.sicht > summary { cursor: pointer; padding: 3px 0; list-style: none; }
details.sicht > summary::-webkit-details-marker { display: none; }
details.sicht > summary::before { content: "›"; display: inline-block; width: .9em; color: var(--leise); font-weight: 700; transition: transform .15s; }
details.sicht[open] > summary::before { transform: rotate(90deg); }
details.sicht > .filter { margin: 2px 0 8px .9em; padding: 6px 10px; border-radius: 8px; background: var(--grund); font-size: .92rem; }
details.sicht > .filter p { margin: 2px 0; }
details.sicht > .filter ul { margin: 2px 0 2px 1.1em; padding: 0; }
details.bereich.klein > summary h2 { font-size: 1rem; color: var(--leise); }
.spalten { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
.passt h3 { font-size: 1rem; margin: 16px 0 8px; }
.passt h3 a.weiter { color: inherit; text-decoration: none; }
.passt h3 a.weiter span { color: var(--leise); font-weight: 700; margin-left: 2px; }
.passt h3 a.weiter:hover, .passt h3 a.weiter:focus-visible { color: var(--a); }
.passt h3 a.weiter:hover span, .passt h3 a.weiter:focus-visible span { color: var(--a); }
.chips { display: flex; flex-wrap: wrap; align-items: center; align-content: flex-start; gap: 6px; margin: 6px 0 0; grid-column: 2; }
.paketkopf .titel > .chips { grid-column: 1 / -1; margin: 4px 0 0; }
.paketkopf .titel > .chips:empty { display: none; }
.chip { display: inline-block; font-size: .78rem; padding: 1px 8px; border-radius: 999px; border: 1px solid var(--linie); color: var(--leise); text-decoration: none; background: var(--grund); }
a.chip:hover, a.chip:focus-visible { border-color: var(--a); color: var(--a); }
.kachel { position: relative; }
.kachel.mit-marke { padding-bottom: 40px; }
/* Passt zu meinem DMS (#84): fester Platz unten rechts, Punkt + Text – bewusst anders als die Kategorie-Chips */
.passt-marke { position: absolute; right: 14px; bottom: 12px; font-size: .82rem; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.passt-marke::before { content: ""; width: 9px; height: 9px; border-radius: 50%; background: currentColor; }
.passt-marke.ja { color: #2e7d32; }
.passt-marke.aelter { color: #b26a00; }
.passt-marke.nein { color: #c62828; }
@media (prefers-color-scheme: dark) { .passt-marke.ja { color: #81c784; } .passt-marke.aelter { color: #ffb74d; } .passt-marke.nein { color: #ef9a9a; } }
.dmsversion { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; margin: -8px 0 18px; }
.dmsversion input#dms-version { font: inherit; padding: 6px 10px; border: 1px solid var(--linie); border-radius: 8px; background: var(--flaeche); color: var(--tinte); width: 9em; }
.dmsversion .haken { display: inline-flex; gap: 6px; align-items: center; }
.dms-passt:empty { display: none; }
.dms-passt { margin: 0 0 16px; padding: 12px 16px; border-radius: 12px; border: 1px solid var(--linie); background: var(--flaeche); }
.dms-passt.ja { padding: 6px 12px; font-size: .92rem; }
.dms-passt.warn { border-color: var(--warn); }
.dms-passt p { margin: 4px 0; }
.dms-passt .aelter-link { font-size: .9rem; }
.dms-passt input { font: inherit; padding: 4px 8px; border: 1px solid var(--linie); border-radius: 8px; background: var(--grund); color: var(--tinte); width: 8em; }
.minis { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
a.mini { display: flex; gap: 10px; align-items: flex-start; background: var(--flaeche); border: 1px solid var(--linie); border-radius: 10px; padding: 10px 12px; color: inherit; text-decoration: none; font-size: .92rem; }
a.mini:hover, a.mini:focus-visible { border-color: var(--a); }
.kurzfassung { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.symbol.klein { width: 32px; height: 32px; font-size: 1rem; border-radius: 8px; flex: none; }
@media (max-width: 640px) { .paketkopf { gap: 12px; } .paketkopf .titel { grid-template-columns: 1fr; grid-template-areas: 'name' 'text' 'meta' 'knopf'; } .paketkopf .installieren { width: 100%; margin-top: 12px; } .paketkopf .symbol.gross { width: 48px; height: 48px; font-size: 1.4rem; } .spalten { grid-template-columns: 1fr; } }
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
  // Passt das Paket zu meinem DMS? (#84) Die Version kommt aus dem Fragment #dms=… (Link aus dem DMS,
  // motom001/dms#622) oder wird eingetippt – sie bleibt nur in diesem Browser und geht an keinen Server.
  var BEREICH = /^(>=|>|=|\\^|~)?(\\d+\\.\\d+\\.\\d+)( <(\\d+\\.\\d+\\.\\d+))?$/, VERSION = /^\\d+\\.\\d+\\.\\d+$/, VSCHL = 'dms-version';
  var EN = document.documentElement.lang === 'en';
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
  function mindestens(bereich) { var m = BEREICH.exec((bereich || '').trim()); return m ? m[2] : bereich; }
  function liesVersion() { try { var v = localStorage.getItem(VSCHL) || ''; return VERSION.test(v) ? v : ''; } catch (e) { return ''; } }
  function merkeVersion(v) { try { if (v) localStorage.setItem(VSCHL, v); else localStorage.removeItem(VSCHL); } catch (e) { /* nur jetzt */ } }
  (function ausFragment() {
    var m = /(?:^#|&)dms=(\\d+\\.\\d+\\.\\d+)(?:&|$)/.exec(location.hash);
    if (!m) return;
    merkeVersion(m[1]);
    // Fragment wieder entfernen, damit die Version nicht mit einem geteilten Link weitergegeben wird.
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* egal */ }
  })();
  // Für sammeldatei.js (läuft nach dms.js): dieselbe gemerkte Version, kein zweites Lesen der Adresse.
  window.dmsVersion = { lies: liesVersion, merke: merkeVersion };
  // Ergebnis je Paket: ja (neueste Version passt) · aelter (eine ältere passt) · nein; null ohne Version.
  function pruefe(versionen, dms) {
    if (!dms) return null;
    if (passt(dms, versionen[0][1])) return { fall: 'ja', version: versionen[0][0] };
    for (var i = 1; i < versionen.length; i++) if (passt(dms, versionen[i][1])) return { fall: 'aelter', version: versionen[i][0], neu: versionen[0] };
    return { fall: 'nein', neu: versionen[0] };
  }
  function marke(r) {
    if (!r) return '';
    if (r.fall === 'ja') return EN ? 'fits your Ablago' : 'passt zu deinem Ablago';
    if (r.fall === 'aelter') return EN ? 'Ablago update recommended' : 'Ablago-Update empfohlen';
    return (EN ? 'needs Ablago ' : 'braucht Ablago ') + mindestens(r.neu[1]) + (EN ? '+' : ' oder neuer');
  }
  var suche = document.getElementById('suche'), art = document.getElementById('art'), kat = document.getElementById('kategorie'),
      autor = document.getElementById('autor'), vfeld = document.getElementById('dms-version'), nur = document.getElementById('nur-passend'),
      lokal = document.getElementById('nur-lokal');
  function filtern() {
    var q = (suche.value || '').trim().toLowerCase(), a = art.value, k = kat ? kat.value : '', au = autor ? autor.value : '', n = 0;
    var dms = vfeld && VERSION.test(vfeld.value.trim()) ? vfeld.value.trim() : '';
    if (nur) { nur.disabled = !dms; if (!dms) nur.checked = false; }
    document.querySelectorAll('.kachel').forEach(function (el) {
      var r = el.dataset.versionen ? pruefe(JSON.parse(el.dataset.versionen), dms) : null, m = el.querySelector('.passt-marke');
      if (m) { m.hidden = !r; m.textContent = marke(r); m.className = 'passt-marke' + (r ? ' ' + r.fall : ''); el.classList.toggle('mit-marke', !!r); }
      var ok = (!q || el.dataset.suche.indexOf(q) >= 0) && (!a || el.dataset.art === a)
        && (!k || (' ' + el.dataset.kategorien + ' ').indexOf(' ' + k + ' ') >= 0) && (!au || el.dataset.autor === au)
        && (!(nur && nur.checked) || (r && r.fall === 'ja')) && (!(lokal && lokal.checked) || el.dataset.netz === 'lokal');
      el.hidden = !ok; if (ok) n++;
    });
    document.getElementById('keine').hidden = n > 0;
    // Kategorie und Autor stehen in der Adresse (teilbar, Zurück im Browser); die DMS-Version nie.
    var p = new URLSearchParams(location.search);
    if (k) p.set('kategorie', k); else p.delete('kategorie');
    if (au) p.set('autor', au); else p.delete('autor');
    var ziel = location.pathname + (p.toString() ? '?' + p.toString() : '');
    if (ziel !== location.pathname + location.search) { try { history.replaceState(null, '', ziel); } catch (e) { /* egal */ } }
  }
  if (suche) {
    var p = new URLSearchParams(location.search);
    if (kat && p.get('kategorie')) kat.value = p.get('kategorie');
    if (autor && p.get('autor')) autor.value = p.get('autor');
    if (vfeld) vfeld.value = liesVersion();
    [suche, art, kat, autor, vfeld, nur, lokal].forEach(function (x) { if (x) x.addEventListener(x.tagName === 'INPUT' && x.type !== 'checkbox' ? 'input' : 'change', function () {
      if (x === vfeld) { var w = vfeld.value.trim(); if (!w || VERSION.test(w)) merkeVersion(w); }
      filtern();
    }); });
    filtern();
  }
  // Paketseite: Hinweis „passt / ältere Version / braucht neueres DMS“ unter dem Kopf.
  var kopf = document.querySelector('.paketkopf[data-versionen]'), feld = document.getElementById('dms-passt');
  function zeigePaket() {
    var versionen = JSON.parse(kopf.dataset.versionen), dms = liesVersion(), r = pruefe(versionen, dms), id = kopf.dataset.paket;
    var knopf = kopf.querySelector('.installieren');
    feld.className = 'dms-passt'; feld.textContent = ''; if (knopf) knopf.hidden = false;
    if (!r) {
      feld.innerHTML = '<p class="leise">Passt das Paket zu deinem Ablago? Deine Ablago-Version: <input id="dms-version-paket" inputmode="decimal" placeholder="z. B. 0.144.2" aria-label="Deine Ablago-Version"> <span class="klein">(steht in Ablago unter „Über Ablago“, bleibt nur in diesem Browser)</span></p>';
      var i = document.getElementById('dms-version-paket');
      i.addEventListener('change', function () { var w = i.value.trim(); if (VERSION.test(w)) { merkeVersion(w); zeigePaket(); } });
      return;
    }
    var aendern = ' <a href="#" data-dms-version-aendern>ändern</a>';
    if (r.fall === 'ja') { feld.className += ' ja'; feld.innerHTML = 'Passt zu deinem Ablago ' + dms + '.' + aendern; return; }
    if (knopf) knopf.hidden = true;
    feld.className += ' warn';
    var html = '<p><strong>Für Version ' + r.neu[0] + ' brauchst du Ablago ' + mindestens(r.neu[1]) + ' oder neuer</strong> – du hast ' + dms + '.' + aendern + '</p>'
      + '<p>Aktualisiere dein Ablago, damit du dieses Paket mit allen Verbesserungen und Fehlerbehebungen nutzen kannst.</p>'
      + '<p><a class="knopf primaer" href="'''+HANDBUCH_AKTUALISIEREN+'''">So aktualisierst du dein Ablago →</a></p>';
    if (r.fall === 'aelter') html += '<p class="aelter-link"><a href="#" data-installieren="' + id + '@' + r.version + '">Ältere Version ' + r.version + ' trotzdem installieren</a> <span class="leise">– ihr fehlen Verbesserungen und Fehlerbehebungen. Nach Ablago-Update holst du die neue Version über die Paketverwaltung nach.</span></p>';
    feld.innerHTML = html;
  }
  if (kopf && feld) {
    feld.addEventListener('click', function (e) { if (e.target.closest('[data-dms-version-aendern]')) { e.preventDefault(); merkeVersion(''); zeigePaket(); } });
    zeigePaket();
  }
})();
'''


# Sammeldatei (motom001/dms#461): Auswahl, Abhängigkeiten und ZIP – alles im Browser aus katalog.json und archive/.
# Format und Prüfung wie werkzeuge/sammeldatei.py (Referenz) und schema/sammeldatei.schema.json.
SAMMEL_INHALT = r'''    <h1>Pakete herunterladen</h1>
    <p><strong>Für Ablago ohne Internetzugang:</strong> mehrere Pakete als eine Datei, die du in Ablago hochlädst.</p>
    <p class="leise">Kommt dein Ablago nicht ins Internet? Wähle hier die Pakete aus und lade sie als <strong>eine Sammeldatei</strong> herunter.
      In Ablago lädst du sie unter <strong>Werkbank → Pakete → „Ohne Internet …“</strong> hoch (oder im Einrichtungsassistenten, Schritt „Pakete dazuholen“).
      Ablago prüft jedes Paket gegen seine Prüfsumme und installiert dann eins nach dem anderen.</p>
    <noscript><p class="fehler">Die Sammeldatei entsteht in deinem Browser – dafür braucht die Seite JavaScript.</p></noscript>
    <form id="sammel" class="stapel" hidden>
      <div class="sammel-dms">
        <label for="dms-version"><strong>Ablago-Version</strong> <span class="leise">– dazu passende Paketversionen</span></label>
        <input id="dms-version" inputmode="decimal" placeholder="z. B. 0.107.1" pattern="\d+\.\d+\.\d+" autocomplete="off" aria-describedby="dms-version-hilfe">
        <p id="dms-version-hilfe" class="leise klein">Steht in Ablago unter „Über Ablago“ (der Link aus Ablago bringt sie mit). Sie bleibt nur in diesem Browser. Vorgabe: die neueste Version. Leer: die neueste Version jedes Pakets.</p>
      </div>
      <fieldset class="sammel-pakete"><legend><strong>Pakete</strong> <span class="leise">– Abhängigkeiten kommen automatisch mit</span></legend>
        <ul id="sammel-liste" class="sammel-liste"></ul>
      </fieldset>
      <div id="sammel-probleme" class="hinweis-warn" role="status" hidden></div>
      <div class="knoepfe"><button type="submit" class="knopf primaer" id="sammel-los">Sammeldatei herunterladen</button><span id="sammel-zusammenfassung" class="leise"></span></div>
      <div id="sammel-ergebnis" role="status" aria-live="polite"></div>
    </form>
    <p id="sammel-laden" class="leise">Lade den Katalog …</p>
    <section><h2>So prüft Ablago die Sammeldatei</h2>
      <ul>
        <li>Die Sammeldatei enthält die Archive aus diesem Katalog Byte für Byte unverändert, dazu das Verzeichnis <code>sammeldatei.json</code> mit Größe und SHA-256 je Archiv und eine Kopie des signierten Katalogs (<code>katalog.json</code> mit <code>katalog.sig</code>). Diese Seite prüft jedes Archiv schon beim Zusammenstellen gegen <code>katalog.json</code>.</li>
        <li>Ablago nimmt die Datei nur an, wenn jedes Archiv genau zu seiner Prüfsumme passt, nichts anderes darin liegt und jedes Paket gültig ist – sonst installiert es gar nichts. Kennt es den offiziellen Katalog schon, vergleicht es die Prüfsummen auch damit.</li>
        <li>Ablago prüft die Signatur des Katalogs auch ohne Internet. Ist sie gültig und steht jedes Archiv mit seiner Prüfsumme darin, zeigt es „aus dem offiziellen Katalog vom …“, und du musst die Herkunft nicht bestätigen. Ist der Katalog nicht signiert, beweisen die Prüfsummen nur, dass die Datei vollständig und unverändert ist – nicht, wer sie zusammengestellt hat; dann bestätigst du die Herkunft in Ablago. Zum Vergleich zeigt diese Seite den SHA-256 der ganzen Datei, Ablago nach dem Hochladen ebenfalls.</li>
        <li>Rechte von Paketen mit Code bestätigst du in Ablago je Paket – eine Sammelbestätigung gibt es nicht.</li>
      </ul>
    </section>
'''


def sammelseite() -> str:
    return seite('Pakete herunterladen – Ablago-Pakete', SAMMEL_INHALT, 0, 'Mehrere Pakete als eine Sammeldatei für Ablago ohne Internet', skripte=('sammeldatei.js',))


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
// passend zur DMS-Version; jedes Archiv gegen katalog.json geprüft; ZIP mit sammeldatei.json, LIESMICH.txt,
// dem signierten Katalog (katalog.json und katalog.sig Byte für Byte, #74) und den Archiven unter pakete/.
// Es wird nichts hochgeladen; die Datei entsteht nur in diesem Browser. Die DMS-Version kommt aus dms.js
// (Fragment #dms=…, gemerkt nur in diesem Browser) – die Adresse liest diese Seite selbst nicht.
(function () {
  var VORAUSWAHL = ['texterkennung', 'benachrichtigungen'];
  var KATALOG_URL = 'https://catalog.ablago.app/katalog.json';
  var BEREICH = /^(>=|>|=|\^|~)?(\d+\.\d+\.\d+)( <(\d+\.\d+\.\d+))?$/;
  var VERSION = /^\d+\.\d+\.\d+$/;
  var katalog = null, katalogRoh = null, signatur = null, gewaehlt = [];
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
      if (!v) { probleme.push(von ? '„' + name(von) + '“ braucht „' + p.name + '“ ' + bereich + '; dazu passt keine Version für Ablago ' + dms + '.' : '„' + p.name + '“: keine Version passt zu DMS ' + dms + '.'); return; }
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
      var unter = !v ? 'Braucht Ablago ' + p.versionen[0].dms + (dms ? ' – du hast ' + dms + '.' : '.') : (zeige.code ? 'Enthält Code – die Rechte bestätigst du in Ablago für dieses Paket einzeln.' : 'Kein Code – legt Mappentypen und Ansichten an.');
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
  var LIESMICH = 'Sammeldatei für Ablago\n=======================\n\nDiese Datei enthält mehrere Pakete aus dem Paketkatalog des Ablago-Projekts\n(https://catalog.ablago.app/) – für Ablago ohne Internet.\n\nSo installierst du sie:\n  Werkbank → Pakete → „Ohne Internet …“ → Sammeldatei wählen\n  (oder im Einrichtungsassistenten, Schritt „Pakete dazuholen“).\n\nAblago prüft vorher jedes Paket gegen die Prüfsumme in sammeldatei.json und\ninstalliert dann Paket für Paket; Rechte von Paketen mit Code bestätigst du einzeln.\nEntpacken musst du nichts.\n';
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
      // Signierter Katalog (#74): genau die geladenen Bytes – die Signatur gilt nur für sie.
      var mitKatalog = signatur ? [{ name: 'katalog.json', daten: katalogRoh }, { name: 'katalog.sig', daten: signatur }] : [];
      var blob = zip([{ name: 'sammeldatei.json', daten: enc.encode(JSON.stringify(vz, null, 2) + '\n') }, { name: 'LIESMICH.txt', daten: enc.encode(LIESMICH) }].concat(mitKatalog, dateien));
      var summe = hex(await crypto.subtle.digest('SHA-256', await blob.arrayBuffer()));
      var dateiname = 'dms-pakete-' + jetzt.slice(0, 10) + '.zip';
      var a = el('a', { href: URL.createObjectURL(blob), download: dateiname, className: 'knopf' }, ['Noch einmal speichern']);
      aus.textContent = '';
      aus.appendChild(el('p', {}, [el('strong', { text: dateiname }), ' mit ' + eintraege.map(function (e) { return e.name + ' ' + e.version; }).join(', ') + ' (' + (blob.size / 1048576).toFixed(1).replace('.', ',') + ' MB).']));
      aus.appendChild(el('p', { className: 'leise' }, ['SHA-256 der Datei: ', el('code', { text: summe }), ' – Ablago zeigt denselben Wert nach dem Hochladen.']));
      aus.appendChild(a);
      a.click();
    } catch (e) { aus.textContent = 'Das hat nicht geklappt: ' + e.message; }
    finally { knopf.disabled = false; zeichne(); }
  }
  async function start() {
    var form = document.getElementById('sammel');
    if (!form) return;
    try {
      // Erst die Signatur, dann den Katalog: Wird dazwischen neu veröffentlicht, passt die Signatur nicht, und das DMS fragt nach der Herkunft.
      var s = await fetch('katalog.sig', { cache: 'no-store' }).catch(function () { return null; });
      signatur = s && s.ok ? new Uint8Array(await s.arrayBuffer()) : null;
      var k = await fetch('katalog.json', { cache: 'no-store' });
      if (!k.ok) throw new Error(String(k.status));
      katalogRoh = new Uint8Array(await k.arrayBuffer());
      katalog = JSON.parse(new TextDecoder().decode(katalogRoh));
    }
    catch (e) { document.getElementById('sammel-laden').textContent = 'Der Katalog lässt sich nicht laden: ' + e.message; return; }
    var gemerkt = window.dmsVersion ? window.dmsVersion.lies() : '', feld = document.getElementById('dms-version');
    if (gemerkt) feld.value = gemerkt;
    else {
      // Vorgabe: die neueste DMS-Version (Releases auf GitHub); klappt das nicht, bleibt das Feld leer.
      fetch('https://api.github.com/repos/motom001/dms/releases/latest').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
        var v = j && String(j.tag_name || '').replace(/^v/, '');
        if (v && VERSION.test(v) && !feld.value) { feld.value = v; zeichne(); }
      }).catch(function () {});
    }
    gewaehlt = VORAUSWAHL.filter(function (id) { return paket(id); });
    feld.addEventListener('input', function () {
      // Wie die Übersicht: eine gültige (oder leere) Eingabe merkt sich der Browser für die anderen Katalogseiten.
      var w = feld.value.trim(); if (window.dmsVersion && (!w || VERSION.test(w))) window.dmsVersion.merke(w);
      document.getElementById('sammel-ergebnis').textContent = ''; zeichne();
    });
    form.addEventListener('submit', herunterladen);
    document.getElementById('sammel-laden').hidden = true;
    form.hidden = false;
    zeichne();
  }
  start();
})();
'''


# Stand von Stil und Skripten im Dateinamen-Anhang, damit Browser nach Änderungen nicht die alte Fassung zeigen
STAND = hashlib.sha256((STIL + SAMMEL_STIL + SKRIPT + SAMMEL_SKRIPT).encode()).hexdigest()[:10]


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
        (ziel / 'index.html').write_text(detail(p, pakete), encoding='utf-8')
    autoren: dict = {}
    for p in pakete:
        autoren.setdefault(p['autor']['github'], (p['autor']['name'], []))[1].append(p)
    for g, (name, liste) in autoren.items():
        ziel = ausgabe / 'autor' / g
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / 'index.html').write_text(autorseite(name, g, liste), encoding='utf-8')
    # Logo und Favicon von Ablago (Quelle: motom001/dms-website, Ordner marke/; Name und Logo nicht unter Apache-2.0)
    for d in (Path(__file__).parent / 'marke').iterdir():
        (ausgabe / d.name).write_bytes(d.read_bytes())
    (ausgabe / 'stil.css').write_text((STIL + SAMMEL_STIL).lstrip(), encoding='utf-8')
    (ausgabe / 'dms.js').write_text(SKRIPT.lstrip(), encoding='utf-8')
    (ausgabe / 'sammeldatei.html').write_text(sammelseite(), encoding='utf-8')
    (ausgabe / 'sammeldatei.js').write_text(SAMMEL_SKRIPT.lstrip(), encoding='utf-8')
    print(f'Webseite: {len(pakete)} Pakete')


if __name__ == '__main__':
    main()
