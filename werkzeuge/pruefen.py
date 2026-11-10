#!/usr/bin/env python3
"""
Prüft Pakete nach den Regeln der Registry (REGELN.md).

    python3 werkzeuge/pruefen.py                    # alle Pakete unter pakete/ und die Vorlage
    python3 werkzeuge/pruefen.py pakete/haushalt    # ein Paket
    python3 werkzeuge/pruefen.py --basis origin/main pakete/haushalt   # zusätzlich: Version erhöht?

Braucht: pip install pyyaml jsonschema
"""
import json, re, subprocess, sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

WURZEL = Path(__file__).resolve().parent.parent
SCHEMA_MANIFEST = json.loads((WURZEL / 'schema/manifest.schema.json').read_text())
SCHEMA_INHALT = json.loads((WURZEL / 'schema/inhalt.schema.json').read_text())
PFLICHT = ['manifest.yaml', 'README.md', 'LICENSE', 'CHANGELOG.md', 'tests']
VERBOTEN = re.compile(r'\.(wasm|so|dll|dylib|exe|jar|class|bin|o|a|pyc|node)$', re.I)
MAX_GROESSE = 2 * 1024 * 1024  # je Datei; Bilder fürs README gern kleiner
# Die eine Größengrenze für Pakete, wie im DMS (PAKET_MAX in shared/src/pakete.ts, DMS #644): Archiv und code/.
# katalog.py und sammeldatei.py nutzen dieselbe Zahl (test_grenzen prüft das).
PAKET_MAX = 128 * 1024 * 1024
CODE_MAX = PAKET_MAX  # alle Dateien unter code/ zusammen
# Beispiel-Dokumente (motom001/dms#878, Registry #137): Dateien unter inhalt/beispiele/, die ein Beispiel unter
# dokumente nennt. Dieselben Grenzen wie in Ablago: nur PDF, PNG und JPEG (am Inhalt erkannt, Endung passend), je Datei
# höchstens so groß wie ein hochgeladenes Dokument (MAX_DATEIGROESSE, 100 MB), alle zusammen höchstens PAKET_MAX.
BEISPIEL_ORDNER = 'inhalt/beispiele/'
BEISPIEL_DATEI_MAX = 100 * 1024 * 1024
BEISPIEL_ENDUNGEN = {'pdf': 'application/pdf', 'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}
BEISPIEL_PFAD = re.compile(r'^beispiele/([A-Za-z0-9_-][A-Za-z0-9._-]{0,79}/){0,4}[A-Za-z0-9_-][A-Za-z0-9._-]{0,99}$')
# git (und damit der Katalog auf gh-pages, Registry #133) nimmt keine Datei über 100 MB an; ab hier ein Hinweis.
GIT_DATEI_MAX = 100 * 1024 * 1024


def inhalt_validator(art: str) -> Draft202012Validator:
    schema = {'$schema': SCHEMA_INHALT['$schema'], '$defs': SCHEMA_INHALT['$defs'], **SCHEMA_INHALT[art]}
    return Draft202012Validator(schema)


def lies_yaml(pfad: Path, fehler: list[str]):
    try:
        return yaml.safe_load(pfad.read_text(encoding='utf-8'))
    except Exception as e:  # noqa: BLE001
        fehler.append(f'{pfad.name}: kein gültiges YAML ({e})')
        return None


def schema_fehler(validator: Draft202012Validator, daten, datei: str) -> list[str]:
    return [f"{datei}: {'/'.join(map(str, e.absolute_path)) or '(oben)'}: {e.message}" for e in validator.iter_errors(daten)]


def version_von(git_ref: str, manifest: Path) -> str | None:
    rel = manifest.relative_to(WURZEL).as_posix()
    try:
        alt = subprocess.run(['git', 'show', f'{git_ref}:{rel}'], cwd=WURZEL, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None  # neues Paket
    return (yaml.safe_load(alt) or {}).get('version')


def geaendert(git_ref: str, ordner: Path) -> bool:
    rel = ordner.relative_to(WURZEL).as_posix()
    r = subprocess.run(['git', 'diff', '--quiet', git_ref, '--', rel], cwd=WURZEL)
    return r.returncode != 0


DATUM = re.compile(r'^\d{4}-\d{2}-\d{2}$')
VERWEISE = {'mappentyp', 'feld', 'benutzer', 'rolle', 'sicht'}
# Mappentypen, die das DMS selbst mitbringt (ab 0.75.0); Verweis als dms:<schluessel>.
DMS_TYPEN = {'ablageort', 'benutzer', 'rolle'}
# Veraltete Verweise (DMS #883, Registry #138): Den Ablageort bringt ab DMS 0.212.0 das Paket Basis (1.6.0) mit.
# dms:ablageort gilt im DMS bis 1.0 weiter als Alias für basis:ablageort – solange gibt es hier eine Warnung statt
# eines Fehlers.
DMS_ALIAS = {'dms:ablageort': 'basis:ablageort'}


def dms_fehler(v: str, wo: str) -> str | None:
    """Prüft einen Verweis dms:<schluessel>; None, wenn er erlaubt ist."""
    if v.split(':', 1)[1] in DMS_TYPEN:
        return None
    return f'{wo}: Mappentyp „{v}“ bringt das DMS nicht mit (erlaubt: ' + ', '.join(f'dms:{t}' for t in sorted(DMS_TYPEN)) + ')'


# Mappentypen des DMS, die code.rechte nennen darf (DMS #435): ablageort, rolle und – nur hier, nicht in
# Verweisen – post (ab DMS 0.94.0). dms:benutzer ist verboten: Pakete sehen keine Benutzer.
DMS_RECHTE_TYPEN = {'ablageort', 'rolle', 'post'}
DMS_POST_RECHT_AB = (0, 94, 0)
# Schnittstelle dms:vektoren und Ereignis volltext.fertig gibt es im DMS ab 0.122.0 (DMS #442).
DMS_VEKTOREN_AB = (0, 122, 0)
# Schnittstelle dms:antworten, Einstellung vom Typ adresse (Dienst-Adresse) und die Läufer-Funktionen
# netz_strom, netz_weiter und teil gibt es im DMS ab 0.124.0 (DMS #444).
DMS_ANTWORTEN_AB = (0, 124, 0)
# Läufer-Funktionen, die erst ab DMS 0.124.0 da sind: Ein Modul, das sie importiert, lädt in älteren nicht.
DMS_FUNKTIONEN_ANTWORTEN = {'netz_strom', 'netz_weiter', 'teil'}
# Schnittstelle dms:erkennen („Aus Dokument ausfüllen“ per Paket) gibt es im DMS ab 0.125.0 (DMS #511).
DMS_ERKENNEN_AB = (0, 125, 0)
# Schnittstelle dms:klassifizieren („Wohin gehört das?“, DMS #939). Die Versionsnummer vergibt Ablago erst beim Merge (#952);
# 0.226.0 ist die erste Version nach 0.225.0 (Verweisfelder, #935).
DMS_KLASSIFIZIEREN_AB = (0, 226, 0)
# Wortlisten (inhalt.wortlisten, DMS #356): gleichbedeutende Wörter für die Suche, ab DMS 0.127.0.
DMS_WORTLISTEN_AB = (0, 127, 0)
# Ansichten über alle Mappentypen (typen: ["*"], DMS #725).
DMS_ALLE_TYPEN_AB = (0, 182, 0)
# Beispiel-Dokumente (motom001/dms#878): ältere Ablago übergehen dokumente an Beispielen.
DMS_BEISPIEL_DOKUMENTE_AB = (0, 223, 0)
ALLE_TYPEN = '*'
# Mitgelieferte Automatisierungen (inhalt.automatisierungen, DMS #712, Registry #108), ab DMS 0.177.0. Seit dieser
# Version legt ein Datumsfeld mit frist keine Aufgaben mehr selbst an – erinnern muss eine Automatisierung.
DMS_AUTOMATISIERUNGEN_AB = (0, 177, 0)
# Wenn-Karte „Zeitplan“, „Favorit geändert“ und die Dann-Karten der Benachrichtigungen (DMS #678), ab DMS 0.181.0.
DMS_BENACHRICHTIGUNGEN_AB = (0, 181, 0)
DANN_BENACHRICHTIGUNGEN = {'zusammenfassung', 'favoriten', 'anmeldeschutz'}
# Wenn-Karten, die ein Paket nutzen darf (DMS shared/src/ereignisse.ts ohne Gruppen zaehler/betrieb/auftrag und
# ohne frist.erreicht, das in „datum“ aufgegangen ist).
WENN_MAPPE = {'mappe.angelegt', 'mappe.geaendert', 'mappe.verknuepft', 'dokument.hochgeladen', 'mappe.notiz', 'mappe.geloescht',
              'mappe.geloescht_verknuepft', 'mappe.endgueltig_geloescht', 'mappe.wiederhergestellt',
              'volltext.fertig', 'datei.umgewandelt', 'archivfassung.erstellt', 'erkennung.fertig', 'favorit.geaendert'}
WENN_OHNE_TYP = {'aufgabe.neu', 'post.angelegt', 'favorit.neu', 'benutzer.abwesenheit_gesetzt', 'benutzer.abwesenheit_beendet',
                 'benutzer.gesperrt', 'benutzer.deaktiviert', 'benutzer.aktiviert', 'benutzer.vertretung_zurueckgezogen'}
# Personen aus dem Ereignis als Empfänger (DMS shared/src/automatisierung.ts PERSONEN_IM_EREIGNIS).
PERSONEN_IM_EREIGNIS = {
    'benutzer.abwesenheit_gesetzt': {'vertreter', 'benutzer'}, 'benutzer.abwesenheit_beendet': {'vertreter', 'benutzer'},
    'benutzer.vertretung_zurueckgezogen': {'vertreter', 'benutzer'}, 'benutzer.gesperrt': {'benutzer'},
    'benutzer.deaktiviert': {'benutzer'}, 'benutzer.aktiviert': {'benutzer'}, 'favorit.neu': {'benutzer'},
}
VORLAUF_EINHEITEN = {'tage', 'wochen', 'monate'}
DANN_KARTEN = {'aufgabe', 'feld', 'stopp', 'zusammenfassung', 'favoriten', 'anmeldeschutz'}
# Schnittstelle dms:texterkennung (DMS #458): das Paket übernimmt die Texterkennung, ab DMS 0.133.0.
DMS_TEXTERKENNUNG_AB = (0, 133, 0)
# Schnittstelle dms:umwandeln, code.umwandeln und Ereignis datei.umwandeln (DMS #577): Dateien umwandeln, ab DMS 0.137.0.
DMS_UMWANDELN_AB = (0, 137, 0)
# Schnittstelle dms:sicherung-lesen und Ereignis sicherung.fertig (DMS #585): Sicherung außer Haus, ab DMS 0.142.0.
DMS_SICHERUNG_AB = (0, 142, 0)
# Schnittstelle dms:volltext, code.volltext und Ereignis datei.volltext (DMS #614): Volltext aus Paketen ohne Schreibrecht
# auf Dokumente, ab DMS 0.145.0.
DMS_VOLLTEXT_AB = (0, 145, 0)
# Schnittstelle dms:archivfassung, code.archivfassung und Ereignis datei.archivfassung (DMS #631): Archivfassung (PDF/A)
# zu Dokumenten mit fertigem Volltext ablegen, ab DMS 0.149.0.
DMS_ARCHIVFASSUNG_AB = (0, 149, 0)
# Einstellungen mit mehrfach / schliesst_aus (DMS #658).
DMS_EINSTELLUNG_MEHRFACH_AB = (0, 179, 0)
MEHRFACH_VERWEISE = ('mappentyp', 'benutzer', 'rolle', 'sicht')
# Ansichten mit fremde_typen (DMS #656): Mappentypen, die das Paket nicht mitbringt, über ihre Kennung.
DMS_FREMDE_TYPEN_AB = (0, 178, 0)
DMS_ARCHIV_AUSWAHL_AB = (0, 176, 0)
# Art emails in code.archivfassung.auswahl (DMS #946): Archivfassung für E-Mails (.eml, .msg), dms-registry #143.
DMS_ARCHIV_EMAILS_AB = (0, 221, 0)
# Ereignisse zu Mappen aus dem Ereigniskatalog und code.mappentypen (DMS #670): eigene Mappentypen ab DMS 0.153.0.
MAPPEN_EREIGNISSE = ('mappe.angelegt', 'mappe.geaendert', 'mappe.geloescht', 'mappe.wiederhergestellt', 'frist.erreicht')
DMS_MAPPEN_EREIGNISSE_AB = (0, 153, 0)
# Fremde Mappentypen (paket:typ, dms:post) und „*“ in code.mappentypen (DMS #686): Zustellung nach den Rechten des
# Paket-Benutzers, ab DMS 0.166.0.
DMS_FREMDE_MAPPENTYPEN_AB = (0, 166, 0)
# Wie shared/src/kennungen.ts in Ablago (#1084): Paket-Id bis 40 Zeichen plus ein Punkt-Zusatz bis 20, Schlüssel bis 60.
PAKET_ID_TEIL = r'[a-z][a-z0-9_]{1,39}(?:\.[a-z][a-z0-9_]{0,19})?'
TYPVERWEIS = re.compile(rf'^(\*|({PAKET_ID_TEIL}:)?[a-z][a-z0-9_]{{0,59}})$')
# Kennungen nach #1084 (Registry #173): Ids mit Punkt, über 20 Zeichen, Schlüssel über 40 Zeichen, ersetzt – ab 0.229.0.
DMS_KENNUNGEN_AB = (0, 229, 0)
HERAUSGEBER = 'app.ablago'


def dms_untergrenze(bereich: str) -> tuple[int, ...] | None:
    """Kleinste DMS-Version, die ein Bereich wie „>=0.94.0“ oder „^0.94.0 <1.0.0“ zulässt; None bei „<“ allein."""
    t = re.match(r'^(>=|>|=|\^|~)?(\d+)\.(\d+)\.(\d+)', str(bereich or '').strip())
    if not t:
        return None
    v = tuple(int(x) for x in t.group(2, 3, 4))
    return (v[0], v[1], v[2] + 1) if t.group(1) == '>' else v


def pruefe_rechte(code: dict, dms_bereich: str) -> list[str]:
    """code.rechte: Kennungen dms:<…> (das Schema prüft nur die Form)."""
    rechte = code.get('rechte') if isinstance(code.get('rechte'), dict) else {}
    fehler: list[str] = []
    post = False
    for art in ('lesen', 'schreiben'):
        for v in rechte.get(art) or []:
            if not isinstance(v, str) or not v.startswith('dms:'):
                continue
            k = v.split(':', 1)[1]
            if k == 'benutzer':
                fehler.append(f'code.rechte.{art}: dms:benutzer ist für Pakete nicht erlaubt – Pakete sehen keine Benutzer')
            elif k not in DMS_RECHTE_TYPEN:
                fehler.append(f'code.rechte.{art}: Mappentyp „{v}“ bringt das DMS nicht mit (erlaubt: ' + ', '.join(f'dms:{t}' for t in sorted(DMS_RECHTE_TYPEN)) + ')')
            elif k == 'post':
                post = True
    if post:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_POST_RECHT_AB:
            fehler.append('code.rechte: dms:post kennt das DMS erst ab 0.94.0 – bitte dms: ">=0.94.0" angeben')
    # Schnittstellen des Kerns (DMS #442): Vektoren gehören zu Dokumenten, das Paket muss sie lesen dürfen.
    ab = dms_untergrenze(dms_bereich)
    neu = 'neu' if ab is None or ab < DMS_VEKTOREN_AB else ''
    if 'dms:vektoren' in (rechte.get('schnittstellen') or []):
        if rechte.get('dokumente', 'keine') == 'keine':
            fehler.append('code.rechte.schnittstellen: dms:vektoren braucht auch code.rechte.dokumente: lesen – Vektoren gehören zu Dokumenten')
        if neu:
            fehler.append('code.rechte.schnittstellen: dms:vektoren kennt das DMS erst ab 0.122.0 – bitte dms: ">=0.122.0" angeben')
    if 'volltext.fertig' in (code.get('ereignisse') or []) and neu:
        fehler.append('code.ereignisse: volltext.fertig kennt das DMS erst ab 0.122.0 – bitte dms: ">=0.122.0" angeben')
    # dms:antworten und die Dienst-Adresse (DMS #444): ab 0.124.0.
    vor_antworten = ab is None or ab < DMS_ANTWORTEN_AB
    if 'dms:antworten' in (rechte.get('schnittstellen') or []) and vor_antworten:
        fehler.append('code.rechte.schnittstellen: dms:antworten kennt das DMS erst ab 0.124.0 – bitte dms: ">=0.124.0" angeben')
    # dms:erkennen (DMS #511): ab 0.125.0.
    if 'dms:erkennen' in (rechte.get('schnittstellen') or []) and (ab is None or ab < DMS_ERKENNEN_AB):
        fehler.append('code.rechte.schnittstellen: dms:erkennen kennt das DMS erst ab 0.125.0 – bitte dms: ">=0.125.0" angeben')
    # dms:klassifizieren (DMS #939): ab 0.226.0, ohne weitere Rechte.
    if 'dms:klassifizieren' in (rechte.get('schnittstellen') or []) and (ab is None or ab < DMS_KLASSIFIZIEREN_AB):
        fehler.append('code.rechte.schnittstellen: dms:klassifizieren kennt das DMS erst ab 0.226.0 – bitte dms: ">=0.226.0" angeben')
    # dms:texterkennung (DMS #458): ab 0.133.0; das Paket schreibt den Volltext, braucht also dokumente: schreiben.
    if 'dms:texterkennung' in (rechte.get('schnittstellen') or []):
        if rechte.get('dokumente') != 'schreiben':
            fehler.append('code.rechte.schnittstellen: dms:texterkennung braucht code.rechte.dokumente: schreiben – das Paket schreibt den Volltext')
        if ab is None or ab < DMS_TEXTERKENNUNG_AB:
            fehler.append('code.rechte.schnittstellen: dms:texterkennung kennt das DMS erst ab 0.133.0 – bitte dms: ">=0.133.0" angeben')
    # dms:umwandeln (DMS #577): ab 0.137.0; nur mit code.umwandeln, dem Ereignis datei.umwandeln und Lesen von Dokumenten.
    umwandeln = 'dms:umwandeln' in (rechte.get('schnittstellen') or [])
    typen = code.get('umwandeln') or []
    ereignis = 'datei.umwandeln' in (code.get('ereignisse') or [])
    if umwandeln:
        if not typen:
            fehler.append('code.rechte.schnittstellen: dms:umwandeln braucht code.umwandeln – die Dateitypen, die das Paket umwandelt')
        if rechte.get('dokumente', 'keine') == 'keine':
            fehler.append('code.rechte.schnittstellen: dms:umwandeln braucht auch code.rechte.dokumente: lesen – das Paket liest die Originaldatei')
        if not ereignis:
            fehler.append('code.rechte.schnittstellen: dms:umwandeln braucht das Ereignis datei.umwandeln in code.ereignisse')
    elif typen:
        fehler.append('code.umwandeln: braucht code.rechte.schnittstellen: [dms:umwandeln]')
    elif ereignis:
        fehler.append('code.ereignisse: datei.umwandeln gibt es nur mit code.rechte.schnittstellen: [dms:umwandeln]')
    if (umwandeln or typen or ereignis) and (ab is None or ab < DMS_UMWANDELN_AB):
        fehler.append('code.rechte.schnittstellen: dms:umwandeln kennt das DMS erst ab 0.137.0 – bitte dms: ">=0.137.0" angeben')
    # dms:volltext (DMS #614): ab 0.145.0; nur mit code.volltext, dem Ereignis datei.volltext und Lesen von Dokumenten.
    volltext = 'dms:volltext' in (rechte.get('schnittstellen') or [])
    vtypen = code.get('volltext') or []
    vereignis = 'datei.volltext' in (code.get('ereignisse') or [])
    if volltext:
        if not vtypen:
            fehler.append('code.rechte.schnittstellen: dms:volltext braucht code.volltext – die Dateitypen, für die das Paket den Volltext liefert')
        if rechte.get('dokumente', 'keine') == 'keine':
            fehler.append('code.rechte.schnittstellen: dms:volltext braucht auch code.rechte.dokumente: lesen – das Paket liest die Datei')
        if not vereignis:
            fehler.append('code.rechte.schnittstellen: dms:volltext braucht das Ereignis datei.volltext in code.ereignisse')
    elif vtypen:
        fehler.append('code.volltext: braucht code.rechte.schnittstellen: [dms:volltext]')
    elif vereignis:
        fehler.append('code.ereignisse: datei.volltext gibt es nur mit code.rechte.schnittstellen: [dms:volltext]')
    if (volltext or vtypen or vereignis) and (ab is None or ab < DMS_VOLLTEXT_AB):
        fehler.append('code.rechte.schnittstellen: dms:volltext kennt das DMS erst ab 0.145.0 – bitte dms: ">=0.145.0" angeben')
    # dms:archivfassung (DMS #631): ab 0.149.0; nur mit code.archivfassung.typen, dem Ereignis datei.archivfassung und Lesen
    # von Dokumenten. auswahl (DMS #660, ab 0.176.0) nennt je Art (pdf_text, pdf_scan, bilder; emails ab DMS #946) eine
    # Ja/Nein-Einstellung eines Abschnitts (an: diese Dokumente bekommen eine Archivfassung).
    archiv = 'dms:archivfassung' in (rechte.get('schnittstellen') or [])
    afass = code.get('archivfassung')
    aereignis = 'datei.archivfassung' in (code.get('ereignisse') or [])
    atypen = (afass.get('typen') or []) if isinstance(afass, dict) else []
    if archiv:
        if not atypen:
            fehler.append('code.rechte.schnittstellen: dms:archivfassung braucht code.archivfassung.typen – die Dateitypen, zu denen das Paket ein PDF/A ablegt')
        if rechte.get('dokumente', 'keine') == 'keine':
            fehler.append('code.rechte.schnittstellen: dms:archivfassung braucht auch code.rechte.dokumente: lesen – das Paket liest die Datei und ihren Volltext')
        if not aereignis:
            fehler.append('code.rechte.schnittstellen: dms:archivfassung braucht das Ereignis datei.archivfassung in code.ereignisse')
    elif afass is not None:
        fehler.append('code.archivfassung: braucht code.rechte.schnittstellen: [dms:archivfassung]')
    elif aereignis:
        fehler.append('code.ereignisse: datei.archivfassung gibt es nur mit code.rechte.schnittstellen: [dms:archivfassung]')
    if isinstance(afass, dict) and isinstance(afass.get('auswahl'), dict):
        felder = [f for b in code.get('einstellungen') or [] if isinstance(b, dict) and 'liste' not in b
                  for f in (b.get('felder') or []) if isinstance(f, dict)]
        for art, schluessel in afass['auswahl'].items():
            if not any(f.get('schluessel') == schluessel and f.get('typ') == 'janein' for f in felder):
                fehler.append(f'code.archivfassung.auswahl.{art}: der Schlüssel einer Einstellung vom Typ janein (Abschnitt, keine Liste) – an: diese Dokumente bekommen eine Archivfassung')
        if ab is None or ab < DMS_ARCHIV_AUSWAHL_AB:
            fehler.append('code.archivfassung.auswahl kennt das DMS erst ab 0.176.0 – bitte dms: ">=0.176.0" angeben')
        if 'emails' in afass['auswahl'] and (ab is None or ab < DMS_ARCHIV_EMAILS_AB):
            v = '.'.join(map(str, DMS_ARCHIV_EMAILS_AB))
            fehler.append(f'code.archivfassung.auswahl.emails kennt das DMS erst ab {v} – bitte dms: ">={v}" angeben')
    if (archiv or afass is not None or aereignis) and (ab is None or ab < DMS_ARCHIVFASSUNG_AB):
        fehler.append('code.rechte.schnittstellen: dms:archivfassung kennt das DMS erst ab 0.149.0 – bitte dms: ">=0.149.0" angeben')
    # dms:sicherung-lesen (DMS #585): ab 0.142.0, nur zusammen mit dem Ereignis sicherung.fertig.
    sichern = 'dms:sicherung-lesen' in (rechte.get('schnittstellen') or [])
    fertig = 'sicherung.fertig' in (code.get('ereignisse') or [])
    if sichern and not fertig:
        fehler.append('code.rechte.schnittstellen: dms:sicherung-lesen braucht das Ereignis sicherung.fertig in code.ereignisse')
    if fertig and not sichern:
        fehler.append('code.ereignisse: sicherung.fertig gibt es nur mit code.rechte.schnittstellen: [dms:sicherung-lesen]')
    if (sichern or fertig) and (ab is None or ab < DMS_SICHERUNG_AB):
        fehler.append('code.rechte.schnittstellen: dms:sicherung-lesen kennt das DMS erst ab 0.142.0 – bitte dms: ">=0.142.0" angeben')
    adressen = [f for b in code.get('einstellungen') or [] if isinstance(b, dict) for f in (b.get('felder') or []) if isinstance(f, dict) and f.get('typ') == 'adresse']
    if adressen and vor_antworten:
        fehler.append('code.einstellungen: Einstellungen vom Typ adresse kennt das DMS erst ab 0.124.0 – bitte dms: ">=0.124.0" angeben')
    return fehler


def pruefe_mappentypen(code: dict, paket_id: str, typen: set, dms_bereich: str) -> list[str]:
    """code.mappentypen (DMS #670, #686): Pflicht mit Mappen-Ereignissen, nur mit ihnen; eigene oder fremde lesbare Mappentypen."""
    fehler: list[str] = []
    mit = [e for e in (code.get('ereignisse') or []) if e in MAPPEN_EREIGNISSE]
    liste = code.get('mappentypen') or []
    rechte = code.get('rechte') if isinstance(code.get('rechte'), dict) else {}
    lesen = set(rechte.get('lesen') or []) | set(rechte.get('schreiben') or [])
    if mit and not liste:
        fehler.append(f'code.ereignisse: {", ".join(mit)} braucht code.mappentypen – die eigenen Mappentypen, zu denen das Paket die Ereignisse bekommt')
    if liste and not mit:
        fehler.append('code.mappentypen: nur mit Mappen-Ereignissen in code.ereignisse (' + ', '.join(MAPPEN_EREIGNISSE) + ')')
    fremd = False
    for k in liste:
        if not isinstance(k, str) or not TYPVERWEIS.match(k):
            fehler.append(f'code.mappentypen: „{k}“ – Schlüssel eines eigenen Mappentyps, Verweis wie paket:typ bzw. dms:post oder „*“')
        elif k == 'dms:benutzer':
            fehler.append('code.mappentypen: dms:benutzer ist für Pakete nicht erlaubt – Pakete sehen keine Benutzer')
        elif k == '*':
            fremd = True
            if '*' not in lesen:
                fehler.append('code.mappentypen: „*“ (alle Mappentypen) geht nur mit code.rechte.lesen: ["*"]')
        elif ':' in k and not k.startswith(f'{paket_id}:'):
            fremd = True
            if not ({k, '*'} & lesen):
                fehler.append(f'code.mappentypen: „{k}“ – das Paket muss diesen Mappentyp auch lesen dürfen (code.rechte.lesen)')
        elif k.split(':')[-1] not in typen:
            fehler.append(f'code.mappentypen: Mappentyp „{k}“ gibt es in diesem Paket nicht – fremde Mappentypen bitte mit Präfix, z. B. basis:vertrag')
        elif not ({k, k.split(':')[-1], f'{paket_id}:{k.split(":")[-1]}', '*'} & lesen):
            fehler.append(f'code.mappentypen: „{k}“ – das Paket muss diesen Mappentyp auch lesen dürfen (code.rechte.lesen)')
    if (mit or liste):
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_MAPPEN_EREIGNISSE_AB:
            fehler.append('code.ereignisse: Ereignisse zu Mappen kennt das DMS erst ab 0.153.0 – bitte dms: ">=0.153.0" angeben')
        elif fremd and ab < DMS_FREMDE_MAPPENTYPEN_AB:
            fehler.append('code.mappentypen: fremde Mappentypen und „*“ kennt das DMS erst ab 0.166.0 – bitte dms: ">=0.166.0" angeben')
    return fehler


# Feld-Eigenschaft „für die Erkennung nutzen“ (DMS #336/#391, ab 0.113.0): welche Arten zu welcher Feldart passen
# – wie artenFuer im DMS (shared/src/erkennung.ts). Passwort, Ja/Nein und formatierter Text nie.
DMS_ERKENNUNG_AB = (0, 113, 0)
_TEXTARTEN = {'name', 'vorname', 'nachname', 'funktion', 'nummer', 'iban', 'ustid', 'email', 'internet', 'telefon', 'mobil', 'fax',
              'strasse', 'hausnummer', 'plz', 'ort'}
ERKENNUNG_ARTEN = {
    'text': _TEXTARTEN, 'langtext': _TEXTARTEN, 'zahl': {'nummer', 'plz', 'hausnummer', 'betrag'},
    'betrag': {'betrag'}, 'datum': {'datum'}, 'auswahl': {'auswahl'}, 'referenz': {'verweis'},
}


def pruefe_erkennung(typen: list, dms_bereich: str) -> list[str]:
    """erkennung an Feldern: nur bei geeigneten Feldarten, Art passend zur Feldart; braucht dms: ">=0.113.0"."""
    fehler: list[str] = []
    benutzt = False
    for t in typen:
        if not isinstance(t, dict):
            continue
        for f in t.get('felder') or []:
            if not isinstance(f, dict) or 'erkennung' not in f:
                continue
            wo = f'mappentypen/{t.get("schluessel")}/{f.get("key")}'
            e, typ = f['erkennung'], f.get('typ')
            benutzt = True
            if typ not in ERKENNUNG_ARTEN:
                fehler.append(f'{wo}: erkennung gibt es nicht bei Feldart „{typ}“ (nur {", ".join(sorted(ERKENNUNG_ARTEN))})')
            elif isinstance(e, dict) and e.get('art') is not None and e['art'] not in ERKENNUNG_ARTEN[typ]:
                fehler.append(f'{wo}: erkennung.art „{e["art"]}“ passt nicht zur Feldart „{typ}“ (möglich: {", ".join(sorted(ERKENNUNG_ARTEN[typ]))})')
    if benutzt:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_ERKENNUNG_AB:
            fehler.append('mappentypen: erkennung kennt das DMS erst ab 0.113.0 – bitte dms: ">=0.113.0" angeben')
    return fehler


# Text → Verweis (DMS #534, ab 0.120.0): Ein Verweisfeld nennt mit aus_text das bisherige Textfeld. Das DMS legt den
# Verweis beim Update zusätzlich an; der Administrator wandelt die Angaben danach mit Vorschau um.
DMS_AUS_TEXT_AB = (0, 120, 0)


def pruefe_aus_text(typen: list, dms_bereich: str) -> list[str]:
    """aus_text nur an Verweisfeldern, nicht Pflicht, nennt ein anderes Feld (falls noch im Paket: Text); dms: ">=0.120.0"."""
    fehler: list[str] = []
    benutzt = False
    for t in typen:
        if not isinstance(t, dict):
            continue
        felder = {f.get('key'): f for f in t.get('felder') or [] if isinstance(f, dict)}
        for f in felder.values():
            if 'aus_text' not in f:
                continue
            benutzt = True
            wo = f'mappentypen/{t.get("schluessel")}/{f.get("key")}'
            quelle = felder.get(f['aus_text'])
            if f.get('typ') != 'referenz':
                fehler.append(f'{wo}: aus_text gibt es nur bei Verweisfeldern (typ: referenz)')
            elif f['aus_text'] == f.get('key'):
                fehler.append(f'{wo}: aus_text muss ein anderes Feld nennen – das bisherige Textfeld')
            elif quelle is not None and quelle.get('typ') not in ('text', 'langtext'):
                fehler.append(f'{wo}: aus_text „{f["aus_text"]}“ ist kein Textfeld (text oder langtext)')
            if f.get('pflicht'):
                fehler.append(f'{wo}: ein Verweisfeld mit aus_text darf keine Pflicht sein – sonst passen vorhandene Mappen nach dem Update nicht mehr')
    if benutzt:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_AUS_TEXT_AB:
            fehler.append('mappentypen: aus_text kennt das DMS erst ab 0.120.0 – bitte dms: ">=0.120.0" angeben')
    return fehler


# Auswahlfilter (DMS #172, #173) und „folgt aus“ (DMS #886, ab 0.225.0) an Verweisfeldern. Ablago prüft beim Installieren
# alles noch einmal gegen die echten Mappentypen; hier, was sich im Paket selbst sehen lässt.
DMS_FOLGT_AUS_AB = (0, 225, 0)


def pruefe_verweise(typen: list, dms_bereich: str) -> list[str]:
    """auswahlFilter und folgtAus nur an Verweisfeldern, Felder gibt es (soweit im Paket), keine Kreise; folgtAus braucht dms: ">=0.225.0"."""
    fehler: list[str] = []
    benutzt = False
    eigene = {t.get('schluessel'): t for t in typen if isinstance(t, dict)}

    def felder_von(ziel) -> dict | None:
        """Felder eines Typs dieses Pakets (ziel ohne Präfix); None bei Typen anderer Pakete."""
        t = eigene.get(ziel) if isinstance(ziel, str) and ':' not in ziel else None
        return {f.get('key'): f for f in t.get('felder') or [] if isinstance(f, dict)} if t else None

    for t in typen:
        if not isinstance(t, dict):
            continue
        felder = {f.get('key'): f for f in t.get('felder') or [] if isinstance(f, dict)}
        for f in felder.values():
            wo = f'mappentypen/{t.get("schluessel")}/{f.get("key")}'
            af = f.get('auswahlFilter')
            if af is not None:
                if f.get('typ') != 'referenz':
                    fehler.append(f'{wo}: auswahlFilter gibt es nur bei Verweisfeldern (typ: referenz)')
                elif not isinstance(af, list) or not all(isinstance(b, dict) and b.get('art') == 'feld' and isinstance(b.get('feld'), str) and isinstance(b.get('op'), str) for b in af):
                    fehler.append(f'{wo}: auswahlFilter ist eine Liste von Bedingungen {{ art: feld, feld, op, wert }}')
                else:
                    ziel = felder_von(f.get('ziel'))
                    for b in af:
                        if ziel is not None and b['feld'] not in ziel and not b['feld'].startswith('_'):
                            fehler.append(f'{wo}: auswahlFilter nennt „{b["feld"]}“ – das Feld gibt es im Ziel-Mappentyp nicht')
                        w = b.get('wert')
                        if isinstance(w, dict) and w.get('art') == 'eigenesFeld' and (w.get('feld') == f.get('key') or w.get('feld') not in felder):
                            fehler.append(f'{wo}: auswahlFilter nimmt den Wert aus „{w.get("feld")}“ – das muss ein anderes Feld dieses Mappentyps sein')
            fa = f.get('folgtAus')
            if fa is None:
                continue
            benutzt = True
            if f.get('typ') != 'referenz':
                fehler.append(f'{wo}: folgtAus gibt es nur bei Verweisfeldern (typ: referenz)')
                continue
            if not isinstance(fa, dict) or not isinstance(fa.get('feld'), str) or not isinstance(fa.get('zielFeld'), str):
                fehler.append(f'{wo}: folgtAus braucht feld (ein Verweisfeld dieses Mappentyps) und zielFeld (ein Verweisfeld in dessen Ziel)')
                continue
            q = felder.get(fa['feld'])
            if q is None or q is f:
                fehler.append(f'{wo}: folgtAus.feld „{fa["feld"]}“ ist kein anderes Feld dieses Mappentyps')
            elif q.get('typ') != 'referenz' or q.get('mehrfach'):
                fehler.append(f'{wo}: folgtAus.feld „{fa["feld"]}“ ist kein Verweisfeld mit einer Mappe')
            else:
                ziel = felder_von(q.get('ziel'))
                zf = ziel.get(fa['zielFeld']) if ziel is not None else None
                if ziel is not None and zf is None:
                    fehler.append(f'{wo}: folgtAus.zielFeld „{fa["zielFeld"]}“ gibt es in „{q.get("ziel")}“ nicht')
                elif zf is not None and (zf.get('typ') != 'referenz' or zf.get('mehrfach') or zf.get('ziel') != f.get('ziel')):
                    fehler.append(f'{wo}: folgtAus.zielFeld „{fa["zielFeld"]}“ zeigt nicht auf eine einzelne Mappe vom selben Mappentyp wie dieses Feld')
        # Keine Kreise (a folgt aus b, b folgt aus a).
        kante = {k: f['folgtAus'].get('feld') for k, f in felder.items() if isinstance(f.get('folgtAus'), dict)}
        im_kreis: set = set()
        for start in kante:
            weg, k = [], start
            while k in kante and k not in weg:
                weg.append(k)
                k = kante[k]
            if k in weg:
                im_kreis.update(weg[weg.index(k):])
        if im_kreis:
            fehler.append(f'mappentypen/{t.get("schluessel")}: folgtAus im Kreis: {", ".join(sorted(im_kreis))}')
    if benutzt:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_FOLGT_AUS_AB:
            fehler.append('mappentypen: folgtAus kennt das DMS erst ab 0.225.0 – bitte dms: ">=0.225.0" angeben')
    return fehler


# Feldformate und Datumsgrenzen (DMS #535, ab 0.121.0) – wie shared/src/feldformate.ts im DMS.
DMS_FORMATE_AB = (0, 121, 0)
FELDFORMATE = ('email', 'telefon', 'internetseite', 'iban', 'plz')
HEUTE = 'heute'
# Länge einer IBAN je Land (SWIFT IBAN Registry) – wie IBAN_LAENGEN im DMS (shared/src/erkennung.ts).
IBAN_LAENGEN = {
    'AD': 24, 'AE': 23, 'AL': 28, 'AT': 20, 'AZ': 28, 'BA': 20, 'BE': 16, 'BG': 22, 'BH': 22, 'BI': 27, 'BR': 29, 'BY': 28, 'CH': 21,
    'CR': 22, 'CY': 28, 'CZ': 24, 'DE': 22, 'DJ': 27, 'DK': 18, 'DO': 28, 'EE': 20, 'EG': 29, 'ES': 24, 'FI': 18, 'FK': 18, 'FO': 18,
    'FR': 27, 'GB': 22, 'GE': 22, 'GI': 23, 'GL': 18, 'GR': 27, 'GT': 28, 'HR': 21, 'HU': 28, 'IE': 22, 'IL': 23, 'IQ': 23, 'IS': 26,
    'IT': 27, 'JO': 30, 'KW': 30, 'KZ': 20, 'LB': 28, 'LC': 32, 'LI': 21, 'LT': 20, 'LU': 20, 'LV': 21, 'LY': 25, 'MC': 27, 'MD': 24,
    'ME': 22, 'MK': 19, 'MN': 20, 'MR': 27, 'MT': 31, 'MU': 30, 'NI': 28, 'NL': 18, 'NO': 15, 'OM': 23, 'PK': 24, 'PL': 28, 'PS': 29,
    'PT': 25, 'QA': 29, 'RO': 24, 'RS': 22, 'RU': 33, 'SA': 24, 'SC': 31, 'SD': 18, 'SE': 24, 'SI': 19, 'SK': 24, 'SM': 27, 'SO': 23,
    'ST': 25, 'SV': 28, 'TL': 23, 'TN': 24, 'TR': 26, 'UA': 29, 'VA': 22, 'VG': 24, 'XK': 20, 'YE': 30,
}
DEUTSCHLAND = {'deutschland', 'de', 'deu', 'd', 'germany', 'bundesrepublik deutschland', 'brd'}


def ist_datumsgrenze(v) -> bool:
    """„heute“ oder ein Datum JJJJ-MM-TT."""
    import datetime
    if v == HEUTE:
        return True
    if isinstance(v, datetime.date):  # YAML liest 2000-01-01 ohne Anführungszeichen als Datum
        return True
    if not isinstance(v, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        return False
    try:
        datetime.date.fromisoformat(v)
        return True
    except ValueError:
        return False


def iban_ok(s: str) -> bool:
    i = re.sub(r'\s', '', s).upper()
    if not re.fullmatch(r'[A-Z]{2}\d{2}[A-Z0-9]+', i) or IBAN_LAENGEN.get(i[:2]) != len(i):
        return False
    return int(''.join(str(int(c, 36)) for c in i[4:] + i[:4])) % 97 == 1


def format_fehler(f: dict, wert, werte: dict, alle: list, heute: str) -> str | None:
    """Was an einem Beispielwert nicht zu Format bzw. Grenzen passt; None = passt (oder leer)."""
    if wert is None or wert == '':
        return None
    fmt = f.get('format')
    if f.get('typ') == 'text' and fmt in FELDFORMATE:
        w = str(wert).strip()
        if fmt == 'email' and not re.fullmatch(r'[^\s@<>()\[\]",;:]+@(?:[^\W_](?:[\w-]*[^\W_])?\.)+[^\W\d_]{2,}', w):
            return 'keine gültige E-Mail-Adresse'
        if fmt == 'telefon' and (not re.fullmatch(r'\+?[\d\s/()-]+', w) or len(re.findall(r'\d', w)) < 3):
            return 'keine gültige Telefonnummer (nur Ziffern, + am Anfang, Leerzeichen, /, -, Klammern)'
        if fmt == 'internetseite':
            u = w if re.match(r'[a-z][a-z0-9+.-]*://', w, re.I) else f'https://{w}'
            if re.search(r'\s', u) or not re.fullmatch(r'https?://[^/?#.\s]+(\.[^/?#.\s]+)+(:\d+)?([/?#]\S*)?', u, re.I):
                return 'keine gültige Internetseite'
        if fmt == 'iban' and not iban_ok(w):
            return 'keine gültige IBAN (Länge des Landes oder Prüfziffer)'
        if fmt == 'plz':
            lf = next((x for x in alle if isinstance(x, dict) and x.get('key') == f.get('landFeld')), None)
            land = werte.get(lf['key']) if lf else None
            if land in (None, '') and lf:
                land = lf.get('standard')
            deutsch = not lf or land in (None, '') or str(land).strip().lower() in DEUTSCHLAND
            if deutsch and not re.fullmatch(r'\d{5}', w):
                return 'keine deutsche PLZ (genau 5 Ziffern)'
    if f.get('typ') == 'datum':
        w = str(wert)
        grenze = lambda g: heute if g == HEUTE else (str(g) if ist_datumsgrenze(g) else None)  # noqa: E731
        lo, hi = grenze(f.get('min')), grenze(f.get('max'))
        if lo and w < lo:
            return f'liegt vor {"heute" if f.get("min") == HEUTE else lo}'
        if hi and w > hi:
            return f'liegt nach {"heute" if f.get("max") == HEUTE else hi}'
    return None


def pruefe_formate(typen: list, beispiele: list, dms_bereich: str, heute: str | None = None) -> list[str]:
    """format, landFeld und Datumsgrenzen an Feldern; Beispiele müssen passen; braucht dms: ">=0.121.0"."""
    import datetime
    heute = heute or datetime.date.today().isoformat()
    fehler: list[str] = []
    benutzt = False
    je_typ: dict = {}
    for t in typen:
        if not isinstance(t, dict):
            continue
        felder = [f for f in t.get('felder') or [] if isinstance(f, dict)]
        je_typ[t.get('schluessel')] = felder
        for f in felder:
            wo = f'mappentypen/{t.get("schluessel")}/{f.get("key")}'
            typ = f.get('typ')
            if 'format' in f:
                benutzt = True
                if typ != 'text':
                    fehler.append(f'{wo}: format gibt es nur bei Feldart „text“')
                elif f['format'] not in FELDFORMATE:
                    fehler.append(f'{wo}: format „{f["format"]}“ gibt es nicht (möglich: {", ".join(FELDFORMATE)})')
            if 'landFeld' in f:
                benutzt = True
                lf = next((x for x in felder if x.get('key') == f['landFeld']), None)
                if f.get('format') != 'plz':
                    fehler.append(f'{wo}: landFeld gibt es nur bei format: plz')
                elif not lf or lf is f or lf.get('typ') not in ('text', 'auswahl'):
                    fehler.append(f'{wo}: landFeld „{f["landFeld"]}“ ist kein Text- oder Auswahlfeld dieses Mappentyps')
            if typ == 'datum' and ('min' in f or 'max' in f):
                benutzt = True
                for k in ('min', 'max'):
                    if k in f and not ist_datumsgrenze(f[k]):
                        fehler.append(f'{wo}: {k} bei einem Datum ist „heute“ oder ein Datum JJJJ-MM-TT')
                lo, hi = f.get('min'), f.get('max')
                if ist_datumsgrenze(lo) and ist_datumsgrenze(hi) and HEUTE not in (lo, hi) and str(lo) > str(hi):
                    fehler.append(f'{wo}: min liegt nach max')
    for i, b in enumerate(beispiele or []):
        if not isinstance(b, dict) or not isinstance(b.get('werte'), dict):
            continue
        felder = je_typ.get(b.get('typ'), [])
        for f in felder:
            x = format_fehler(f, b['werte'].get(f.get('key')), b['werte'], felder, heute)
            if x:
                fehler.append(f'beispiele[{i}] ({b.get("typ")}): {f.get("key")} „{b["werte"].get(f.get("key"))}“ – {x}')
    if benutzt:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_FORMATE_AB:
            fehler.append('mappentypen: format, landFeld und Datumsgrenzen kennt das DMS erst ab 0.121.0 – bitte dms: ">=0.121.0" angeben')
    return fehler


def falte(w: str) -> str:
    """Wie das DMS vergleicht: ohne Akzente und Umlautpunkte, ß als ss, klein."""
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', w) if not unicodedata.combining(c)).replace('ß', 'ss').lower()


def pruefe_wortlisten(gruppen: list, dms_bereich: str) -> list[str]:
    """inhalt.wortlisten: keine doppelten Wörter in einer Gruppe (gefaltet), passende DMS-Version."""
    fehler: list[str] = []
    for i, g in enumerate(gruppen, 1):
        woerter = [w.strip() for w in (g.get('woerter') or []) if isinstance(w, str)] if isinstance(g, dict) else []
        gefaltet = [falte(w) for w in woerter]
        doppelt = sorted({w for w, f in zip(woerter, gefaltet) if gefaltet.count(f) > 1})
        if doppelt:
            fehler.append(f'wortlisten[{i}]: Wörter doppelt (Groß-/Kleinschreibung und Umlaute zählen nicht): {", ".join(doppelt)}')
    if gruppen:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_WORTLISTEN_AB:
            fehler.append('inhalt.wortlisten: Wortlisten kennt das DMS erst ab 0.127.0 – bitte dms: ">=0.127.0" angeben')
    return fehler


def pruefe_automatisierungen(liste: list, typen: dict, paket_id: str, abh: set, dms_bereich: str) -> list[str]:
    """inhalt.automatisierungen (DMS #712, Registry #108): bekannte Karten, vorhandene Felder, keine festen Personen
    oder Rollen, Empfänger-Felder verweisen auf Benutzer; passende DMS-Version. typen: Schlüssel → Liste der Felder."""
    fehler: list[str] = []
    gesehen: set[str] = set()
    neu = False  # Karten aus DMS #678 (Zeitplan, Favorit geändert, Benachrichtigungen)
    for i, a in enumerate(liste, 1):
        if not isinstance(a, dict):
            continue
        wo = f'automatisierungen/{a.get("schluessel") or i}'
        if a.get('schluessel') in gesehen:
            fehler.append(f'automatisierungen: Schlüssel „{a.get("schluessel")}“ doppelt')
        gesehen.add(a.get('schluessel'))
        w = a.get('wenn') or {}
        art = w.get('art')
        typ = w.get('typ')
        felder: list | None = None
        if typ is not None:
            t = str(typ)
            if ':' in t:
                pk = t.split(':', 1)[0]
                if pk == 'dms' or (pk != paket_id and pk not in abh):
                    fehler.append(f'{wo}: wenn.typ „{t}“ – nur Mappentypen des Pakets oder seiner Abhängigkeiten')
                elif pk == paket_id:
                    felder = typen.get(t.split(':', 1)[1])
            else:
                felder = typen.get(t)
                if felder is None:
                    fehler.append(f'{wo}: Mappentyp „{t}“ gibt es in diesem Paket nicht')
        feldnamen = {f.get('key'): f for f in (felder or []) if isinstance(f, dict)}
        pruefbar = felder is not None
        if art == 'datum':
            if not typ:
                fehler.append(f'{wo}: „Datum erreicht“ braucht wenn.typ')
            fe = feldnamen.get(w.get('feld'))
            if pruefbar and (not fe or fe.get('typ') != 'datum'):
                fehler.append(f'{wo}: wenn.feld „{w.get("feld")}“ ist kein Datumsfeld von „{typ}“')
            if not isinstance(w.get('vorlauf'), int) or not -3650 <= w['vorlauf'] <= 3650:
                fehler.append(f'{wo}: wenn.vorlauf muss eine ganze Zahl sein (Tage, Wochen oder Monate vorher)')
            if w.get('einheit', 'tage') not in VORLAUF_EINHEITEN:
                fehler.append(f'{wo}: wenn.einheit muss tage, wochen oder monate sein')
        elif art == 'zeitplan':
            neu = True
            if typ:
                fehler.append(f'{wo}: „Zeitplan“ hat keinen Mappentyp – wenn.typ weglassen')
            if w.get('rolle'):
                fehler.append(f'{wo}: wenn.rolle – feste Rollen gibt es in Paketen nicht; „für jeden Benutzer“ gilt für alle aktiven Benutzer')
            if not re.fullmatch(r'([01]\d|2[0-3]):[0-5]\d', str(w.get('uhrzeit', '07:00'))):
                fehler.append(f'{wo}: wenn.uhrzeit als HH:MM, z. B. 07:00')
            tage = w.get('tage', [1, 2, 3, 4, 5, 6, 7])
            if not isinstance(tage, list) or not tage or any(not isinstance(t, int) or not 1 <= t <= 7 for t in tage):
                fehler.append(f'{wo}: wenn.tage als Liste der Wochentage 1 (Montag) bis 7 (Sonntag)')
        elif art in WENN_MAPPE:
            if art == 'favorit.geaendert':
                neu = True
        elif art in WENN_OHNE_TYP:
            if typ:
                fehler.append(f'{wo}: „{art}“ hat keinen Mappentyp – wenn.typ weglassen')
        else:
            fehler.append(f'{wo}: unbekannte Wenn-Karte „{art}“')
        for j, k in enumerate(a.get('dann') or [], 1):
            if not isinstance(k, dict):
                continue
            kw = f'{wo}/dann[{j}]'
            if k.get('art') not in DANN_KARTEN:
                fehler.append(f'{kw}: unbekannte Dann-Karte „{k.get("art")}“ (erlaubt: {", ".join(sorted(DANN_KARTEN))})')
                continue
            if k['art'] in DANN_BENACHRICHTIGUNGEN:
                neu = True
                je = art == 'zeitplan' and w.get('jeBenutzer') is True
                if k['art'] == 'zusammenfassung' and not je:
                    fehler.append(f'{kw}: „Tägliche Zusammenfassung senden“ braucht wenn: zeitplan mit jeBenutzer: true')
                if k['art'] == 'favoriten' and art != 'favorit.geaendert':
                    fehler.append(f'{kw}: „Favoriten-Änderungen melden“ braucht wenn: favorit.geaendert')
                if k['art'] == 'anmeldeschutz':
                    was = k.get('was', 'sammel')
                    if was not in ('sammel', 'konto'):
                        fehler.append(f'{kw}: was muss sammel oder konto sein')
                    elif was == 'sammel' and not (art == 'zeitplan' and not w.get('jeBenutzer')):
                        fehler.append(f'{kw}: Sammelmeldung braucht wenn: zeitplan (nicht je Benutzer)')
                    elif was == 'konto' and art != 'benutzer.gesperrt':
                        fehler.append(f'{kw}: Kontosperre melden braucht wenn: benutzer.gesperrt')
            if k['art'] == 'feld':
                if not typ:
                    fehler.append(f'{kw}: „Feld ändern“ braucht eine Wenn-Karte mit Mappentyp')
                for key in (k.get('werte') or {}):
                    if pruefbar and key not in feldnamen:
                        fehler.append(f'{kw}: Feld „{key}“ gibt es an „{typ}“ nicht')
            if k['art'] == 'aufgabe':
                if not str(k.get('text') or '').strip():
                    fehler.append(f'{kw}: Text fehlt')
                if k.get('als', 'aufgabe') not in ('aufgabe', 'benachrichtigung'):
                    fehler.append(f'{kw}: als muss aufgabe oder benachrichtigung sein')
                empf = k.get('empfaenger') or []
                if not empf:
                    fehler.append(f'{kw}: Empfänger fehlt')
                for e in empf:
                    ea = e.get('art') if isinstance(e, dict) else None
                    if ea in ('person', 'rolle'):
                        fehler.append(f'{kw}: feste Personen und Rollen gibt es in Paketen nicht – Empfänger aus einem Feld, aus dem Ereignis oder der Ersteller')
                    elif ea == 'feld':
                        fe = feldnamen.get(e.get('feld'))
                        if pruefbar and (not fe or fe.get('typ') != 'referenz' or fe.get('ziel') != 'dms:benutzer'):
                            fehler.append(f'{kw}: Empfänger-Feld „{e.get("feld")}“ muss ein Verweis auf Benutzer sein (ziel: dms:benutzer)')
                        if e.get('sonst') not in (None, 'ersteller'):
                            fehler.append(f'{kw}: sonst darf nur ersteller sein')
                    elif ea == 'ereignis':
                        if e.get('feld') not in PERSONEN_IM_EREIGNIS.get(str(art), set()):
                            fehler.append(f'{kw}: „{art}“ bringt keine Person „{e.get("feld")}“ mit')
                    elif ea == 'ersteller':
                        if not typ:
                            fehler.append(f'{kw}: „wer die Mappe angelegt hat“ braucht eine Wenn-Karte mit Mappentyp')
                    else:
                        fehler.append(f'{kw}: unbekannter Empfänger „{ea}“')
    if liste:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_AUTOMATISIERUNGEN_AB:
            fehler.append('inhalt.automatisierungen: Automatisierungen in Paketen kennt Ablago erst ab 0.177.0 – bitte dms: ">=0.177.0" angeben')
        elif neu and ab < DMS_BENACHRICHTIGUNGEN_AB:
            fehler.append('inhalt.automatisierungen: „Zeitplan“, „Favorit geändert“ und die Karten der Benachrichtigungen kennt Ablago erst ab 0.181.0 – bitte dms: ">=0.181.0" angeben')
    # Ab 0.177.0 erinnert ein Datumsfeld mit frist nicht mehr selbst: Jede Frist braucht eine mitgelieferte Automatisierung.
    ab = dms_untergrenze(dms_bereich)
    if ab is not None and ab >= DMS_AUTOMATISIERUNGEN_AB:
        erinnert = {(str((a.get('wenn') or {}).get('typ')), (a.get('wenn') or {}).get('feld')) for a in liste if isinstance(a, dict) and (a.get('wenn') or {}).get('art') == 'datum'}
        for t, fs in typen.items():
            for f in fs or []:
                if isinstance(f, dict) and f.get('frist') and (t, f.get('key')) not in erinnert and (f'{paket_id}:{t}', f.get('key')) not in erinnert:
                    fehler.append(f'mappentypen/{t}/{f.get("key")}: Frist ohne mitgelieferte Automatisierung „Datum erreicht“ – ab Ablago 0.177.0 erinnert das Feld nicht mehr selbst')
    return fehler


def beispiel_verweise(werte: dict) -> list[str]:
    """Verweise auf andere Beispiele in den Werten (#347 im DMS): { beispiel: x } oder Listen davon."""
    erg = []
    for w in (werte or {}).values():
        for x in (w if isinstance(w, list) else [w]):
            if isinstance(x, dict) and set(x) == {'beispiel'} and isinstance(x['beispiel'], str):
                erg.append(x['beispiel'])
    return erg


def pruefe_beispiel_verweise(beispiele: list, paket_id: str, abh: set) -> list[str]:
    """Schlüssel eindeutig, Ziele vorhanden bzw. aus einer Abhängigkeit, keine Kreise (braucht DMS ab 0.79.0)."""
    fehler: list[str] = []
    bsp = [b for b in beispiele if isinstance(b, dict)]
    schl = [b['schluessel'] for b in bsp if b.get('schluessel')]
    for s in sorted({s for s in schl if schl.count(s) > 1}):
        fehler.append(f'beispiele: Schlüssel „{s}“ doppelt')
    eigene = set(schl)
    kanten: dict[str, list[str]] = {}
    for i, b in enumerate(bsp, 1):
        for z in beispiel_verweise(b.get('werte')):
            paket, s = (z.split(':', 1) if ':' in z else (paket_id, z))
            if paket == paket_id:
                if s not in eigene:
                    fehler.append(f'beispiele[{i}]: Verweis auf das Beispiel „{s}“, das es im Paket nicht gibt')
                elif b.get('schluessel'):
                    kanten.setdefault(b['schluessel'], []).append(s)
            elif paket == 'dms' or paket not in abh:
                fehler.append(f'beispiele[{i}]: Verweis „{z}“ – das Paket „{paket}“ steht nicht unter abhaengigkeiten')
    # Kreise nur zwischen Beispielen mit Schlüssel möglich (ohne Schlüssel zeigt niemand darauf).
    farbe: dict[str, int] = {}
    def kreis(k: str) -> bool:
        farbe[k] = 1
        for z in kanten.get(k, []):
            if farbe.get(z) == 1 or (farbe.get(z) is None and kreis(z)):
                return True
        farbe[k] = 2
        return False
    if any(farbe.get(k) is None and kreis(k) for k in list(kanten)):
        fehler.append('beispiele: Die Verweise zwischen den Beispielen bilden einen Kreis – ein Verweis muss weg')
    return fehler


def dateiart(name: str, kopf: bytes) -> str | None:
    """Art einer Beispiel-Datei am Inhalt (wie beispielDateiart in Ablago): PDF, PNG oder JPEG, und nur mit passender Endung."""
    erwartet = BEISPIEL_ENDUNGEN.get(name.rsplit('.', 1)[-1].lower()) if '.' in name else None
    ist = ('application/pdf' if kopf.startswith(b'%PDF-') else 'image/png' if kopf.startswith(b'\x89PNG') else
           'image/jpeg' if kopf.startswith(b'\xff\xd8\xff') else None)
    return ist if erwartet and ist == erwartet else None


def mb(n: int) -> str:
    return f'{n / 1048576:.1f} MB' if n >= 1048576 else f'{max(1, round(n / 1024))} KB'


def pruefe_beispiel_dokumente(ordner: Path, beispiele: list, typen: list, paket_id: str, dms_bereich: str) -> list[str]:
    """Beispiel-Dokumente (motom001/dms#878): Jede genannte Datei liegt unter inhalt/beispiele/, ist PDF, PNG oder JPEG
    und nicht zu groß; jede Datei dort ist auch genannt; zusammen passen sie unter die Paketgrenze; das Register gibt es
    (bei eigenen Mappentypen) und das Paket verlangt Ablago ab 0.223.0."""
    fehler: list[str] = []
    genannt: set[str] = set()
    eigene = {t.get('schluessel'): t for t in typen if isinstance(t, dict)}
    for i, b in enumerate(beispiele or []):
        if not isinstance(b, dict) or not isinstance(b.get('dokumente'), list):
            continue
        typ = str(b.get('typ', ''))
        eigen = eigene.get(typ.split(':', 1)[1] if typ.startswith(f'{paket_id}:') else typ) if (':' not in typ or typ.startswith(f'{paket_id}:')) else None
        dokreg = [r.get('key') for r in (eigen or {}).get('register') or [] if isinstance(r, dict) and r.get('art') == 'dokumente']
        for j, d in enumerate(b['dokumente']):
            if not isinstance(d, dict):
                continue
            wo = f'beispiele[{i}].dokumente[{j}]'
            datei = str(d.get('datei', ''))
            if not BEISPIEL_PFAD.match(datei) or '..' in datei.split('/'):
                fehler.append(f'{wo}: „{datei}“ muss unter inhalt/beispiele/ liegen (Pfad relativ zu inhalt/, z. B. beispiele/heizung/vertrag.pdf)')
                continue
            genannt.add(datei)
            pfad = ordner / 'inhalt' / datei
            if not pfad.is_file():
                fehler.append(f'{wo}: inhalt/{datei} fehlt')
                continue
            groesse = pfad.stat().st_size
            if not groesse:
                fehler.append(f'{wo}: inhalt/{datei} ist leer')
            elif groesse > BEISPIEL_DATEI_MAX:
                fehler.append(f'{wo}: inhalt/{datei} ist {mb(groesse)} groß – höchstens {BEISPIEL_DATEI_MAX // 1048576} MB je Datei (wie beim Hochladen in Ablago)')
            with pfad.open('rb') as f:
                if not dateiart(datei, f.read(8)):
                    fehler.append(f'{wo}: inhalt/{datei} ist kein PDF, PNG oder JPEG, oder die Endung passt nicht zum Inhalt')
            if eigen is not None:
                reg = d.get('register')
                if (reg and reg not in dokreg) or (not reg and not dokreg):
                    fehler.append(f'{wo}: Der Mappentyp „{typ}“ hat kein Dokumentenregister „{reg or "–"}“')
    unten = ordner / BEISPIEL_ORDNER
    vorhanden = {p.relative_to(ordner / 'inhalt').as_posix(): p.stat().st_size for p in sorted(unten.rglob('*')) if p.is_file()} if unten.is_dir() else {}
    for rel in sorted(set(vorhanden) - genannt):
        fehler.append(f'inhalt/{rel}: liegt unter inhalt/beispiele/, aber kein Beispiel nennt die Datei unter dokumente')
    summe = sum(vorhanden.values())
    if summe > PAKET_MAX:
        fehler.append(f'inhalt/beispiele/: zusammen {mb(summe)} – höchstens {PAKET_MAX // 1048576} MB je Paket (Grenze des DMS, DMS #644)')
    if genannt:
        ab = dms_untergrenze(dms_bereich)
        if ab is None or ab < DMS_BEISPIEL_DOKUMENTE_AB:
            fehler.append('beispiele: dokumente kennt Ablago erst ab 0.223.0 – bitte dms: ">=0.223.0" angeben')
    return fehler


def beispiel_groessen(ordner: Path) -> list[str]:
    """Größe der Beispiel-Dokumente je Datei und gesamt (Registry #137), als Hinweis bei jeder Prüfung."""
    unten = ordner / BEISPIEL_ORDNER
    if not unten.is_dir():
        return []
    dateien = [(p.relative_to(ordner).as_posix(), p.stat().st_size) for p in sorted(unten.rglob('*')) if p.is_file()]
    if not dateien:
        return []
    summe = sum(g for _, g in dateien)
    h = [f'Beispiel-Dokumente: {len(dateien)} Datei(en), zusammen {mb(summe)} von höchstens {PAKET_MAX // 1048576} MB je Paket – '
         + ', '.join(f'{n} {mb(g)}' for n, g in dateien)]
    gesamt = sum(p.stat().st_size for p in ordner.rglob('*') if p.is_file())
    if gesamt > GIT_DATEI_MAX * 0.9:
        h.append(f'Paket zusammen {mb(gesamt)}: Ein Archiv über 100 MB nimmt git nicht an – der Katalog auf gh-pages (Registry #133) '
                 'ginge dann nicht. Beispiel-Dokumente klein halten (z. B. PDF verkleinern, Bilder als JPEG).')
    return h


def pruefe_einstellungen(code: dict, paket_id: str, typen: set, abh: set, dms_bereich: str = '') -> list[str]:
    """Einstellungen und Aktionen im Manifest (code.einstellungen, code.aktionen) über das Schema hinaus."""
    fehler: list[str] = []

    def typ_ok(v: str, wo: str):
        if ':' in v:
            paket = v.split(':', 1)[0]
            if paket == 'dms':
                if (f := dms_fehler(v, wo)):
                    fehler.append(f)
            elif paket != paket_id and paket not in abh:
                fehler.append(f'{wo}: „{v}“ verweist auf Paket „{paket}“, das nicht unter abhaengigkeiten steht')
            elif paket == paket_id and v.split(':', 1)[1] not in typen:
                fehler.append(f'{wo}: Mappentyp „{v}“ gibt es in diesem Paket nicht')
        elif v not in typen:
            fehler.append(f'{wo}: Mappentyp „{v}“ gibt es in diesem Paket nicht (anderes Paket: <paket>:<schluessel>)')

    def felder(eintraege: list, wo: str, liste: bool = False):
        gesehen = set()
        for f in eintraege or []:
            if not isinstance(f, dict):
                continue
            s, typ, w = f.get('schluessel'), f.get('typ'), f'{wo}/{f.get("schluessel")}'
            if s in gesehen:
                fehler.append(f'{wo}: Schlüssel „{s}“ doppelt')
            gesehen.add(s)
            if typ in ('auswahl', 'mehrfachauswahl') and not f.get('optionen'):
                fehler.append(f'{w}: {typ} braucht optionen')
            if f.get('beispiel') is not None and typ != 'adresse':
                fehler.append(f'{w}: beispiel gibt es nur bei typ adresse')
            if typ == 'adresse':
                if liste:
                    fehler.append(f'{w}: adresse geht nur in einem Abschnitt, nicht in einer Liste')
                if 'standard' in f:
                    fehler.append(f'{w}: adresse hat keine Vorgabe – der Administrator trägt die Dienst-Adresse selbst ein und bestätigt sie (höchstens beispiel)')
                    continue
            if f.get('mehrfach') is not None and (f.get('mehrfach') is not True or typ not in MEHRFACH_VERWEISE):
                fehler.append(f'{w}: mehrfach: true gibt es nur bei {", ".join(MEHRFACH_VERWEISE)}')
            if f.get('mappentyp') is not None:
                if typ != 'feld':
                    fehler.append(f'{w}: mappentyp gibt es nur bei typ feld')
                else:
                    typ_ok(str(f['mappentyp']), w)
            if 'standard' not in f:
                continue
            st = f['standard']
            if typ == 'geheim':
                fehler.append(f'{w}: geheim hat keine Vorgabe (Zugangsdaten nie als standard)')
            elif typ in VERWEISE:
                fehler.append(f'{w}: Verweise ({typ}) haben keine Vorgabe – die Ids gibt es erst im DMS')
            elif typ in ('text', 'mehrzeilig') and not isinstance(st, str):
                fehler.append(f'{w}: standard muss Text sein')
            elif typ == 'zahl' and (isinstance(st, bool) or not isinstance(st, (int, float)) or ('min' in f and st < f['min']) or ('max' in f and st > f['max'])):
                fehler.append(f'{w}: standard muss eine Zahl (zwischen min und max) sein')
            elif typ == 'janein' and not isinstance(st, bool):
                fehler.append(f'{w}: standard muss true oder false sein')
            elif typ == 'datum' and not (isinstance(st, str) and DATUM.match(st)):
                fehler.append(f'{w}: standard muss ein Datum JJJJ-MM-TT sein')
            elif typ == 'auswahl' and st not in (f.get('optionen') or []):
                fehler.append(f'{w}: standard steht nicht in optionen')
            elif typ == 'mehrfachauswahl' and not (isinstance(st, list) and all(x in (f.get('optionen') or []) for x in st)):
                fehler.append(f'{w}: standard muss eine Liste aus optionen sein')
        return gesehen

    oben: set = set()
    for b in code.get('einstellungen') or []:
        if not isinstance(b, dict):
            continue
        if 'liste' in b:
            if b['liste'] in oben:
                fehler.append(f'code.einstellungen: Schlüssel „{b["liste"]}“ doppelt')
            oben.add(b['liste'])
            felder(b.get('felder'), f'code.einstellungen/{b["liste"]}', liste=True)
        else:
            for s in felder(b.get('felder'), f'code.einstellungen/{b.get("abschnitt")}'):
                if s in oben:
                    fehler.append(f'code.einstellungen: Schlüssel „{s}“ doppelt')
                oben.add(s)
    # mehrfach / schliesst_aus (DMS #658): ab 0.179.0; schliesst_aus nennt ein anderes Feld desselben Verweistyps im Abschnitt.
    alle = [(b, f) for b in code.get('einstellungen') or [] if isinstance(b, dict) for f in (b.get('felder') or []) if isinstance(f, dict)]
    abschnitt = {f.get('schluessel'): f for b, f in alle if 'liste' not in b}
    for b, f in alle:
        if 'mehrfach' in f or 'schliesst_aus' in f:
            ab = dms_untergrenze(dms_bereich)
            if ab is None or ab < DMS_EINSTELLUNG_MEHRFACH_AB:
                fehler.append(f'code.einstellungen/{f.get("schluessel")}: mehrfach und schliesst_aus kennt das DMS erst ab 0.179.0 – bitte dms: ">=0.179.0" angeben')
        if 'schliesst_aus' in f:
            g = abschnitt.get(f['schliesst_aus'])
            if 'liste' in b or g is None or g is f or g.get('typ') != f.get('typ') or f.get('typ') not in MEHRFACH_VERWEISE:
                fehler.append(f'code.einstellungen/{f.get("schluessel")}: schliesst_aus „{f["schliesst_aus"]}“ muss ein anderes Feld eines Abschnitts mit demselben Verweistyp sein')
    anzahl = sum(1 for b in code.get('einstellungen') or [] if isinstance(b, dict) and 'liste' not in b for f in (b.get('felder') or []) if isinstance(f, dict) and f.get('typ') == 'adresse')
    if anzahl > 1:
        fehler.append('code.einstellungen: höchstens eine Einstellung vom Typ adresse je Paket')
    aktionen = [a.get('schluessel') for a in code.get('aktionen') or [] if isinstance(a, dict)]
    for s in {x for x in aktionen if aktionen.count(x) > 1}:
        fehler.append(f'code.aktionen: Schlüssel „{s}“ doppelt')
    return fehler


# Beschriftungen je Sprache (Ablago #728, Registry #135): Form prüft das Schema; hier, was es nicht kann.
SPRACHKENNUNG = re.compile(r'^[a-z]{2,3}(-[A-Z]{2})?$')


def pruefe_beschriftungen(typen: list, sichten: list) -> list[str]:
    """Schlüssel unter optionen gibt es im Feld (fester Wert); optionen nur bei Auswahlfeldern; Deutsch nur für optionen."""
    fehler: list[str] = []

    def deutsch(b, wo: str, nur_optionen: bool):
        de = (b or {}).get('de') if isinstance(b, dict) else None
        if isinstance(de, dict) and any(k != 'optionen' for k in de):
            fehler.append(f'{wo}: beschriftungen.de nur für optionen – {", ".join(sorted(k for k in de if k != "optionen"))} '
                          'steht als deutscher Grundtext schon am Eintrag')
        elif isinstance(de, dict) and not nur_optionen:
            fehler.append(f'{wo}: beschriftungen.de gibt es nur an Auswahlfeldern (für optionen)')

    for t in typen:
        if not isinstance(t, dict):
            continue
        s = t.get('schluessel')
        deutsch(t.get('beschriftungen'), f'mappentypen/{s}', False)
        for f in t.get('felder', []) or []:
            if not isinstance(f, dict) or not isinstance(f.get('beschriftungen'), dict):
                continue
            wo = f'mappentypen/{s}/{f.get("key")}'
            optionen = set(f.get('optionen') or [])
            deutsch(f['beschriftungen'], wo, f.get('typ') == 'auswahl')
            for spr, teile in f['beschriftungen'].items():
                opt = (teile or {}).get('optionen') if isinstance(teile, dict) else None
                if opt is None:
                    continue
                if f.get('typ') != 'auswahl':
                    fehler.append(f'{wo}: beschriftungen.{spr}.optionen gibt es nur bei Auswahlfeldern')
                    continue
                for w in opt:
                    if w not in optionen:
                        fehler.append(f'{wo}: beschriftungen.{spr}.optionen nennt „{w}“, das es unter optionen nicht gibt')
        for r in t.get('register', []) or []:
            if isinstance(r, dict):
                deutsch(r.get('beschriftungen'), f'mappentypen/{s}/register/{r.get("key")}', False)
    for v in sichten:
        if isinstance(v, dict):
            deutsch(v.get('beschriftungen'), f'sichten/{v.get("schluessel")}', False)
    return fehler


# Sprachpakete (Ablago #731, Registry #116): nur Texte. Dieselben Grenzen wie Ablago (shared/src/sprachpaket.ts).
DMS_SPRACHPAKETE_AB = (0, 203, 0)
SPRACHTEXT_MAX = 4000
SPRACHTEXTE_MAX = 4 * 1024 * 1024
SPRACHPAKET_DATEI = re.compile(r'^(manifest\.yaml|README(\.[a-z]{2})?\.md|LICENSE(\.[A-Za-z]{1,10})?|NOTICE|CHANGELOG\.md|'
                               r'tests/[A-Za-z0-9._-]{1,80}\.(ya?ml|json|md)|texte/[a-z][a-z0-9-]{0,40}\.json|beschriftungen/[a-z][a-z0-9_]{1,39}(\.[a-z][a-z0-9_]{0,19})?\.yaml)$')
STEUERZEICHEN = re.compile('[\x00-\x08\x0b-\x1f\x7f\u2028\u2029]')
# HTML erkennen ohne die Texte von Ablago: Tags bekannter Elemente, Ereignis-Attribute, javascript:. Den genauen Abgleich
# („spitze Klammern nur, wo das Deutsche sie hat“) macht Ablago beim Installieren und werkzeuge/sprachen.py.
HTML = re.compile(r'</?(a|abbr|b|body|br|button|code|div|em|embed|form|h[1-6]|head|hr|html|i|iframe|img|input|li|link|meta|object|ol|p|'
                  r'pre|script|small|span|strong|style|svg|table|td|th|tr|u|ul|video|audio|source|math|base|frame|frameset|template)\b[^>]*>'
                  r'|\bon[a-z]+\s*=|javascript:', re.I)


def sprachpaket_id(kennung: str) -> str:
    """Paket-Id eines Sprachpakets: sprache_<kennung>, z. B. sprache_fr, sprache_pt_br."""
    return 'sprache_' + kennung.lower().replace('-', '_')


def pruefe_sprachtext(text, wo: str) -> str | None:
    if not isinstance(text, str):
        return f'{wo}: kein Text'
    if len(text) > SPRACHTEXT_MAX:
        return f'{wo}: länger als {SPRACHTEXT_MAX} Zeichen'
    if STEUERZEICHEN.search(text):
        return f'{wo}: enthält Steuerzeichen'
    if HTML.search(text):
        return f'{wo}: enthält HTML – Sprachpakete enthalten nur Texte'
    return None


def pruefe_sprachpaket(ordner: Path, m: dict, pakete: Path | None = None) -> list[str]:
    """Paketart „Sprache“: Manifest, erlaubte Dateien, Texte, Beschriftungen der Standardpakete (gegen pakete/)."""
    fehler: list[str] = []
    s = m.get('sprache') if isinstance(m.get('sprache'), dict) else {}
    kennung = str(s.get('kennung', ''))
    if 'code' in m:
        fehler.append('manifest.yaml: ein Sprachpaket enthält keinen Code (code)')
    if m.get('inhalt'):
        fehler.append('manifest.yaml: inhalt bleibt bei einem Sprachpaket leer (inhalt: {})')
    if m.get('abhaengigkeiten') or m.get('ergaenzt'):
        fehler.append('manifest.yaml: ein Sprachpaket hängt von keinem Paket ab und ergänzt keins')
    ab = dms_untergrenze(str(m.get('dms', '')))
    if ab is None or ab < DMS_SPRACHPAKETE_AB:
        fehler.append('manifest.yaml: Sprachpakete kennt Ablago erst ab 0.203.0 – bitte dms: ">=0.203.0" angeben')
    if SPRACHKENNUNG.fullmatch(kennung) and ordner.name != 'vorlage' and m.get('id') != sprachpaket_id(kennung):
        fehler.append(f'manifest.yaml: ein Sprachpaket heißt {sprachpaket_id(kennung)} (sprache_<kennung>)')
    if 'kategorien' in m and 'sprachen' not in (m.get('kategorien') or []):
        fehler.append('manifest.yaml: kategorien eines Sprachpakets enthalten sprachen')
    if 'kuerzel' in m and kennung and str(m['kuerzel']) != kennung.split('-')[0].upper():
        fehler.append(f'manifest.yaml: kuerzel eines Sprachpakets ist die Sprachkennung in Großbuchstaben ({kennung.split("-")[0].upper()})')
    texte_gesamt = 0
    anzahl = 0
    for datei in sorted(p for p in ordner.rglob('*') if p.is_file()):
        rel = datei.relative_to(ordner).as_posix()
        if not SPRACHPAKET_DATEI.fullmatch(rel):
            fehler.append(f'{rel}: gehört nicht in ein Sprachpaket (nur texte/<bereich>.json, beschriftungen/<paket>.yaml, README, LICENSE, CHANGELOG, tests/)')
            continue
        if rel.startswith('texte/'):
            try:
                d = json.loads(datei.read_text(encoding='utf-8'))
            except Exception as e:  # noqa: BLE001
                fehler.append(f'{rel}: kein gültiges JSON ({e})')
                continue
            fehler += schema_fehler(inhalt_validator('sprachtexte'), d, rel)
            if isinstance(d, dict):
                for k, v in d.items():
                    if (f := pruefe_sprachtext(v, f'{rel}: „{k}“')):
                        fehler.append(f)
                    elif isinstance(v, str) and v.strip():
                        anzahl += 1
                        texte_gesamt += len(k.encode()) + len(v.encode())
        elif rel.startswith('beschriftungen/'):
            fehler += pruefe_sprachbeschriftung(datei, rel, pakete or WURZEL / 'pakete')
    if texte_gesamt > SPRACHTEXTE_MAX:
        fehler.append(f'texte/: zusammen größer als {SPRACHTEXTE_MAX // 1048576} MB')
    if not anzahl and not (ordner / 'beschriftungen').is_dir():
        fehler.append('texte/: ein Sprachpaket braucht Texte oder Beschriftungen')
    return fehler


def pruefe_sprachbeschriftung(datei: Path, rel: str, pakete: Path) -> list[str]:
    """beschriftungen/<paket>.yaml: Schema, kein HTML, und jeder Schlüssel gibt es im Paket der Registry."""
    fehler: list[str] = []
    b = lies_yaml(datei, fehler)
    if b is None:
        return fehler
    fehler += schema_fehler(inhalt_validator('sprachbeschriftung'), b, rel)
    if not isinstance(b, dict):
        return fehler
    pid = datei.stem
    ziel = pakete / pid / 'manifest.yaml'
    if not ziel.exists():
        return fehler + [f'{rel}: Paket „{pid}“ gibt es in der Registry nicht']
    zm = yaml.safe_load(ziel.read_text(encoding='utf-8')) or {}
    zi = zm.get('inhalt') or {}
    typen = {t['schluessel']: t for t in (yaml.safe_load((ziel.parent / zi['mappentypen']).read_text(encoding='utf-8')) or [] if zi.get('mappentypen') else []) if isinstance(t, dict)}
    sichten = {s['schluessel'] for s in (yaml.safe_load((ziel.parent / zi['sichten']).read_text(encoding='utf-8')) or [] if zi.get('sichten') else []) if isinstance(s, dict)}

    def texte(o, wo):
        if isinstance(o, dict):
            for k, v in o.items():
                texte(v, f'{wo}.{k}')
        elif isinstance(o, str) and (f := pruefe_sprachtext(o, wo)):
            fehler.append(f)
    texte(b, rel)
    for s, x in (b.get('mappentypen') or {}).items():
        t = typen.get(s)
        if not t:
            fehler.append(f'{rel}: Mappentyp „{s}“ gibt es in {pid} nicht')
            continue
        felder = {f.get('key'): f for f in t.get('felder', []) if isinstance(f, dict)}
        register = {r.get('key') for r in t.get('register', []) if isinstance(r, dict)}
        for k, f in ((x or {}).get('felder') or {}).items():
            if k not in felder:
                fehler.append(f'{rel}: {s}: Feld „{k}“ gibt es in {pid} nicht')
                continue
            for w in ((f or {}).get('optionen') or {}):
                if w not in (felder[k].get('optionen') or []):
                    fehler.append(f'{rel}: {s}.{k}: Option „{w}“ gibt es in {pid} nicht')
        for k in ((x or {}).get('register') or {}):
            if k not in register:
                fehler.append(f'{rel}: {s}: Register „{k}“ gibt es in {pid} nicht')
    for k in (b.get('sichten') or {}):
        if k not in sichten:
            fehler.append(f'{rel}: Ansicht „{k}“ gibt es in {pid} nicht')
    return fehler


# ---------- Paketsprache (Registry #157): gleiche Kennungen, Text-Vorlagen ----------

# Gleiche Kennung für gleiche Bedeutung über alle Mappentypen (REGELN.md, „Gleiche Kennungen“), damit Trefferlisten,
# Ansichten und die erweiterte Suche über mehrere Typen dieselben Spalten zeigen. Je Kennung: Feldart(en), Bedeutung
# und Schlüssel, die dasselbe meinen und künftig nicht mehr neu entstehen sollen.
KENNUNGEN = {
    'von': ({'referenz'}, 'Gegenseite, von der etwas kommt: Anbieter, Rechnungssteller, Verkäufer, Vermieter, Versicherer, Absender',
            {'absender', 'vertragspartner', 'anbieter', 'aussteller', 'rechnungssteller', 'verkaeufer', 'vermieter', 'versicherer', 'lieferant'}),
    'an': ({'referenz'}, 'wer es bekommt: Kunde, Rechnungsempfänger, Käufer, Mieter, Versicherungsnehmer, Empfänger',
           {'empfaenger', 'fuer', 'kunde', 'rechnungsempfaenger', 'kaeufer', 'versicherungsnehmer'}),
    'betrag': ({'betrag'}, 'Geldbetrag (bei Rechnungen brutto)', {'summe', 'preis', 'gesamtbetrag', 'bruttobetrag', 'betrag_brutto', 'betrag_eur'}),
    'datum': ({'datum'}, 'Datum des Schriftstücks', {'rechnungsdatum', 'belegdatum', 'dokumentdatum', 'ausstellungsdatum', 'briefdatum'}),
    'betrifft': ({'referenz'}, 'Gegenstand, um den es geht (Fahrzeug, Wohnung, Vertrag …)', {'bezug', 'gegenstand_verweis', 'betreff_verweis'}),
    'steuerjahr': ({'referenz'}, 'Verweis auf das Steuerjahr', {'steuer_jahr', 'veranlagungsjahr'}),
    'zustaendig': ({'referenz'}, 'Benutzer, der sich kümmert (dms:benutzer)', {'verantwortlich', 'zustaendigkeit', 'bearbeiter', 'kuemmert_sich'}),
    'verbleib_original': ({'referenz'}, 'wo das Original liegt (basis:ablageort)', {'original', 'verbleib', 'originale', 'ablageort_original'}),
    'person_verweis': ({'referenz'}, 'Person des Haushalts bzw. Betriebs (basis:person)', set()),
    'bezeichnung': ({'text'}, 'kurzer Name der Mappe („Handyvertrag Jonas“)', {'name_kurz', 'kurzname'}),
    'art': ({'auswahl', 'referenz'}, 'was es ist (Auswahl oder Verweis auf eine Art)', {'typ', 'kategorie', 'sorte'}),
    'beginn': ({'datum'}, 'Beginn eines Zeitraums', {'start', 'startdatum', 'von_datum', 'gueltig_ab'}),
    'ende': ({'datum'}, 'Ende eines Zeitraums', {'enddatum', 'bis_datum', 'gueltig_bis', 'ablauf'}),
    'kuendigen_bis': ({'datum'}, 'letzter Tag zum Kündigen (Frist)', {'kuendigung_bis', 'kuendigungsfrist_bis'}),
    'vertragsnummer': ({'text'}, 'Vertragsnummer der Gegenseite', {'vertrags_nr', 'vertragsnr'}),
    'zahlweise': ({'auswahl'}, 'monatlich, vierteljährlich, jährlich …', {'zahlungsweise', 'zahlungsrhythmus'}),
    'notiz': ({'langtext', 'formatiert'}, 'freie Bemerkungen', {'bemerkung', 'bemerkungen', 'anmerkung', 'anmerkungen', 'kommentar'}),
}
STATT = {alt: neu for neu, (_, _, alte) in KENNUNGEN.items() for alt in alte}
# Zeiträume heißen beginn/ende; von/an/bis bleiben den Parteien vorbehalten (von/an) bzw. sind keine eigene Kennung.
ZEITRAUM = {'von': 'beginn', 'bis': 'ende'}


def kennung_hinweise(typen: list, neu: set[tuple[str, str]] | None) -> list[str]:
    """Hinweise zu Kennungen (Registry #157): nur für neue Felder (neu = {(typ, feld)}, None = alle Felder)."""
    h: list[str] = []
    for t in typen:
        if not isinstance(t, dict):
            continue
        ts = str(t.get('schluessel', ''))
        for f in t.get('felder') or []:
            if not isinstance(f, dict) or not isinstance(f.get('key'), str):
                continue
            k, art = f['key'], f.get('typ')
            if neu is not None and (ts, k) not in neu:
                continue
            wo = f'mappentypen.{ts}.{k}'
            if k in STATT:
                h.append(f'{wo}: für „{KENNUNGEN[STATT[k]][1]}“ heißt die Kennung „{STATT[k]}“ (REGELN.md, „Gleiche Kennungen“)')
            elif k in ZEITRAUM and art == 'datum':
                h.append(f'{wo}: ein Zeitraum heißt „{ZEITRAUM[k]}“ – „von“ und „an“ sind die Parteien (REGELN.md, „Gleiche Kennungen“)')
            elif k in KENNUNGEN and art and art not in KENNUNGEN[k][0]:
                h.append(f'{wo}: „{k}“ bedeutet „{KENNUNGEN[k][1]}“ und ist {" oder ".join(sorted(KENNUNGEN[k][0]))} – '
                         f'hier {art}; bitte eine andere Kennung wählen (REGELN.md, „Gleiche Kennungen“)')
    return h


def neue_felder(ordner: Path, basis: str | None, typen: list, inhalt_pfad: str | None) -> set[tuple[str, str]] | None:
    """Felder, die es auf der Basis (z. B. origin/main) noch nicht gab; ohne Basis keine (leere Menge)."""
    if not basis:
        return set()
    alle = {(str(t.get('schluessel', '')), f['key']) for t in typen if isinstance(t, dict)
            for f in t.get('felder') or [] if isinstance(f, dict) and isinstance(f.get('key'), str)}
    if not inhalt_pfad:
        return alle
    rel = (ordner / inhalt_pfad).relative_to(WURZEL).as_posix()
    try:
        alt = yaml.safe_load(subprocess.run(['git', 'show', f'{basis}:{rel}'], cwd=WURZEL, capture_output=True, text=True, check=True).stdout) or []
    except (subprocess.CalledProcessError, yaml.YAMLError):
        return alle  # neues Paket bzw. neue Datei
    da = {(str(t.get('schluessel', '')), f.get('key')) for t in alt if isinstance(t, dict) for f in t.get('felder') or [] if isinstance(f, dict)}
    return alle - da


# Text-Vorlagen (Registry #157, Kern: DMS #1038/#1040): Markdown unter inhalt/vorlagen/, daraus macht Ablago ein PDF.
# Dieselben Regeln prüft Ablago beim Installieren, denn Pakete kommen auch als Datei.
VORLAGEN_ORDNER = 'inhalt/vorlagen'
VORLAGE_MAX = 256 * 1024  # je Vorlage; vorläufig, bis die Grenze des Kerns (grenzen.ts, DMS #1038) feststeht
VORLAGE_LIZENZEN = {'CC-BY-4.0': 'Attribution 4.0 International', 'CC0-1.0': 'CC0'}
_HTML = re.compile(r'<(?!https://[^\s<>]+>)[A-Za-z!/?]')
_BILD = re.compile(r'!\[[^\]]*\]')
_LINK = re.compile(r'\]\(\s*<?([^)\s>]*)')
_REFLINK = re.compile(r'^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(\s|$)', re.M)
_ROH = re.compile(r'(?<![<(\w])(?:https?|ftp|file|javascript|data):', re.I)
_PLATZHALTER = re.compile(r'\{([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*)\}')


def pruefe_vorlage_text(roh: bytes, wo: str, passwortfelder: set[str]) -> list[str]:
    """Eine Text-Vorlage: UTF-8, klein, kein HTML, keine Bilder, Links nur https:, keine Passwortfelder als Platzhalter."""
    if len(roh) > VORLAGE_MAX:
        return [f'{wo}: größer als {VORLAGE_MAX // 1024} KB']
    try:
        text = roh.decode('utf-8')
    except UnicodeDecodeError:
        return [f'{wo}: kein UTF-8-Text']
    fehler: list[str] = []
    if '\x00' in text:
        fehler.append(f'{wo}: enthält Nullzeichen – nur Text')
    if _HTML.search(text):
        fehler.append(f'{wo}: kein HTML in Vorlagen (auch keine Kommentare) – nur Markdown')
    if _BILD.search(text):
        fehler.append(f'{wo}: keine Bilder in Vorlagen – Briefkopf und Logo setzt Ablago')
    ziele = _LINK.findall(text) + [m.group(1) for m in _REFLINK.finditer(text)]
    for z in ziele:
        if z and not z.startswith('https://') and not z.startswith('{'):
            fehler.append(f'{wo}: Link „{z[:60]}“ – Links nur mit https://')
    ohne_https = re.sub(r'https://\S+', '', text)
    if _ROH.search(ohne_https):
        fehler.append(f'{wo}: Adressen nur mit https:// (kein http:, data:, javascript: …)')
    for p in _PLATZHALTER.findall(text):
        if set(p.split('.')) & passwortfelder:
            fehler.append(f'{wo}: Platzhalter {{{p}}} – Passwortfelder kommen nie in Vorlagen')
    return fehler


def pruefe_vorlagen(ordner: Path, typen: list) -> list[str]:
    """Alle Dateien unter inhalt/vorlagen/: nur .md (und eine LICENSE für eine eigene Lizenz der Vorlagentexte)."""
    wurzel = ordner / VORLAGEN_ORDNER
    if not wurzel.is_dir():
        return []
    passwort = {f['key'] for t in typen if isinstance(t, dict) for f in t.get('felder') or []
                if isinstance(f, dict) and f.get('typ') == 'passwort' and isinstance(f.get('key'), str)}
    fehler: list[str] = []
    for datei in sorted(p for p in wurzel.rglob('*') if p.is_file()):
        rel = datei.relative_to(ordner).as_posix()
        if datei.name == 'LICENSE' and datei.parent == wurzel:
            text = datei.read_text(encoding='utf-8', errors='replace')
            if not any(v.lower() in text.lower() for v in VORLAGE_LIZENZEN.values()):
                fehler.append(f'{rel}: eigene Lizenz der Vorlagentexte nur ' + ' oder '.join(VORLAGE_LIZENZEN) + ' (sonst gilt die Lizenz des Pakets)')
        elif datei.suffix != '.md' or not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', datei.name):
            fehler.append(f'{rel}: Vorlagen nur als Markdown (.md), Namen aus Kleinbuchstaben, Ziffern, „.“, „-“ und „_“')
        else:
            fehler += pruefe_vorlage_text(datei.read_bytes(), rel, passwort)
    return fehler


def pruefe(ordner: Path, basis: str | None) -> list[str]:
    fehler: list[str] = []
    vorlage = ordner.name == 'vorlage'

    for name in PFLICHT:
        if not (ordner / name).exists():
            fehler.append(f'{name} fehlt')
    for datei in ordner.rglob('*'):
        if datei.is_file():
            # code/modul.wasm baut die CI selbst (werkzeuge/bauen.py); eingecheckt wäre es verboten (siehe unten).
            if VERBOTEN.search(datei.name) and datei.relative_to(ordner).as_posix() != 'code/modul.wasm':
                fehler.append(f'{datei.relative_to(ordner)}: fertige Programmdateien sind nicht erlaubt (REGELN.md)')
            erzeugt = datei.relative_to(ordner).as_posix() == 'code/modul.wasm' or datei.relative_to(ordner).as_posix().startswith('code/daten/')
            # Beispiel-Dokumente (motom001/dms#878) haben ihre eigene Grenze je Datei (pruefe_beispiel_dokumente).
            beispiel = datei.relative_to(ordner).as_posix().startswith(BEISPIEL_ORDNER)
            if datei.stat().st_size > MAX_GROESSE and not erzeugt and not beispiel:
                fehler.append(f'{datei.relative_to(ordner)}: größer als 2 MB')
    # Das ganze Paket (gepackt höchstens so groß wie alle Dateien zusammen) muss unter die Grenze des DMS passen (#644).
    gesamt = sum(p.stat().st_size for p in ordner.rglob('*') if p.is_file())
    if gesamt > PAKET_MAX:
        fehler.append(f'Paket zusammen {gesamt / 1048576:.1f} MB – höchstens {PAKET_MAX // 1048576} MB je Paket (Grenze des DMS, DMS #644)')

    m_pfad = ordner / 'manifest.yaml'
    if not m_pfad.exists():
        return fehler
    m = lies_yaml(m_pfad, fehler)
    if not isinstance(m, dict):
        return fehler + ['manifest.yaml: leer oder kein Objekt']
    fehler += schema_fehler(Draft202012Validator(SCHEMA_MANIFEST), m, 'manifest.yaml')
    if m.get('id') == 'dms':
        fehler.append('manifest.yaml: id „dms“ ist reserviert (Verweise auf Mappentypen des DMS)')
    if not vorlage and m.get('id') != ordner.name:
        fehler.append(f"manifest.yaml: id „{m.get('id')}“ muss wie der Ordner heißen („{ordner.name}“)")
    # Symbol (#98): Name prüft das Schema (feste Liste = werkzeuge/symbole/*.svg); das Kürzel gehört zum Symbol.
    if 'kuerzel' in m and 'symbol' not in m:
        fehler.append('manifest.yaml: kuerzel nur zusammen mit symbol')
    if 'kuerzel' in m and not re.fullmatch(r'[A-Z]{2,3}', str(m['kuerzel'])):
        fehler.append('manifest.yaml: kuerzel hat 2–3 Großbuchstaben, bei Sprachen den ISO-639-Code der Sprache (z. B. FR)')
    # Ergänzung (motom001/dms#405): das ergänzte Paket steht auch unter abhaengigkeiten; Form prüft das Schema.
    erg = m.get('ergaenzt')
    erg_paket = erg if isinstance(erg, str) else erg.get('paket') if isinstance(erg, dict) else None
    if erg_paket and erg_paket not in (m.get('abhaengigkeiten') or {}):
        fehler.append(f'manifest.yaml: ergaenzt „{erg_paket}“ muss auch unter abhaengigkeiten stehen')
    if erg_paket and erg_paket == m.get('id'):
        fehler.append('manifest.yaml: ein Paket ergänzt nicht sich selbst')
    fehler += kennungen_pruefung(ordner, m, erg_paket, basis, vorlage)

    # Lizenztext passt grob zur Kennung.
    lizenz = (ordner / 'LICENSE').read_text(encoding='utf-8', errors='replace') if (ordner / 'LICENSE').exists() else ''
    kennung = str(m.get('lizenz', ''))
    merkmale = {'MIT': 'MIT License', 'Apache-2.0': 'Apache License', 'BSD-2-Clause': 'Redistribution and use',
                'BSD-3-Clause': 'Redistribution and use', 'MPL-2.0': 'Mozilla Public License', 'LGPL-3.0-or-later': 'GNU LESSER GENERAL PUBLIC LICENSE',
                'GPL-3.0-or-later': 'GNU GENERAL PUBLIC LICENSE', 'AGPL-3.0-or-later': 'GNU AFFERO GENERAL PUBLIC LICENSE', 'CC0-1.0': 'CC0'}
    if kennung in merkmale and merkmale[kennung].lower() not in lizenz.lower():
        fehler.append(f'LICENSE: passt nicht zur Lizenz „{kennung}“ aus manifest.yaml')
    if not vorlage and ('<Jahr>' in lizenz or '<Name>' in lizenz):
        fehler.append('LICENSE: <Jahr> und <Name> ausfüllen')
    if kennung == 'CC0-1.0' and 'code' in m:
        fehler.append('CC0-1.0 nur für Pakete ohne Code')

    # Changelog nennt die aktuelle Version.
    version = str(m.get('version', ''))
    if (ordner / 'CHANGELOG.md').exists() and not re.search(rf'^##\s+{re.escape(version)}\b', (ordner / 'CHANGELOG.md').read_text(encoding='utf-8'), re.M):
        fehler.append(f'CHANGELOG.md: kein Abschnitt „## {version}“')

    # Inhalte gegen das Schema; lokale Schlüssel eindeutig; Verweise auflösbar.
    inhalte = m.get('inhalt') or {}
    geladen: dict[str, list] = {}
    for art in ('mappentypen', 'sichten', 'beispiele', 'wortlisten', 'automatisierungen'):
        if art not in inhalte:
            continue
        pfad = ordner / str(inhalte[art])
        if not pfad.exists():
            fehler.append(f'inhalt.{art}: Datei {inhalte[art]} fehlt')
            continue
        daten = lies_yaml(pfad, fehler) or []
        fehler += schema_fehler(inhalt_validator(art), daten, str(inhalte[art]))
        geladen[art] = daten if isinstance(daten, list) else []

    typen = {t.get('schluessel') for t in geladen.get('mappentypen', []) if isinstance(t, dict)}
    abh = set((m.get('abhaengigkeiten') or {}).keys())

    def verweis_ok(v: str, wo: str):
        if ':' in v:
            paket = v.split(':', 1)[0]
            if paket == 'dms':
                if (f := dms_fehler(v, wo)):
                    fehler.append(f)
            elif paket != m.get('id') and paket not in abh:
                fehler.append(f'{wo}: „{v}“ verweist auf Paket „{paket}“, das nicht unter abhaengigkeiten steht')
        elif v not in typen:
            fehler.append(f'{wo}: Mappentyp „{v}“ gibt es in diesem Paket nicht')

    gesehen: set[str] = set()
    for t in geladen.get('mappentypen', []):
        if not isinstance(t, dict):
            continue
        s = t.get('schluessel')
        if s in gesehen:
            fehler.append(f'mappentypen: Schlüssel „{s}“ doppelt')
        gesehen.add(s)
        # Bis Ablago 0.228 hießen Mappentypen <paket>_<schluessel> mit höchstens 40 Zeichen; ab 0.229.0 (#1084) gilt
        # nur noch der Schlüssel (bis 60, prüft das Schema).
        if len(f"{m.get('id')}_{s}") > 40 and not kennungen_neu(m):
            fehler.append(f'mappentypen: „{m.get("id")}_{s}“ ist länger als 40 Zeichen – erst ab Ablago 0.229.0 erlaubt (dms: ">=0.229.0")')
        felder = {f.get('key') for f in t.get('felder', []) if isinstance(f, dict)}
        for f in t.get('felder', []):
            if isinstance(f, dict) and f.get('ziel'):
                verweis_ok(f['ziel'], f'mappentypen/{s}/{f.get("key")}')
        auf_registern: list[str] = []
        for r in t.get('register', []):
            if not isinstance(r, dict):
                continue
            for k in r.get('felder', []) or []:
                if k not in felder:
                    fehler.append(f'mappentypen/{s}: Register „{r.get("key")}“ nennt unbekanntes Feld „{k}“')
                auf_registern.append(k)
            for q in r.get('quellen', []) or []:
                verweis_ok(q.get('typ', ''), f'mappentypen/{s}/register/{r.get("key")}')
        ohne = felder - set(auf_registern)
        if ohne:
            fehler.append(f'mappentypen/{s}: Felder auf keinem Feldregister: {", ".join(sorted(ohne))}')
        doppelt = {k for k in auf_registern if auf_registern.count(k) > 1}
        if doppelt:
            fehler.append(f'mappentypen/{s}: Felder auf mehreren Registern: {", ".join(sorted(doppelt))}')
        for k in t.get('trefferliste', []) or []:
            if k not in felder and not k.startswith('_'):
                fehler.append(f'mappentypen/{s}: Trefferliste nennt unbekanntes Feld „{k}“')

    fehler += pruefe_erkennung(geladen.get('mappentypen', []) or [], str(m.get('dms', '')))
    fehler += pruefe_beschriftungen(geladen.get('mappentypen', []) or [], geladen.get('sichten', []) or [])
    fehler += pruefe_aus_text(geladen.get('mappentypen', []) or [], str(m.get('dms', '')))
    fehler += pruefe_verweise(geladen.get('mappentypen', []) or [], str(m.get('dms', '')))
    fehler += pruefe_formate(geladen.get('mappentypen', []) or [], geladen.get('beispiele', []) or [], str(m.get('dms', '')))

    sichten = {s.get('schluessel') for s in geladen.get('sichten', []) if isinstance(s, dict)}
    for s in geladen.get('sichten', []):
        if not isinstance(s, dict):
            continue
        if s.get('eltern') and s['eltern'] not in sichten:
            fehler.append(f'sichten/{s.get("schluessel")}: Elternsicht „{s["eltern"]}“ fehlt')
        for t in s.get('typen', []) or []:
            if t == ALLE_TYPEN:
                # Ansicht über alle Mappentypen (DMS #725), z. B. „Favoriten“ – allein, ab Ablago 0.182.0.
                if len(s.get('typen') or []) > 1:
                    fehler.append(f'sichten/{s.get("schluessel")}: „*“ (alle Mappentypen) steht allein in typen')
                ab = dms_untergrenze(str(m.get('dms', '')))
                if ab is None or ab < DMS_ALLE_TYPEN_AB:
                    fehler.append(f'sichten/{s.get("schluessel")}: „*“ (alle Mappentypen) kennt Ablago erst ab 0.182.0 – bitte dms: ">=0.182.0" angeben')
                continue
            verweis_ok(t, f'sichten/{s.get("schluessel")}')
        if s.get('fremde_typen'):
            ab_f = dms_untergrenze(str(m.get("dms", "")))
            if ab_f is None or ab_f < DMS_FREMDE_TYPEN_AB:
                fehler.append(f'sichten/{s.get("schluessel")}: fremde_typen kennt das DMS erst ab 0.178.0 – bitte dms: ">=0.178.0" angeben')
    for b in geladen.get('beispiele', []):
        if isinstance(b, dict) and b.get('typ'):
            verweis_ok(b['typ'], 'beispiele')
    fehler += pruefe_beispiel_verweise(geladen.get('beispiele', []) or [], str(m.get('id')), abh)
    fehler += pruefe_beispiel_dokumente(ordner, geladen.get('beispiele', []) or [], geladen.get('mappentypen', []) or [], str(m.get('id')), str(m.get('dms', '')))
    fehler += pruefe_wortlisten(geladen.get('wortlisten', []) or [], str(m.get('dms', '')))
    fehler += pruefe_vorlagen(ordner, geladen.get('mappentypen', []) or [])
    typfelder = {t.get('schluessel'): t.get('felder') or [] for t in geladen.get('mappentypen', []) if isinstance(t, dict)}
    fehler += pruefe_automatisierungen(geladen.get('automatisierungen', []) or [], typfelder, str(m.get('id')), abh, str(m.get('dms', '')))

    # tests/erwartung.yaml stimmt mit dem Inhalt überein.
    erw_pfad = ordner / 'tests' / 'erwartung.yaml'
    if erw_pfad.exists():
        erw = lies_yaml(erw_pfad, fehler) or {}
        if set(erw.get('mappentypen', [])) != typen:
            fehler.append('tests/erwartung.yaml: mappentypen passen nicht zu inhalt/')
        if set(erw.get('sichten', [])) != sichten:
            fehler.append('tests/erwartung.yaml: sichten passen nicht zu inhalt/')
        if 'beispiele' in erw and erw['beispiele'] != len(geladen.get('beispiele', [])):
            fehler.append('tests/erwartung.yaml: Anzahl beispiele passt nicht')
        if erw.get('wortlisten', 0) != len(geladen.get('wortlisten', [])):
            fehler.append('tests/erwartung.yaml: Anzahl wortlisten passt nicht')
        if erw.get('automatisierungen', 0) != len(geladen.get('automatisierungen', [])):
            fehler.append('tests/erwartung.yaml: Anzahl automatisierungen passt nicht')
        if 'sprache' in m and erw.get('sprache') != (m.get('sprache') or {}).get('kennung'):
            fehler.append('tests/erwartung.yaml: sprache passt nicht zu manifest.yaml (sprache.kennung)')
    elif not vorlage:
        fehler.append('tests/erwartung.yaml fehlt')

    # Sprachpaket (Ablago #731): nur Texte.
    if 'sprache' in m:
        fehler += pruefe_sprachpaket(ordner, m)

    if isinstance(m.get('code'), dict):
        fehler += pruefe_einstellungen(m['code'], str(m.get('id')), typen, abh, str(m.get('dms', '')))
        fehler += pruefe_rechte(m['code'], str(m.get('dms', '')))
        fehler += pruefe_mappentypen(m['code'], str(m.get('id')), typen, str(m.get('dms', '')))
    if 'code' in m:
        quelle = ordner / str(m['code'].get('quelle', ''))
        if not quelle.is_dir() or not any(p.is_file() and p.name != 'README.md' for p in quelle.rglob('*')):
            fehler.append('code.quelle: kein Quellcode gefunden')
        if not (ordner / 'code' / 'bauen.sh').exists():
            fehler.append('code/bauen.sh fehlt – die CI baut das Modul aus dem Quellcode (siehe vorlage/code/README.md)')
        # Gebaute Module nie einchecken: Die CI baut sie selbst (werkzeuge/bauen.py).
        r = subprocess.run(['git', 'ls-files', '--', 'code/modul.wasm', 'code/daten'], cwd=ordner, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            fehler.append('code/modul.wasm und code/daten/ entstehen beim Bau und gehören nicht ins Repository')
        # Grenze des DMS: code/ zusammen höchstens PAKET_MAX (nach dem Bau sinnvoll, mit modul.wasm und daten/).
        code_ordner = ordner / 'code'
        if code_ordner.is_dir():
            summe = sum(p.stat().st_size for p in code_ordner.rglob('*') if p.is_file())
            if summe > CODE_MAX:
                fehler.append(f'code/: zusammen {summe / 1024 / 1024:.1f} MB – höchstens {CODE_MAX // 1048576} MB je Paket')
        modul = ordner / 'code' / 'modul.wasm'
        if modul.exists():
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            import wasm  # erst hier: pruefen.py läuft auch allein (z. B. kopiert im Test des DMS)
            fehler += wasm.pruefe(modul.read_bytes())
            # netz_strom, netz_weiter und teil (DMS #444): Ältere DMS lehnen ein solches Modul ab.
            neu = sorted(wasm.dms_importe(modul.read_bytes()) & DMS_FUNKTIONEN_ANTWORTEN)
            ab = dms_untergrenze(str(m.get('dms', '')))
            if neu and (ab is None or ab < DMS_ANTWORTEN_AB):
                fehler.append(f'code/modul.wasm: {", ".join(neu)} kennt das DMS erst ab 0.124.0 – bitte dms: ">=0.124.0" angeben')

    if basis and not vorlage and geaendert(basis, ordner):
        alt = version_von(basis, m_pfad)
        if alt is not None and alt == version:
            fehler.append(f'version: Paket geändert, aber Version {version} nicht erhöht')
    return fehler


def veraltete_verweise(ordner: Path) -> list[str]:
    """Warnungen für veraltete Verweise (DMS #883): jeder Wert dms:ablageort im Manifest und in den Inhalten."""
    gefunden: dict[str, set[str]] = {}

    def suche(w, datei: str):
        if isinstance(w, str) and w in DMS_ALIAS:
            gefunden.setdefault(w, set()).add(datei)
        elif isinstance(w, dict):
            for x in w.values():
                suche(x, datei)
        elif isinstance(w, list):
            for x in w:
                suche(x, datei)

    for pfad in [ordner / 'manifest.yaml', *sorted((ordner / 'inhalt').glob('*.yaml'))]:
        if not pfad.is_file():
            continue
        try:
            suche(yaml.safe_load(pfad.read_text(encoding='utf-8')), pfad.relative_to(ordner).as_posix())
        except Exception:  # noqa: BLE001 – meldet schon pruefe()
            continue
    return [f'{", ".join(sorted(dateien))}: „{alt}“ ist veraltet – bitte „{DMS_ALIAS[alt]}“ (Paket Basis, abhaengigkeiten: '
            f'basis: ">=1.6.0"). Das DMS versteht „{alt}“ nur noch bis 1.0.' for alt, dateien in sorted(gefunden.items())]


def sprach_hinweise(ordner: Path, basis: str | None) -> list[str]:
    """Paketsprache (Registry #157): Kennungen neuer Felder; Vorlagen-Pakete mit Code ändern nur eigene Mappentypen."""
    try:
        m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001 – meldet schon pruefe()
        return []
    if not isinstance(m, dict):
        return []
    pfad = (m.get('inhalt') or {}).get('mappentypen')
    typen = []
    if pfad and (ordner / str(pfad)).is_file():
        try:
            typen = yaml.safe_load((ordner / str(pfad)).read_text(encoding='utf-8')) or []
        except Exception:  # noqa: BLE001
            typen = []
    typen = typen if isinstance(typen, list) else []
    h = kennung_hinweise(typen, neue_felder(ordner, basis, typen, str(pfad) if pfad else None))
    code = m.get('code') if isinstance(m.get('code'), dict) else {}
    rechte = code.get('rechte') if isinstance(code.get('rechte'), dict) else {}
    eigene = {str(t.get('schluessel')) for t in typen if isinstance(t, dict)}
    if eigene and code:
        fremd = [v for v in rechte.get('schreiben') or [] if isinstance(v, str)
                 and (v == '*' or (':' in v and not v.startswith(f"{m.get('id')}:")) or (':' not in v and v not in eigene))]
        if fremd:
            h.append('code.rechte.schreiben: ' + ', '.join(fremd) + ' – ein Vorlagen-Paket mit Code pflegt nur seine eigenen Mappentypen; '
                     'Code für alle Mappen gehört in ein Funktions-Paket (REGELN.md, „Paketarten“)')
    return h


def doppelte_typen(ordner: list[Path]) -> list[str]:
    """„Ein Mappentyp lebt in genau einem Paket“ (Registry #157): gleicher Name in zwei Paketen."""
    namen: dict[str, list[str]] = {}
    for o in ordner:
        try:
            m = yaml.safe_load((o / 'manifest.yaml').read_text(encoding='utf-8')) or {}
            pfad = (m.get('inhalt') or {}).get('mappentypen')
            typen = yaml.safe_load((o / str(pfad)).read_text(encoding='utf-8')) or [] if pfad else []
        except Exception:  # noqa: BLE001
            continue
        for t in typen if isinstance(typen, list) else []:
            if isinstance(t, dict) and isinstance(t.get('name'), str):
                namen.setdefault(t['name'].strip().lower(), []).append(f"{m.get('id', o.name)}:{t.get('schluessel')}")
    return [f'Mappentyp „{n}“ gibt es in {", ".join(sorted(w))} – ein Mappentyp lebt in genau einem Paket, die anderen verweisen '
            'darauf (REGELN.md, „Paketarten“)' for n, w in sorted(namen.items()) if len(w) > 1]


def kennungen_neu(m: dict) -> bool:
    """Verlangt das Paket Ablago ab 0.229.0 (Kennungen paket:schluessel, #1084)?"""
    ab = dms_untergrenze(str(m.get('dms', '')))
    return ab is not None and ab >= DMS_KENNUNGEN_AB


def ersetzte_ids(m: dict) -> list[str]:
    e = m.get('ersetzt')
    return [str(x) for x in ([e] if isinstance(e, str) else e if isinstance(e, list) else [])]


def lange_schluessel(ordner: Path, m: dict) -> list[str]:
    """Schlüssel über 40 Zeichen (bis Ablago 0.228 die Grenze) in Mappentypen, Feldern, Registern, Ansichten, Beispielen
    und Automatisierungen."""
    lang = []
    for art in ('mappentypen', 'sichten', 'beispiele', 'automatisierungen'):
        rel = (m.get('inhalt') or {}).get(art)
        try:
            liste = yaml.safe_load((ordner / str(rel)).read_text(encoding='utf-8')) or [] if rel else []
        except Exception:  # noqa: BLE001 – meldet schon pruefe()
            continue
        for x in liste if isinstance(liste, list) else []:
            if not isinstance(x, dict):
                continue
            werte = [x.get('schluessel')] + [f.get('key') for f in x.get('felder') or [] if isinstance(f, dict)] \
                + [r.get('key') for r in x.get('register') or [] if isinstance(r, dict)]
            lang += [f'{art}: „{w}“' for w in werte if isinstance(w, str) and len(w) > 40]
    return lang


def kennungen_pruefung(ordner: Path, m: dict, erg_paket: str | None, basis: str | None, vorlage: bool) -> list[str]:
    """Registry #173 nach motom001/dms#1084: Id mit Punkt nur als Ergänzung des Pakets vor dem Punkt, ersetzt, längere
    Ids und Schlüssel erst ab Ablago 0.229.0, Herausgeber app.ablago für jede neue Version."""
    fehler: list[str] = []
    pid = str(m.get('id', ''))
    neu = kennungen_neu(m)
    if '.' in pid:
        haupt = pid.split('.', 1)[0]
        if erg_paket != haupt:
            fehler.append(f'manifest.yaml: Eine Id mit Punkt ergänzt das Paket vor dem Punkt – bitte ergaenzt: {haupt} (und {haupt} unter abhaengigkeiten)')
        if not neu:
            fehler.append('manifest.yaml: Ids mit Punkt kennt Ablago erst ab 0.229.0 – bitte dms: ">=0.229.0" angeben')
    elif len(pid) > 20 and not neu:
        fehler.append('manifest.yaml: Ids über 20 Zeichen kennt Ablago erst ab 0.229.0 – bitte dms: ">=0.229.0" angeben')
    ersetzt = ersetzte_ids(m)
    if ersetzt:
        if pid in ersetzt or 'dms' in ersetzt:
            fehler.append('manifest.yaml: ersetzt nennt frühere Ids – nicht die eigene und nicht „dms“')
        if not neu:
            fehler.append('manifest.yaml: ersetzt (Umzug auf eine neue Id) kennt Ablago erst ab 0.229.0 – bitte dms: ">=0.229.0" angeben')
    if not neu:
        fehler += [f'{x} ist länger als 40 Zeichen – erst ab Ablago 0.229.0 erlaubt (dms: ">=0.229.0")' for x in lange_schluessel(ordner, m)]
    # Herausgeber (Sicherheit, #1084): Pflicht für jede neue Version; ältere Versionen gelten im offiziellen Katalog
    # ohnehin als app.ablago. Die Form (genau app.ablago) prüft das Schema.
    if not vorlage and 'herausgeber' not in m and basis and neue_version(ordner, m, basis):
        fehler.append(f'manifest.yaml: herausgeber: {HERAUSGEBER} fehlt – Pflicht für jede neue Version (Registry #173)')
    return fehler


def neue_version(ordner: Path, m: dict, basis: str) -> bool:
    """Ist die Version im Ordner gegenüber der Basis neu (neues Paket oder andere Version)?"""
    r = subprocess.run(['git', 'show', f'{basis}:pakete/{ordner.name}/manifest.yaml'], cwd=WURZEL, capture_output=True, text=True)
    if r.returncode != 0:
        return True
    try:
        alt = yaml.safe_load(r.stdout) or {}
    except Exception:  # noqa: BLE001
        return True
    return str(alt.get('version')) != str(m.get('version'))


def kennungs_kollisionen(ordner: list[Path]) -> tuple[list[str], list[str]]:
    """Kennungen in Ablago bis 0.228 (Registry #173; ab 0.229.0 paket:schluessel, #1084): Mappentypen und Ansichten hießen <paket>_<schluessel>. Weil beide
    „_“ enthalten dürfen, können zwei Pakete dieselbe Kennung erzeugen (haus + garten_pflanze, haus_garten + pflanze).
    Liefert (Fehler, Hinweise): Fehler bei gleicher Kennung, Hinweis bei einer Id, die wie <andere id>_… aussieht."""
    gesehen: dict[str, str] = {}
    fehler: list[str] = []
    ids: dict[str, dict] = {}
    for o in ordner:
        try:
            m = yaml.safe_load((o / 'manifest.yaml').read_text(encoding='utf-8')) or {}
        except Exception:  # noqa: BLE001 – meldet schon pruefe()
            continue
        if not isinstance(m, dict) or not m.get('id'):
            continue
        pid = str(m['id'])
        ids[pid] = m
        for art in ('mappentypen', 'sichten'):
            pfad = (m.get('inhalt') or {}).get(art)
            try:
                liste = yaml.safe_load((o / str(pfad)).read_text(encoding='utf-8')) or [] if pfad else []
            except Exception:  # noqa: BLE001
                continue
            for x in liste if isinstance(liste, list) else []:
                if not isinstance(x, dict) or not x.get('schluessel'):
                    continue
                k = f'{pid}_{x["schluessel"]}'
                wer = f'{pid}:{x["schluessel"]} ({art})'
                if k in gesehen and gesehen[k].split(':', 1)[0] != pid:
                    fehler.append(f'Kennung „{k}“ entsteht doppelt: {gesehen[k]} und {wer} – Ablago legt beide als „{k}“ an. '
                                  'Bitte einen Schlüssel umbenennen (Registry #173, motom001/dms#1084).')
                gesehen.setdefault(k, wer)
    hinweise: list[str] = []
    for pid, m in sorted(ids.items()):
        erg = m.get('ergaenzt')
        erg = erg if isinstance(erg, str) else erg.get('paket') if isinstance(erg, dict) else None
        for andere in sorted(ids):
            if andere != pid and pid.startswith(andere + '_') and erg != andere:
                hinweise.append(f'Paket-Id „{pid}“ beginnt wie „{andere}_“, ergänzt es aber nicht – das kann Kennungen doppeldeutig machen; '
                                'besser eine eigene Id ohne diesen Anfang (Registry #173)')
    return fehler, hinweise


IDS = WURZEL / 'werkzeuge' / 'ids.txt'


def lies_ids(text: str) -> list[str]:
    return [z.strip() for z in text.splitlines() if z.strip() and not z.lstrip().startswith('#')]


def id_pruefung(ordner: list[Path], basis: str | None, ids_text: str | None = None, alt_text: str | None = None,
                gab_es=None) -> list[str]:
    """Eine Id nur einmal (Registry #173): werkzeuge/ids.txt nennt jede je veröffentlichte Paket-Id. Neue Pakete
    tragen sich dort ein; keine Zeile verschwindet; ein neuer Paketordner darf keine früher vergebene Id nutzen."""
    fehler: list[str] = []
    ids = lies_ids(IDS.read_text(encoding='utf-8') if ids_text is None else ids_text)
    if len(ids) != len(set(ids)):
        fehler.append('werkzeuge/ids.txt: eine Id steht doppelt')
    alt: list[str] = []
    if basis or alt_text is not None:
        if alt_text is None:
            r = subprocess.run(['git', 'show', f'{basis}:werkzeuge/ids.txt'], cwd=WURZEL, capture_output=True, text=True)
            alt_text = r.stdout if r.returncode == 0 else ''
        alt = lies_ids(alt_text)
        weg = sorted(set(alt) - set(ids))
        if weg:
            fehler.append(f'werkzeuge/ids.txt: {", ".join(weg)} gestrichen – Ids bleiben für immer vergeben, nur anhängen')
    if gab_es is None:
        def gab_es(pid: str) -> bool:
            return not basis or subprocess.run(['git', 'cat-file', '-e', f'{basis}:pakete/{pid}/manifest.yaml'], cwd=WURZEL,
                                               capture_output=True).returncode == 0
    for o in ordner:
        try:
            pid = str((yaml.safe_load((o / 'manifest.yaml').read_text(encoding='utf-8')) or {}).get('id'))
        except Exception:  # noqa: BLE001 – meldet schon pruefe()
            continue
        if pid not in ids:
            fehler.append(f'{pid}: neue Paket-Id – bitte im selben Pull Request in werkzeuge/ids.txt eintragen (Registry #173)')
        elif pid in alt and not gab_es(pid):
            fehler.append(f'{pid}: diese Id war schon vergeben (werkzeuge/ids.txt) – ein neues Paket braucht eine eigene, auch wenn das alte zurückgezogen ist')
        # Umzug (#1084): Die alte Id gab es (ids.txt) und hat keinen Paketordner mehr; das Hauptpaket einer Id mit Punkt
        # gibt es in der Registry (gleicher Herausgeber: hier immer app.ablago).
        try:
            m = yaml.safe_load((o / 'manifest.yaml').read_text(encoding='utf-8')) or {}
        except Exception:  # noqa: BLE001
            m = {}
        for x in ersetzte_ids(m) if isinstance(m, dict) else []:
            if x not in ids:
                fehler.append(f'{pid}: ersetzt „{x}“ – diese Id gab es nie (werkzeuge/ids.txt)')
            if (o.parent / x).is_dir():
                fehler.append(f'{pid}: ersetzt „{x}“, den Ordner pakete/{x} gibt es aber noch – beim Umzug zieht der Ordner mit')
        if '.' in pid and not (o.parent / pid.split('.', 1)[0] / 'manifest.yaml').exists():
            fehler.append(f'{pid}: das Hauptpaket „{pid.split(".", 1)[0]}“ gibt es in der Registry nicht')
    return fehler


def hinweise(ordner: Path, basis: str | None = None) -> list[str]:
    """Hinweise ohne Fehler (#98): veraltete Verweise (DMS #883), Paket ohne Symbol, Manifest und
    werkzeuge/kategorien.yaml verschieden, Paketsprache (#157: Kennungen neuer Felder gegen die Basis).

    Ohne vorlagen.py und kategorien.yaml (pruefen.py allein, z. B. im Test des DMS) nur die veralteten Verweise."""
    veraltet = (veraltete_verweise(ordner) if (ordner / 'manifest.yaml').exists() else []) + beispiel_groessen(ordner)
    if ordner.name != 'vorlage' and (ordner / 'manifest.yaml').exists():
        veraltet += sprach_hinweise(ordner, basis)
    if ordner.name == 'vorlage' or not (ordner / 'manifest.yaml').exists():
        return veraltet
    if not (WURZEL / 'werkzeuge' / 'vorlagen.py').exists() or not (WURZEL / 'werkzeuge' / 'kategorien.yaml').exists():
        return veraltet
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import vorlagen  # erst hier: pruefen.py läuft auch allein
    try:
        m = yaml.safe_load((ordner / 'manifest.yaml').read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001 – meldet schon pruefe()
        return veraltet
    if not isinstance(m, dict):
        return veraltet
    daten = vorlagen.lies_kategorien()
    pid = str(m.get('id', ordner.name))
    h = veraltet + vorlagen.abweichungen(pid, m, daten)
    if not vorlagen.symbol_von(pid, daten, m)[0]:
        h.append('symbol: Das Paket hat kein Symbol – der Katalog zeigt den Anfangsbuchstaben. '
                 f'Bitte ein Symbol im Manifest setzen (symbol: …), erlaubt: {", ".join(vorlagen.symbolnamen())} (REGELN.md, „Symbol“)')
    return h


def main():
    args = sys.argv[1:]
    basis = None
    if args[:1] == ['--basis']:
        basis, args = args[1], args[2:]
    ordner = [Path(a).resolve() for a in args] or [WURZEL / 'vorlage', *sorted(p for p in (WURZEL / 'pakete').iterdir() if p.is_dir())]
    gesamt = 0
    for o in ordner:
        f = pruefe(o, basis)
        name = o.relative_to(WURZEL).as_posix()
        if f:
            gesamt += len(f)
            print(f'✗ {name}')
            for x in f:
                print(f'    {x}')
                if 'GITHUB_ACTIONS' in __import__('os').environ:
                    print(f'::error file={name}/manifest.yaml,title={name}::{x}')
        else:
            print(f'✓ {name}')
        for x in hinweise(o, basis):
            print(f'    Hinweis: {x}')
            if 'GITHUB_ACTIONS' in __import__('os').environ:
                print(f'::warning file={name}/manifest.yaml,title={name}::{x}')
    k_fehler, k_hinweise = kennungs_kollisionen([o for o in ordner if o.name != 'vorlage'])
    k_fehler += id_pruefung([o for o in ordner if o.name != 'vorlage'], basis)
    for x in k_fehler:
        gesamt += 1
        print(f'✗ {x}')
        if 'GITHUB_ACTIONS' in __import__('os').environ:
            print(f'::error title=Kennungen::{x}')
    for x in k_hinweise:
        print(f'Hinweis: {x}')
        if 'GITHUB_ACTIONS' in __import__('os').environ:
            print(f'::warning title=Kennungen::{x}')
    for x in doppelte_typen([o for o in ordner if o.name != 'vorlage']):
        print(f'Hinweis: {x}')
        if 'GITHUB_ACTIONS' in __import__('os').environ:
            print(f'::warning title=Paketsprache::{x}')
    sys.exit(1 if gesamt else 0)


if __name__ == '__main__':
    main()
