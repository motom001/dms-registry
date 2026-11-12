# Regeln für Pakete

**Deutsch** · [English](REGELN.en.md)

> Bei Abweichungen zwischen deutscher und englischer Fassung gilt die deutsche.

## Lizenzen

Jedes Paket steht unter einer dieser Open-Source-Lizenzen (Kennung nach [SPDX](https://spdx.org/licenses/), so in `manifest.yaml` unter `lizenz`):

`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `MPL-2.0`, `LGPL-3.0-or-later`, `GPL-3.0-or-later`, `AGPL-3.0-or-later`, `CC0-1.0` (nur für reine Konfiguration)

Für **Vorlagentexte** darf zusätzlich `CC-BY-4.0` oder `CC0-1.0` gelten (siehe [Text-Vorlagen](#text-vorlagen)).

Der vollständige Lizenztext liegt als `LICENSE` im Paketordner. Fremder Code im Paket braucht eine dazu passende Lizenz und einen Hinweis im README.

## Erlaubt

- Mappentypen, Sichten, Rollen, Beispiel-Mappen
- Beschriftungen je Sprache an Mappentypen, Feldern, Auswahlwerten, Registern und Ansichten (siehe [Beschriftungen je Sprache](#beschriftungen-je-sprache))
- Sprachpakete: weitere Sprachen für Ablago, nur Texte (siehe [Sprachpakete](#sprachpakete))
- Sichten über **alle Mappentypen** mit `typen: ["*"]` – auch künftige, z. B. eine Ansicht „Favoriten“ (allein in `typen`, ab Ablago 0.182.0, `dms: ">=0.182.0"`)
- Wortlisten: gleichbedeutende Wörter für die Suche (siehe [Wortlisten](#wortlisten))
- Vorgefertigte Automatisierungen (siehe [Automatisierungen](#automatisierungen))
- Automatisierungsvorlagen fürs Menü „Mappe“, nur mit Aufgaben und Benachrichtigungen (siehe [Automatisierungsvorlagen](#automatisierungsvorlagen))
- Code, der über die API von Ablago arbeitet (sobald der Paket-Läufer verfügbar ist)
- Zugriff auf Netzwerk/Internet nur zu Adressen, die im Manifest stehen (`code.netz`) und deren Zweck das README erklärt. Ohne `code.netz` hat ein Paket keinen Zugriff auf Netzwerk und Internet.

## Verboten

- **Fertige Programmdateien** jeder Art (`.wasm`, `.so`, `.dll`, `.exe`, `.jar`, `.bin` …). Gebaut wird in der CI aus dem Quellcode.
- Verschleierter oder minifizierter Quellcode
- Telemetrie, Tracking, Werbung
- Zugriff auf Netzwerk/Internet zu Adressen, die nicht im Manifest stehen – außer zur Dienst-Adresse, die der Administrator in einer Einstellung vom Typ `adresse` einträgt und bestätigt
- Eine voreingestellte Dienst-Adresse eines fremden Anbieters (Cloud) – auch nicht als `beispiel`
- Mehr Rechte als nötig, z. B. Schreibrecht, wo Lesen reicht
- Echte persönliche Daten in Beispielen, Beispiel-Dokumenten, Tests oder Screenshots
- Löschen von Feldern, Registern oder Mappen bei einem Update (ein Textfeld, das ein Verweis mit `aus_text` ablöst, darf aus dem Paket – siehe [Text in Verweis umwandeln](#text-in-verweis-umwandeln))

## So sehen Administratoren die Rechte

Vor der Installation zeigt Ablago die Rechte eines Pakets mit Code, die Katalog-Webseite genauso:

- „Mappen lesen: …“, „Mappen anlegen und ändern: …“, „Dokumente lesen“ bzw. „Dokumente lesen und Volltext schreiben“
- „Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.122.0"`
- „Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die Ablago mitgibt (dms:antworten)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.124.0"`
- „Felder aus Dokumenten vorschlagen („Aus Dokument ausfüllen“) – nur aus dem Text, den Ablago mitgibt (dms:erkennen)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.125.0"`
- „Texterkennung für Scans und Bilder übernehmen – Ablago meldet Dokumente ohne Text und zeigt „wartet auf Texterkennung“, bis das Paket den Volltext schreibt (dms:texterkennung)“ – nur mit `code.rechte.schnittstellen`, `dokumente: schreiben` und `dms: ">=0.133.0"`
- „Dateien umwandeln, die Ablago nicht selbst lesen kann – das Paket liest die Originaldatei und liefert eine Fassung (PDF, PNG oder JPEG) für Vorschaubild und Volltext; das Original bleibt unverändert (dms:umwandeln): TIFF, WebP, …“ – nur mit `code.rechte.schnittstellen`, `code.umwandeln`, dem Ereignis `datei.umwandeln`, `dokumente: lesen` und `dms: ">=0.137.0"` (siehe [Dateien umwandeln](#dateien-umwandeln))
- „Volltext für Dateien liefern, die Ablago nicht selbst lesen kann – das Paket liest die Datei und schreibt nur ihren Volltext; Dokumente ändern, ersetzen oder löschen kann es nicht (dms:volltext): Word, E-Mail, …“ – nur mit `code.rechte.schnittstellen`, `code.volltext`, dem Ereignis `datei.volltext`, `dokumente: lesen` und `dms: ">=0.145.0"` (siehe [Nur Text aus Dokumenten](#nur-text-aus-dokumenten))
- „Mappentyp vorschlagen („Wohin gehört das?“) – nur aus dem Anfang des Dokuments und der Liste der Mappentypen, die Ablago mitgibt (dms:klassifizieren)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.226.0"`; Aufruf und Antwort im Entwicklerhandbuch unter [Mappentyp vorschlagen](https://help.ablago.app/entwickler/aktuell/pakete-code/#klassifizieren)
- „Markiert leere Seiten in neuer Post – löscht nichts; weggelassen werden sie erst, wenn jemand die Post in eine Mappe übernimmt (dms:leerseiten)“ – nur mit `code.rechte.schnittstellen`, `code.rechte.lesen` mit `dms:post` (oder `*`), `dokumente: lesen` und `dms: ">=0.255.0"`; Aufruf im Entwicklerhandbuch unter [Leerseiten markieren](https://help.ablago.app/entwickler/aktuell/pakete-code/#leerseiten)
- „Archivfassung (PDF/A) ablegen – das Paket liest Dokumente mit ihrem Volltext und den Wortpositionen und legt daneben ein durchsuchbares PDF/A ab; das Original bleibt unverändert, ändern, ersetzen oder löschen kann es nichts (dms:archivfassung): PDF, JPEG, PNG, …“ – nur mit `code.rechte.schnittstellen`, `code.archivfassung`, dem Ereignis `datei.archivfassung`, `dokumente: lesen` und `dms: ">=0.149.0"` (siehe [Archivfassung (PDF/A)](#archivfassung-pdfa))
- „Die verschlüsselte Sicherung lesen, um sie außer Haus zu kopieren – kann sie nicht öffnen (kein Schlüssel, keine Inhalte) (dms:sicherung-lesen)“ – nur mit `code.rechte.schnittstellen`, dem Ereignis `sicherung.fertig` und `dms: ">=0.142.0"` (siehe [Sicherung außer Haus](#sicherung-außer-haus))
- „kein Zugriff auf Netzwerk und Internet“ bzw. „Zugriff auf Netzwerk/Internet nur zu: …“; mit einer Dienst-Adresse als Einstellung zusätzlich „der Adresse aus der Einstellung „…“ (trägst du ein und bestätigst sie)“
- „Reagiert auf diese Ereignisse:“ mit einem Ereignis je Zeile

Erklärt sind sie im Administratorhandbuch unter [Pakete mit Code](https://help.ablago.app/admin/aktuell/pakete/#rechte-eines-pakets). Schreibe im README eines Pakets mit Code im Abschnitt „Rechte und Netzwerkzugriff“ (wie in der [Vorlage](vorlage/README.md)) mit denselben Worten, was das Paket darf und wozu.

## Pflicht

- `manifest.yaml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `inhalt/` (ggf. leer), `tests/`
- Paket-Id = Ordnername: Kleinbuchstaben, Ziffern, `_`, beginnt mit einem Buchstaben, höchstens 40 Zeichen (über 20 erst ab Ablago 0.229.0, `dms: ">=0.229.0"`). Dazu darf **ein** Punkt mit einem Zusatz bis 20 Zeichen stehen – nur für Ergänzungen (siehe [Ergänzungen](#ergänzungen)).
- **Herausgeber** (Registry #173, motom001/dms#1084): `herausgeber: app.ablago` – Pflicht für jede neue Version; alle Pakete dieser Registry gibt das Ablago-Projekt heraus. Ablago ab 0.229.0 zeigt ihn neben dem Namen („Verträge · app.ablago“) und nimmt `app.ablago` nur aus dem offiziellen Katalog. Ältere Versionen ohne das Feld gelten im Katalog ebenfalls als `app.ablago`; ältere Ablago-Versionen übergehen es.
- **Schlüssel** (Mappentypen, Felder, Register, Ansichten, Beispiele, Automatisierungen) bis 60 Zeichen; über 40 erst ab Ablago 0.229.0.
- **Eine Id nur einmal** (Registry #173): Ein neues Paket trägt seine Id im selben Pull Request in `werkzeuge/ids.txt` ein. Dort steht jede Id, die es im Katalog je gab, für immer, auch wenn das Paket zurückgezogen wird. `pruefen.py` lehnt eine früher vergebene Id für ein neues Paket ab, ebenso das Streichen einer Zeile.
- Bei jeder Änderung eine höhere Version (SemVer) und ein Eintrag im `CHANGELOG.md`
- Deutsche Texte in Feldern und Sichten; das README auf Deutsch, gern zusätzlich auf Englisch. Englische Beschriftungen (`beschriftungen.en`) sind erwünscht – die mitgelieferten Pakete mit Mappentypen haben sie.
- Ein Pfleger in `CODEOWNERS`
- **Größe:** Ein Paket ist höchstens **128 MB** groß – als Archiv im Katalog und in der Sammeldatei ebenso wie alle Dateien unter `code/` zusammen (`modul.wasm`, `daten/`, Quellcode). Ablago hat dieselbe Grenze (DMS #644); `pruefen.py` und `katalog.py` lehnen größere Pakete ab. Große Daten wie Modelle gehören in eigene Ergänzungspakete (z. B. je Sprache), damit niemand mehr lädt als nötig. Beispiel-Dokumente unter `inhalt/beispiele/` zählen mit (siehe [Beispiel-Dokumente](#beispiel-dokumente)).

## Einstellungen

- Pakete mit Code **beschreiben** ihre Einstellungen im Manifest (`code.einstellungen`, `code.aktionen`). Ablago zeigt das Formular, prüft die Werte, speichert sie (Teil der Sicherung) und gibt sie dem Paket.
- **Zugangsdaten nur als `geheim`**, nie als `text` und nie als `standard`. Ablago verschlüsselt Geheimnisse und zeigt sie nach dem Speichern nicht mehr an.
- **Dienst-Adresse** (ab Ablago 0.124.0, `dms: ">=0.124.0"`): Braucht ein Paket einen Dienst, den jeder Haushalt woanders betreibt (z. B. einen KI-Dienst), verlangt es die Adresse als Einstellung vom Typ `adresse` statt einer festen Adresse in `code.netz`. Höchstens eine je Paket, nur in einem Abschnitt, **ohne** `standard` – höchstens ein `beispiel` für einen Dienst im eigenen Netz (z. B. `http://ollama:11434/v1`). Der Administrator bestätigt die Adresse beim Speichern; nur dorthin lässt der Paket-Läufer das Paket ins Netz. Das README erklärt, was wann dorthin geht.
- Einstellungen ändern ist Sache von Ablago. Ein Paket speichert seine Einstellungen nicht selbst irgendwo anders und bringt keine eigene Oberfläche dafür mit.

## Kategorien

Jedes Paket gehört zu **einer oder zwei Kategorien** aus einer festen Liste in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml) (Vorlagen für die Ablage, Dateiformate, Texterkennung und Volltext, Sprachen, KI, Suche, Post und Scannen, Sicherung, Für Entwickler). Danach filtert die Katalog-Webseite, und „Ähnliche Pakete“ zeigt Pakete derselben Kategorie. Ein neues Paket nennt sie im Manifest, z. B. `kategorien: [dateiformate, volltext]`; die CI prüft es (`python3 werkzeuge/vorlagen.py --pruefen`). Pakete, deren Manifest das Feld noch nicht hat, stehen übergangsweise unter `pakete:` in `kategorien.yaml` – **das Manifest gewinnt**, und `pruefen.py` weist auf Abweichungen hin. Eine neue Kategorie kommt nur über ein Issue dazu, freie Schlagwörter gibt es nicht. Ablago liest das Feld nicht; es liest das Manifest Feld für Feld und übergeht Felder, die es nicht kennt – auch ältere Ablago-Versionen installieren solche Pakete. Ob ein Paket **nur lokal** läuft, sich mit **einem eingetragenen Dienst** verbindet (Einstellung vom Typ `adresse`) oder **feste Adressen im Internet** nutzt (`code.netz`), liest die Webseite selbst aus dem Manifest – dafür gibt es keine Kategorie.

## Symbol

Im Katalog steht bei jedem Paket ein kleines **Symbol**, damit man auf einen Blick sieht, worum es geht. Du wählst es im Manifest mit `symbol:` aus einer **festen Liste** von [Lucide](https://lucide.dev)-Symbolen – denselben einfarbigen Strichsymbolen wie in Ablago. Alle Symbole haben **dieselbe Farbe**; die Farbe zeigt keine Kategorie (dafür gibt es die Kategorie-Chips). Ohne `symbol` zeigt der Katalog den Anfangsbuchstaben, und `pruefen.py` gibt einen Hinweis aus (keinen Fehler). Ein unbekannter Name ist ein Fehler.

```yaml
symbol: languages
kuerzel: FR        # optional, nur mit symbol: höchstens 3 Großbuchstaben unten rechts am Symbol
```

- **Wählen:** Nimm das Symbol, das zeigt, **was das Paket für den Anwender tut** – nicht, wie es das technisch macht. Keine Logos, keine Emoji, keine Flaggen (Flaggen stehen für Länder, nicht für Sprachen). Zusatzsprachen nehmen `languages` mit dem Sprachkürzel als `kuerzel` (FR, ES, IT …).
- **Kürzel:** höchstens 3 Großbuchstaben; Schema und `pruefen.py` lehnen längere ab. Bei Sprachen steht dort der **ISO-639-Code der Sprache, nicht des Landes**: zweistellig nach ISO 639-1 in Großbuchstaben (FR Französisch, PT Portugiesisch, AR Arabisch, **UK Ukrainisch** – nicht UA), dreistellig nach ISO 639-2/3 nur für Sprachen ohne zweistelligen Code.
- **Erlaubt** sind genau die SVG-Dateien in [`werkzeuge/symbole/`](werkzeuge/symbole/) (dieselbe Liste steht im Schema):

| Symbol | passt zu |
| --- | --- |
| `car` | Fahrzeuge |
| `cloud-upload` | Sicherung, Hochladen |
| `contact` | Personen, Kontakte, Grundausstattung |
| `file-signature` | Verträge |
| `file-text` | Dokumente, Office |
| `files` | mehrere Dokumente, Ähnlichkeit |
| `house` | Haus, Wohnung |
| `image` | Bilder, Bildformate |
| `key-round` | Vermietung, Schlüssel |
| `languages` | Sprachen (mit `kuerzel`) |
| `mail` | Post, E-Mail |
| `message-circle-question-mark` | Fragen, Assistent |
| `receipt-text` | Rechnungen, Belege |
| `scan-barcode` | Trennblätter, Barcodes |
| `scan-text` | Texterkennung |
| `wallet` | Geld, Haushalt |

- **Neues Symbol:** über ein Issue. Dann kommt das SVG unverändert aus `lucide-static` nach `werkzeuge/symbole/<name>.svg` und der Name in `schema/manifest.schema.json` (`symbol`); die CI prüft, dass beides übereinstimmt und das SVG nur einfache Formen enthält. Die Webseite bettet das SVG direkt in die Seite ein, nichts wird aus dem Internet geladen. Lizenz der Symbole: ISC ([`werkzeuge/symbole/LICENSE`](werkzeuge/symbole/LICENSE), NOTICE).
- **Bestehende Pakete:** Ihre Symbole stehen übergangsweise unter `symbole:` in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml); mit der nächsten Version wandert das Symbol ins Manifest. Das Manifest gewinnt. Wie `kategorien` liest Ablago `symbol` und `kuerzel` nicht; ältere Ablago-Versionen installieren solche Pakete weiter.
- **Symbol einer Ansicht** (dms #428): In `sichten.yaml` darf jede Ansicht `symbol: <name>` tragen – ein Lucide-Name aus der festen Liste in Ablago ([`shared/src/ansichtsymbole.ts`](https://github.com/motom001/dms/blob/main/shared/src/ansichtsymbole.ts)), z. B. `house`, `car`, `euro`, `mail`. Ablago zeigt es in der Ablage vor dem Namen; einen unbekannten Namen zeigt es ohne Symbol. Ältere Ablago-Versionen ignorieren das Feld.

## Kurzanleitung

Oben auf der Paketseite im Katalog steht **„So nutzt du es“**: 3 bis 5 kurze Schritte, wie man das Paket nach der Installation benutzt (#164). Später zeigt Ablago sie auch einmal direkt nach der Installation (motom001/dms#1047). Das ist **kein Handbuch** – große Themen gehören in einen Rundgang.

```yaml
kurzanleitung:
  de:
    - Lege ein Mietobjekt an und darunter seine Wohnungen.
    - Trage zu jeder Wohnung den Mietvertrag mit Mieter, Miete und Fristen ein.
    - Ordne Rechnungen als Ausgabe dem Mietobjekt zu – „umlagefähig“ angehakt landet in der Nebenkostenabrechnung.
  en:
    - …gleich viele Schritte auf Englisch
```

- Jeder Schritt ist **ein Satz** in Alltagssprache, mit den Namen, die man in Ablago sieht. Höchstens 200 Zeichen.
- Vorlagen-Pakete (mit Mappentypen) und Funktions-Pakete (mit Code) bringen eine Kurzanleitung mit; ohne gibt `pruefen.py` einen **Hinweis** – später wird sie Pflicht. Sprachpakete und Ergänzungen brauchen keine.
- `en` ist optional, hat aber gleich viele Schritte wie `de`. Ältere Ablago-Versionen übergehen das Feld.

## Namen

Schlüssel von Mappentypen, Feldern und Registern sind **im Paket lokal**, z. B. `versicherung`. Ablago legt sie mit der Paket-Id davor an – ab 0.229.0 als `haushalt:versicherung` (Paket und Schlüssel getrennt, motom001/dms#1084), bis 0.228 als `haushalt_versicherung` –, damit sich zwei Pakete nicht in die Quere kommen. Angezeigt wird nur der Name („Versicherung“). Verweise auf Typen anderer Pakete schreibst du als `<paket>:<schluessel>`, z. B. `basis:organisation`. Das andere Paket muss dann unter `abhaengigkeiten` stehen. Auf Mappentypen, die Ablago selbst mitbringt, verweist du mit `dms:` – ohne Abhängigkeit: `dms:benutzer` und `dms:rolle`. Dafür muss im Manifest `dms: ">=0.75.0"` stehen. Den **Ablageort** (wo ein Original liegt) bringt seit Ablago 0.212.0 das Paket Basis mit: `basis:ablageort` mit `basis: ">=1.6.0"` unter `abhaengigkeiten` (Ablago #883, Registry #138). Das frühere `dms:ablageort` versteht Ablago bis 1.0 noch als Alias; `pruefen.py` warnt davor. Die Paket-Id `dms` ist deshalb vergeben.

Beispiel-Mappen dürfen aufeinander verweisen (ab Ablago 0.79.0): Ein Beispiel bekommt einen `schluessel`, ein Verweisfeld eines anderen Beispiels den Wert `{ beispiel: strom }` – oder `{ beispiel: "basis:stadtwerke" }` für ein Beispiel einer Abhängigkeit. Dann muss im Manifest `dms: ">=0.79.0"` stehen.

### Beispiel-Dokumente { #beispiel-dokumente }

Ab Ablago 0.223.0 (motom001/dms#878, Registry #137) kann ein Beispiel Dokumente mitbringen – etwa einen Wartungsvertrag und Rechnungen zur Beispiel-Mappe „Heizung“. Die Dateien liegen unter `inhalt/beispiele/`, das Beispiel nennt sie unter `dokumente`:

```yaml
- typ: vertrag
  schluessel: heizung_wartung
  werte: { bezeichnung: Wartungsvertrag Heizung }
  dokumente:
    - { datei: beispiele/heizung/wartungsvertrag.pdf, titel: Wartungsvertrag, datum: "2023-04-01" }
    - { datei: beispiele/heizung/rechnung-2026.png, register: rechnungen }
```

- `datei` ist relativ zu `inhalt/` und beginnt mit `beispiele/`; Ordner und Namen nur aus Buchstaben, Ziffern, `.`, `-` und `_`. `titel` wird der Name in Ablago, `datum` „hochgeladen am“, `register` das Dokumentenregister (ohne Angabe das erste).
- **Nur PDF, PNG und JPEG** – am Inhalt erkannt, die Endung muss passen. Je Datei höchstens 100 MB wie beim Hochladen in Ablago, alle zusammen höchstens 128 MB; halte sie trotzdem klein (verkleinerte PDFs, Bilder als JPEG). Die Grenze von 2 MB je Datei gilt hier nicht.
- **Jede genannte Datei muss da sein, und jede Datei unter `inhalt/beispiele/` muss genannt sein.** `pruefen.py` meldet bei jeder Prüfung die Größe je Datei und zusammen.
- Pakete mit Beispiel-Dokumenten verlangen `dms: ">=0.223.0"`.
- **Keine echten Daten:** nur erfundene Personen und Firmen (Persona-Namen wie Lena, Jonas, Markus, Petra, Herr Özdemir, Katrin), Beispiel-Domains (`example.org`, `example.com`, `example.net`), ungültige oder ausdrücklich als Beispiel gedachte Werte für IBAN, Steuer- und Versichertennummern. Keine eingescannten echten Briefe, auch nicht geschwärzt – Metadaten, Unterschriften und Logos verraten oft mehr als gedacht.
- **Große Pakete:** Ablago lädt Pakete vom Release (bis 128 MB, Registry #156), die Kopie für die Sammeldatei liegt aber auf dem Branch `gh-pages`, und git nimmt dort keine Datei über 100 MB an (Registry #133). Ein Paket, dessen Archiv größer würde, lässt sich deshalb noch nicht veröffentlichen; `pruefen.py` weist ab 90 MB darauf hin.

## Paketarten

Jedes Paket hat **eine** Art. Die Art steht nicht im Manifest – Katalog und Ablago leiten sie aus dem Inhalt ab. Wähle beim Zuschnitt die Art zuerst; was nicht zu ihr passt, gehört in ein anderes Paket.

| Art | bringt mit | Beispiele | Name |
|---|---|---|---|
| **Grundlagen-Paket** | die gemeinsamen Mappentypen, auf die alle verweisen (Organisation, Person, Ablageort) | Basis | – (gibt es nur einmal, immer dabei) |
| **Vorlagen-Paket** | Mappentypen, Ansichten, Beispiele, mitgelieferte Automatisierungen für **einen** Lebens- oder Fachbereich; **darf Code mitbringen, der nur seine eigenen Mappentypen pflegt** (z. B. Status und Fristen berechnen) | Haushalt, Haus, Fahrzeuge, Vermietung, Verträge, Rechnungen | Hauptwort in der Mehrzahl oder der Bereich |
| **Funktions-Paket** | Code für **alle** Mappen, **keine** eigenen Mappentypen | Texterkennung, PDF/A, Trennblatt, KI | was es tut |
| **Ergänzung** | erweitert **genau ein** anderes Paket (`ergaenzt`, siehe [Ergänzungen](#ergänzungen)) | Zusatzsprachen der Texterkennung, eine Vorlage für eine vorhandene Vertragsart | Hauptpaket + Zusatz |
| **Sprache** | nur Texte für Ablago (siehe [Sprachpakete](#sprachpakete)) | Sprache Französisch | Sprache … |
| **Automatisierungs-Paket** | nur Automatisierungen (und ggf. Einstellungen), keine Mappentypen | Benachrichtigungen | was es auslöst |

- **Jedes Vorlagen-Paket hängt von Basis ab** (`abhaengigkeiten: basis: …`) und verweist auf deren Typen statt eigene Personen oder Organisationen mitzubringen.
- **Code im Vorlagen-Paket** schreibt nur die eigenen Mappentypen (`code.rechte.schreiben`); lesen darf er, was er für die Berechnung braucht. Soll Code an allen Mappen arbeiten, ist es ein Funktions-Paket. `pruefen.py` weist darauf hin.
- **Kleine Pakete, ein Zweck:** Ändert sich etwas an Verträgen, wird nur das Paket Verträge aktualisiert, nicht Haushalt. Lieber ein weiteres Paket mit Abhängigkeit als ein Typ, der in mehreren Paketen halb vorkommt.

### Ein Mappentyp lebt in genau einem Paket

Jeder Mappentyp gehört **genau einem** Paket. Andere Pakete **verweisen** darauf (`vertraege:vertrag`, `basis:organisation`) und nennen das Paket unter `abhaengigkeiten` – sie bringen keinen eigenen Typ gleicher Bedeutung mit, auch nicht unter anderem Schlüssel. Beispiel: Haushalt, Vermietung und Fahrzeuge bringen keine eigenen Vertragstypen mehr mit, sondern hängen von Verträge ab (Registry #163). Die Werkbank zeigt bei jedem Paket, wer davon abhängt.

`pruefen.py` weist darauf hin, wenn zwei Pakete einen Mappentyp mit demselben Namen mitbringen. Zieht ein Typ in ein anderes Paket um, geht das über ein Umbau-Update (Ablago #1041), nie durch Löschen.

## Gleiche Kennungen

Felder mit **derselben Bedeutung** heißen in allen Mappentypen gleich – auch über Pakete hinweg. Dann zeigen Trefferlisten, Ansichten und die erweiterte Suche über mehrere Typen dieselben Spalten („von“ bei Post, Vertrag und Rechnung). Die **Kennung** ist fest, die **Beschriftung** darf je Typ sprechen: `von` heißt am Vertrag „Anbieter“, an der Rechnung „Rechnungssteller“.

| Kennung | Feldart | Bedeutung | nicht |
|---|---|---|---|
| `von` | Verweis | Gegenseite, von der etwas kommt: Anbieter, Rechnungssteller, Verkäufer, Vermieter, Versicherer, Absender | `absender`, `vertragspartner`, `anbieter`, `rechnungssteller` … |
| `an` | Verweis | wer es bekommt: Kunde, Rechnungsempfänger, Käufer, Mieter, Versicherungsnehmer | `empfaenger`, `fuer`, `kunde` … |
| `betrag` | Betrag | Geldbetrag (bei Rechnungen brutto) | `summe`, `preis`, `gesamtbetrag` |
| `datum` | Datum | Datum des Schriftstücks | `rechnungsdatum`, `belegdatum` |
| `betrifft` | Verweis | Gegenstand, um den es geht (Fahrzeug, Wohnung, Vertrag …) | `bezug`, `gegenstand_verweis` |
| `steuerjahr` | Verweis | Steuerjahr, unter dessen „Belegen“ die Mappe erscheint | `veranlagungsjahr` |
| `zustaendig` | Verweis auf `dms:benutzer` | wer sich kümmert, Empfänger von Erinnerungen | `verantwortlich`, `bearbeiter` |
| `verbleib_original` | Verweis auf `basis:ablageort` | wo das Original liegt | `original`, `verbleib` |
| `person_verweis` | Verweis auf `basis:person` | Person des Haushalts bzw. Betriebs | – |
| `bezeichnung` | Text | kurzer Name der Mappe („Handyvertrag Jonas“) | `kurzname` |
| `art` | Auswahl oder Verweis | was es ist | `typ`, `kategorie` |
| `beginn`, `ende` | Datum | Beginn und Ende eines Zeitraums | `von`/`bis` als Datum, `startdatum`, `gueltig_bis` |
| `kuendigen_bis` | Datum (Frist) | letzter Tag zum Kündigen | `kuendigung_bis` |
| `vertragsnummer` | Text | Nummer der Gegenseite | `vertragsnr` |
| `zahlweise` | Auswahl | monatlich, vierteljährlich, jährlich … | `zahlungsweise` |
| `notiz` | langer Text | freie Bemerkungen | `bemerkungen`, `kommentar` |

- **`von` und `an` sind die Parteien.** Ein Zeitraum heißt `beginn`/`ende`. Ablago leitet daraus ab, wer „wir“ sind: Zeigt `von` auf eine eigene Organisation oder eine Person des Haushalts, ist es ausgehend.
- **Neue Felder** in neuen oder geänderten Paketen folgen der Liste; `pruefen.py` gibt einen Hinweis, wenn ein neues Feld eine Kennung aus der Spalte „nicht“ hat oder eine Kennung der Liste mit anderer Feldart nutzt. Bestehende Felder bleiben, bis ein Umbau-Update sie umzieht (Registry #163) – Kennungen ändern bricht sonst Ansichten und Automatisierungen der Nutzer.
- Die Liste wächst über Issues. Hat ein Feld eine Bedeutung, die schon ein anderer Typ kennt, nimm dessen Kennung.

## Text-Vorlagen

Pakete können **Vorlagen als Text** mitbringen – etwa ein Kündigungsschreiben an einer Vertragsart (Registry #160). Ablago macht daraus beim Erzeugen ein PDF (Ablago #1040); wie ein Paket die Vorlagen an seine mitgelieferten Mappen hängt, beschreibt Ablago #1038.

- **Nur Markdown** (`.md`, UTF-8) unter `inhalt/vorlagen/`, höchstens 256 KB je Datei. Keine Office-Formate, auch keine offenen wie `.odt`.
- **Kein HTML** (auch keine Kommentare `<!-- -->`), **keine Bilder** – Briefkopf und Logo setzt Ablago. Links nur mit `https://`, keine anderen Adressen (`http:`, `data:`, `javascript:` …).
- **Platzhalter** wie bei Automatisierungen: `{vertragsnummer}`, `{von.name}`, `{kuendigen_bis}`. Ablago füllt nur Werte, die die Person sehen darf. **Passwortfelder nie** als Platzhalter.
- `pruefen.py` lehnt Vorlagen ab, die gegen diese Regeln verstoßen; **Ablago prüft beim Installieren dasselbe**, denn Pakete können auch als Datei kommen.
- **Lizenz:** Vorlagentexte stehen unter der Lizenz des Pakets. Eine eigene offene Lizenz nur für die Texte (`CC-BY-4.0` oder `CC0-1.0`) legst du als `inhalt/vorlagen/LICENSE` dazu und nennst sie im README.
- **Vertragsmuster:** nur **eigene, schlichte** Muster, keine fremden oder geschützten Texte. Jedes Muster endet mit dem Hinweis *„Muster ohne Gewähr, keine Rechtsberatung – im Zweifel fachlich prüfen lassen.“* Kündigungsschreiben sind unkritisch, Kaufverträge eher vorsichtig formulieren.
- **Keine echten Daten** in Vorlagen (wie bei Beispielen): Platzhalter statt Namen, Adressen oder Nummern.

## Bausteine für Verträge, Rechnungen und Compliance (Etappe 15/16) { #bausteine-etappe-15 }

> **In Ablago ab 0.227.0 bis 0.239.0.** Jeder Baustein kam mit einer eigenen Version (in der Tabelle). `pruefen.py` verlangt genau die höchste, die ein Paket braucht, und nennt die Bausteine dazu – wie die Konstanten `DMS_*_AB` in Ablago. Noch offen sind nur die Rechte für Einrichtung und Nachweise (Compliance, dms #1053/#1054).

| Baustein | so im Paket | Kern |
|---|---|---|
| **Zeitraum** (ab 0.227.0) | `typ: zeitraum`, Wert `{ anzahl: 3, einheit: monate }` (tage, wochen, monate, jahre) oder kurz `P3M` | #1035 |
| **Prozent** (ab 0.227.0) | `typ: prozent`, `nachkomma: 1` | #1035 |
| **Negativer Betrag** (ab 0.227.0) | `typ: betrag`, `negativ: true` (Gutschrift, Erstattung) | #1035 |
| **Mehrere Ziele** (ab 0.230.0) | `ziel: [fahrzeuge:fahrzeug, haus:immobilie]`; mit `mehrfach: true` optional `gleicherTyp: true`. Ziele aus Paketen, von denen das Paket **nicht** abhängt, stehen in `zielOptional` – Ablago nimmt sie dazu, sobald es den Typ gibt (z. B. „betrifft“ einer Rechnung: Fahrzeug, Wohnung, Anschaffung) | #1036 |
| **Anzeigen, wenn …** (ab 0.228.0) | `anzeigen: { modus: alle, bedingungen: [...] }` an Feldern und Abschnitten (`register.abschnitte`), wie im Kern; `modus: eine` heißt „eine davon reicht“. Bedingungen: `{ art: merkmal, merkmal: beruflich }`, `{ art: feld, bedingung: { feld, op, wert: { art: fest, wert } } }` mit den Operatoren der Ansichten je Feldart (Auswahl `einerVon` mit Liste, Ja/Nein `ja`/`nein`, Zahlen `gleich`/`kleiner`/`groesser` …), `{ art: verweistyp, feld, typ: fahrzeuge:fahrzeug }`, ab 0.236.0 `{ art: vorgabe, feld, vorgabe: [miete] }` (zeigt auf die mitgelieferte Mappe, #1038), ab 0.238.0 `{ art: eigeneOrganisation, feld }` (#995); jede mit `nicht: true` umkehrbar. In Ansichten gibt es für Verweise mit mehreren Zielen den Operator `zeigtAufTyp` (ab 0.230.0). Ein ausgeblendeter Abschnitt blendet alle Felder bis zum nächsten aus. **Ordnung, kein Schutz** – Werte bleiben gespeichert und über API und Export sichtbar. | #1032, #1033 |
| **Berechnet** (ab 0.231.0) | `berechnet: true` – nur der Code dieses Pakets schreibt das Feld, in der Oberfläche nur lesbar; braucht `code.rechte.schreiben` auf den eigenen Typ, nie `pflicht` | #1034 |
| **Hinweis an der Mappe** (ab 0.231.0) | `code.rechte.schnittstellen: [dms:hinweise]` – `PUT`/`DELETE /api/v1/mappen/{id}/hinweise/{schluessel}` mit `{ text }`, reiner Text bis 300 Zeichen, höchstens 3 je Paket und Mappe; Speichern hindert er nie | #1034 |
| **Nach Zeitplan** (ab 0.233.0) | eine mitgelieferte Automatisierung mit `wenn: { art: zeitplan, … }` und der Dann-Karte `{ art: paket, aufgabe: taeglich }` („Paket nach Zeitplan ausführen“), gern mit `eingeschaltet: true`; das Paket abonniert `zeitplan.ausgefuehrt` und bekommt `aufgabe` und `datum`. Der Admin sieht den Lauf unter Automatisierungen und kann Uhrzeit und Tage ändern. Ruft nur das eigene Paket auf. | #1082 |
| **Tabelle** (ab 0.232.0) | `typ: tabelle`, `quelle: { typ: rechnungsposition, feld: rechnung, trefferliste, neu: "+ Position" }` – kein eigener Wert, nie Pflicht oder berechnet; `neu` höchstens 40 Zeichen, englisch unter `beschriftungen.en.neu` | #1030 |
| **Gehört immer zu** (ab 0.235.0) | am Mappentyp `gehoertZu: rechnung` – die Kennung des **Verweisfelds** (genau ein Zieltyp, eine Mappe, Pflicht, ohne `zielOptional` und `anzeigen`; keine Ketten) – nicht in Ansichten und Suche | #1031 |
| **Zusammengesetzt** (ab 0.239.0) | `typ: zusammengesetzt`, `vorlage: "{von} · {rechnungsnummer}"` (höchstens 300 Zeichen), gern `eindeutig: true`; nie Pflicht, berechnet oder mit `standard` – den Wert setzt Ablago, auch nicht in Beispielen | #1050 |
| **Vorbelegen** (ab 0.234.0) | an einem Verweisfeld `vorbelegen: [{ von: kuendigungsfrist, nach: kuendigungsfrist }]` – nur in leere Felder, als Vorschlag | #1037 |
| **Eigene Organisation** (ab 0.238.0) | Ja/Nein-Feld mit `merkmal: eigeneOrganisation` und `schreibschutz: verwaltung` (nur mit Verwaltungsrecht änderbar) | #995 |
| **Vorgaben** (ab 0.236.0) | `inhalt.vorgaben: inhalt/vorgaben.yaml` – Mappen mit fester `kennung`, die bleiben (z. B. Vertragsarten), mit `werte`, `beschriftungen` je Sprache und `vorlagen` (nur [Text-Vorlagen](#text-vorlagen), je `datei`, `titel`, `register`; höchstens 20). Verweis darauf in Werten `{ vorgabe: miete }` bzw. `{ vorgabe: "vertraege:miete" }`. Eine **Ergänzung** hängt mit `ergaenzt: "vertraege:pkw_kaufvertrag"` nur Vorlagen an die Vorgabe eines Pakets unter `abhaengigkeiten`. Höchstens 200 Einträge. | #1038 |

```yaml
# inhalt/vorgaben.yaml (Paket Verträge)
- kennung: mobilfunk
  typ: vertragsart
  werte: { name: Mobilfunk, mindestlaufzeit: { anzahl: 24, einheit: monate }, kuendigungsfrist: { anzahl: 1, einheit: monate } }
  beschriftungen: { en: { name: Mobile phone } }
  vorlagen:
    - { datei: vorlagen/kuendigung.md, register: vorlagen, titel: Kündigung }
```

`pruefen.py` prüft, was im Paket selbst nachprüfbar ist: Felder und Vorgaben, auf die verwiesen wird, Quelle einer Tabelle, Platzhalter einer Zusammensetzung, Schreibrecht für berechnete Felder, Werte von Zeiträumen, Dateien der Vorgaben.

## Ergänzungen

Ein Paket, das ein anderes erweitert – etwa eine Zusatzsprache die Texterkennung –, sagt das mit `ergaenzt` (motom001/dms#405). Das ergänzte Paket steht auch unter `abhaengigkeiten`:

```yaml
abhaengigkeiten:
  texterkennung: ">=2.0.0"
ergaenzt: { paket: texterkennung, gruppe: Weitere Sprachen }   # oder kurz: ergaenzt: texterkennung
```

**Id mit Punkt** (ab Ablago 0.229.0, motom001/dms#1084): Eine Ergänzung darf `<hauptpaket>.<zusatz>` heißen, z. B. `texterkennung.fra`. Der Punkt heißt immer „ergänzt das Paket vor dem Punkt“ – das Paket muss dann `ergaenzt: <hauptpaket>` angeben, das Hauptpaket gibt es in der Registry, und `dms` ist mindestens `">=0.229.0"`. Neue Ergänzungen nehmen diese Form.

Ablago ab 0.151.0 zeigt Ergänzungen beim Installieren als Häkchen unter dem ergänzten Paket, gruppiert nach `gruppe` (kurze Frage ohne Fragezeichen, höchstens 40 Zeichen; ohne Gruppe: „Ergänzungen“) – auch nachträglich, im Einrichtungsassistenten und in der Sammeldatei. Jede Ergänzung bleibt ein eigenes Paket mit eigener Version. Ältere Ablago-Versionen ignorieren das Feld, deshalb braucht es kein höheres `dms`. Im Katalog steht es je Version als `ergaenzt: { paket, gruppe }`, auf der Katalog-Webseite als eigene Gruppe unter „Passt dazu“.

**Was eine Ergänzung darf:** Sie fügt dem ergänzten Paket etwas hinzu – Daten (z. B. ein Sprachmodell) oder Dokumente an dessen Vorgaben (z. B. eine Vorlage an eine vorhandene Vertragsart). Sie **ändert keine Mappentypen und keine Rechte** des ergänzten Pakets, bringt keine eigenen Mappentypen mit und ändert keine fremden Vorlagen. Entfernt man sie, nimmt sie nur mit, was sie selbst hinzugefügt hat.

## Neue Id (Umzug)

Bekommt ein Paket eine neue Id (motom001/dms#1084, z. B. `texterkennung_fra` → `texterkennung.fra`), zieht der **Ordner** um, und das Manifest nennt die alte Id unter `ersetzt` (Text oder Liste, höchstens 5):

```yaml
id: texterkennung.fra
version: 1.1.0          # höher als die letzte Version unter der alten Id
dms: ">=0.229.0"
ersetzt: texterkennung_fra
```

- Ablago ab 0.229.0 nimmt die neue Id als **Update** der Installation unter der alten – mit allen Mappentypen, Mappen, Einstellungen und Daten; ein zweites Paket entsteht nicht. Das geht nur aus derselben Quelle und vom selben Herausgeber.
- Die alte Id **fällt aus dem Katalog**; `katalog.json` nennt sie am neuen Paket unter `ersetzt`. Ihre Releases bleiben stehen, ihre Downloads zählen beim neuen Paket mit. Ältere Ablago-Versionen behalten das Paket unter der alten Id, bis sie aktualisiert sind.
- Die alte Id steht weiter in `werkzeuge/ids.txt` und wird nie wieder vergeben; die neue kommt dazu. `pruefen.py` prüft, dass es die alte Id gab und ihr Ordner weg ist.
- Kein Alias: Wer das Paket irgendwo mit der alten Id nennt (Abhängigkeiten, Verweise), zieht im selben Pull Request mit.

## Umbau: ein Mappentyp zieht in ein anderes Paket { #umbau }

Gibt ein Paket einen Mappentyp ab (Registry #163: Haushalt gibt *Vertrag* und *Versicherung* an Verträge ab), bringt **das Paket, das ihn aufnimmt,** Umbau-Schritte im Manifest mit (Ablago ab 0.243.0, motom001/dms#1041, `dms: ">=0.243.0"`):

```yaml
umbau:
  - von: "haushalt:versicherung"   # alter Typ; ohne Präfix ein früherer eigener
    nach: vertrag                   # Typ dieses Pakets oder paket:schluessel einer Abhängigkeit
    felder: { versicherer: von, beitrag: betrag }          # alt → neu; ohne Zuordnung: Notiz
    setzen: { art: { vorgabe: versicherung }, bezeichnung: Versicherung }   # feste Werte in leere Felder
    register: { unterlagen: dokumente }                     # Dokumentregister alt → neu
```

- Beim Installieren bzw. Aktualisieren zeigt Ablago je Schritt, wie viele Mappen umziehen und welche Werte wohin gehen, und fragt bei Feldern nach, die der Administrator selbst angelegt hat. Mappen, Dokumente, Verweise, Ansichten, Automatisierungen und Rechte-Regeln ziehen mit; was nicht passt, steht in einer **Notiz** an der Mappe. Gibt es den Zieltyp noch nicht, **übernimmt** der erste Schritt den alten Typ mit seiner Id – dann gibt es auch keinen Namenskonflikt.
- Nur einzeln (nicht im Ablauf mehrerer Pakete), nur mit „Gesamte Verwaltung“. Ein Schritt, dessen alter Typ nicht (mehr) da ist, entfällt still – Umbau-Schritte dürfen also in späteren Versionen stehen bleiben.
- **Das abgebende Paket** bekommt eine **Major-Version** ohne den Typ (Breaking Change im CHANGELOG), hängt vom aufnehmenden Paket in der Version mit dem Umbau ab und verweist auf dessen Typ. So kommt das Update erst, wenn der Umbau gelaufen ist.
- Werte zieht Ablago nur in passende Felder um (gleiche Feldart, Text → Zeitraum/Zahl/Datum/Auswahl, Verweise nur auf erlaubte Typen). Mehrere alte Felder auf ein neues: Der erste gefüllte Wert in der Reihenfolge des alten Typs gilt. `setzen` schreibt Werte so, wie sie sind – Text, Zahl, Ja/Nein, Liste oder `{ vorgabe: … }`, kein Zeitraum und kein Betrag.
- `pruefen.py` prüft Form, Zieltyp, die neuen Felder (vorhanden, nicht berechnet), `setzen` gegen Feldart und Optionen und die alten Feldkennungen gegen den Typ, wie er zuletzt in der Registry stand (auch aus der git-Geschichte). Die CI installiert außerdem alle Pakete mit dem echten Installer einer festen Ablago-Version (`pakete-pruefen` im Image `ghcr.io/motom001/dms`, motom001/dms#1124) – im Pull Request als Update vom Stand des Ziel-Zweigs aus, Umbau eingeschlossen. Lokal: `docker run --rm -v "$PWD/pakete:/neu:ro" ghcr.io/motom001/dms:<version> pakete-pruefen /neu`.

## Beschriftungen je Sprache

Mappentypen, Felder, Auswahlwerte, Register und Ansichten eines Pakets bekommen Beschriftungen in weiteren Sprachen (Ablago #728, Registry #135) – dann erscheinen sie in einer englischen Ablago englisch:

```yaml
- schluessel: vertrag
  name: Vertrag                     # deutscher Grundtext, wie bisher
  beschreibung: Strom, Gas, Internet …
  beschriftungen: { en: { name: Contract, beschreibung: "Electricity, gas, internet …" } }
  felder:
    - key: art
      label: Art
      typ: auswahl
      optionen: [Strom, Gas, Wasser]   # die festen Werte – genau die stehen in den Mappen
      beschriftungen:
        en: { label: Type, optionen: { Strom: Electricity, Gas: Gas, Wasser: Water } }
  register:
    - { key: allgemein, name: Allgemein, art: felder, felder: [art], beschriftungen: { en: { name: General } } }
```

- **Wo:** am Mappentyp und an Ansichten `name` und `beschreibung`, an Feldern `label`, `hilfe` und `optionen` (fester Wert → Text), an Registern `name`.
- **Sprachen:** Kennungen wie `en`, `fr` oder `pt-BR`; höchstens 30 je Eintrag, je Text höchstens 500 Zeichen, ohne spitze Klammern (kein HTML).
- **`optionen` bleiben eine Liste von Zeichenketten** – das sind die festen Werte, die Mappen speichern. Schlüssel unter `beschriftungen.<sprache>.optionen` müssen unter `optionen` stehen, und es gibt sie nur bei Auswahlfeldern.
- **Deutsch ist der Grundtext** (`label`, `name` …). `beschriftungen.de` gibt es nur für `optionen` – etwa ein neutraler Wert `strom` mit der Beschriftung „Strom“.
- **Ohne höheres `dms`:** Ablago ab 0.200.0 übernimmt die Beschriftungen beim Installieren, ein Update ergänzt nur, was der Administrator noch nicht beschriftet hat. Ältere Versionen übergehen das Feld; Pakete mit reinen Textoptionen funktionieren unverändert. Neue Beschriftungen sind eine Minor-Version.

`werkzeuge/pruefen.py` prüft Form, Sprachkennungen, Optionen und `de`.

## Sprachpakete

Weitere Sprachen für Ablago kommen als **Sprachpaket** (Ablago #731, Registry #116, ab Ablago 0.203.0). Ein Sprachpaket enthält **nur Texte** – keinen Code, keine Mappentypen, kein HTML:

```
pakete/sprache_fr/
  manifest.yaml  README.md  LICENSE  CHANGELOG.md
  tests/erwartung.yaml            mappentypen: [], sichten: [], sprache: fr
  texte/<bereich>.json            Texte der Oberfläche, Meldungen, E-Mails – wie shared/src/sprachen/<sprache>/ in Ablago
  beschriftungen/<paket>.yaml     Beschriftungen der Standardpakete (optional)
```

```yaml
id: sprache_fr                    # immer sprache_<kennung>, z. B. sprache_pt_br
name: "Sprache: Französisch (Français)"
dms: ">=0.203.0"
symbol: languages
kuerzel: FR                       # die Sprachkennung in Großbuchstaben
kategorien: [sprachen]
sprache:
  kennung: fr                     # Deutsch und Englisch sind eingebaut
  gebietsschema: fr-FR            # Datum, Zahlen, Beträge
  ablago: 0.203.0                 # Ablago-Version, für die die Texte gemacht sind
  maschinell: true                # maschinell übersetzt → Hinweis in Ablago und im Katalog
  # geprueft_von: "@github-name"  # wer die Übersetzung geprüft hat
inhalt: {}
```

- **Texte** (`texte/<bereich>.json`): flach, dieselben Bereiche, Schlüssel und Platzhalter wie die deutschen Sprachdateien von Ablago; am einfachsten übersetzt man die englischen. Mehrzahl nach den Regeln der Sprache (`_one`, `_few`, `_many`, `_other`). **Immer die vertraute Anrede** (du, tu, je, ty …) – eine förmliche Fassung gibt es nicht. Je Text höchstens 4000 Zeichen, alle zusammen höchstens 4 MB, keine Steuerzeichen, **spitze Klammern nur, wo der deutsche Text sie hat** (kein HTML).
- **Beschriftungen** (`beschriftungen/<paket>.yaml`): Mappentypen (Name, Beschreibung, Felder mit `label`, `hilfe`, `optionen`, Register) und Ansichten eines Pakets dieser Registry, mit den Schlüsseln des Pakets ohne Präfix. Ablago ergänzt sie an installierten Paketen, nur wo in dieser Sprache noch nichts steht. `pruefen.py` prüft, dass es Paket, Mappentyp, Feld, Option, Register und Ansicht gibt.
- **Verboten:** `code`, Einträge unter `inhalt`, `abhaengigkeiten`, `ergaenzt` und alle anderen Dateien (`code/`, Bilder, Skripte). Ablago lehnt solche Sprachpakete ab.
- **Fehlt etwas**, erscheint es auf Englisch. Schlüssel, die eine Ablago-Version nicht (mehr) kennt, und Texte mit anderen Platzhaltern übergeht Ablago – das Paket bleibt installierbar.
- **Maschinell übersetzt** (`maschinell: true`) zeigen Ablago (Mein Konto, Paketvorschau) und die Katalog-Webseite „Maschinell übersetzt – Verbesserungen willkommen“ mit Link. Wer eine Sprache durchgesehen hat, trägt sich unter `geprueft_von` ein; dann steht dort „Geprüft von …“.
- **Mithelfen:** Issue-Vorlage [„Übersetzung verbessern“](https://github.com/motom001/dms-registry/issues/new?template=uebersetzung.yml) oder ein Pull Request (Text ändern, Patch-Version, Eintrag im `CHANGELOG.md`). Neue Texte einer neuen Ablago-Version: Minor-Version, `sprache.ablago` anheben.
- **Abdeckung:** `python3 werkzeuge/sprachen.py --ablago <checkout von motom001/dms>` prüft jede Sprache gegen die deutschen Texte von Ablago, nennt „Übersetzung … % vollständig“ und mit `--fehlend` die fehlenden Texte auf Englisch. Die CI vergleicht mit der neuesten veröffentlichten Ablago-Version und schreibt die Abdeckung in die Zusammenfassung; nur Fehler wie HTML machen sie rot.

Das Format beschreibt auch das Entwicklerhandbuch von Ablago unter [Sprachpakete](https://help.ablago.app/entwickler/aktuell/pakete/#sprachpakete).

## Felder für die Erkennung

Ablago erkennt Post und füllt Mappen aus Dokumenten (DMS #336, #391) – ohne KI, mit Mustern und dem Abgleich mit vorhandenen Mappen. Welche Felder es dafür nutzt, sagt das Paket mit der Feld-Eigenschaft `erkennung`:

```yaml
- key: kundennummer
  label: Kundennummer
  typ: text
  erkennung: { art: nummer, hinweis: "Steht meist oben rechts im Brief" }
- { key: email, label: E-Mail, typ: text, erkennung: {} }   # art ergibt sich aus der Bezeichnung
```

- **Markiere, was ein Schreiben eindeutig zuordnet:** Kunden-, Vertrags-, Versicherungs- oder Aktenzeichen, Kennzeichen, IBAN, Umsatzsteuer-Id, E-Mail-Adresse, Internetseite, Telefon, Name. Hat ein Typ markierte Namen oder Kontaktangaben (`name`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`), gilt er als möglicher **Absender** (Organisation, Person); markiert er nur Nummern, als mögliche **Zielmappe**.
- **Markiere, was „Aus Dokument ausfüllen“ füllen soll:** Datum, Betrag, Anschrift, Vorname/Nachname, Funktion, Verweise (z. B. Werkstatt einer Rechnung). Hat ein Typ markierte Felder, füllt Ablago nur diese.
- **Nicht markieren**, was in fremden Briefen ständig vorkommt und nichts zuordnet – z. B. die IBAN des eigenen Kontos (steht in jeder Lastschrift) oder eine Nummer, die viele Mappen gemeinsam haben.
- Nur bei den Feldarten `text`, `langtext`, `zahl`, `betrag`, `datum`, `auswahl` und `referenz`; nie bei `passwort`. `art` (optional) muss zur Feldart passen: `name`, `vorname`, `nachname`, `funktion`, `nummer`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`, `strasse`, `hausnummer`, `plz`, `ort` bei Text; `nummer`, `plz`, `hausnummer`, `betrag` bei Zahl; `datum`, `betrag`, `auswahl`, `verweis` bei der gleichnamigen Feldart. `hinweis` hat höchstens 300 Zeichen; ein Muster nach dem Wort *Muster* (`#` = Ziffer, `A` = Großbuchstabe, z. B. „Muster 100-####“) sucht Ablago gezielt.
- Wer `erkennung` nutzt, schreibt im Manifest `dms: ">=0.113.0"`. Ein Update des Pakets übernimmt die Markierung an installierten Feldern, an denen der Administrator nichts zur Erkennung eingestellt hat; das ist eine Patch-Version (mit neuen Feldern eine Minor-Version).

`werkzeuge/pruefen.py` prüft Feldart, Art und Ablago-Version.

## Text in Verweis umwandeln

Steht in einem Paket ein Mensch, eine Firma oder ein anderes Ding als **Text**, wo ein **Verweis** hingehört (z. B. „Halter: Lena Muster“ am Fahrzeug), machst du daraus in einer neuen Version ein Verweisfeld und sagst mit `aus_text`, aus welchem bisherigen Textfeld es sich füllen lässt (DMS #534):

```yaml
- { key: halter_verweis, label: Halter, typ: referenz, ziel: "basis:person", verweisart: bezug, aus_text: halter }
```

- **Neue Kennung:** Das Verweisfeld bekommt eine eigene Kennung – üblich ist die alte mit `_verweis` dahinter. Das alte Textfeld nimmst du aus dem Paket (Feld, Register, Trefferliste, Titel-Vorlage). Neue Installationen bekommen nur noch den Verweis.
- **Nichts geht verloren:** Bei einem Update legt Ablago das Verweisfeld **zusätzlich** an; das alte Textfeld bleibt mit allen Werten. Das gilt nicht als Löschen eines Felds. Erst in der Werkbank (Pakete → Paket → *Text in Verweise umwandeln*) schlägt Ablago je Name eine vorhandene Mappe vor, legt auf Wunsch eine neue an oder überspringt; erst dann wird umgewandelt, mit Eintrag in der Historie und rückgängig zu machen. Updates ändern nichts heimlich.
- **Keine Pflicht:** Ein Verweisfeld mit `aus_text` ist nie `pflicht` – sonst passten vorhandene Mappen nach dem Update nicht mehr.
- **Verweisart:** Für Personen und Organisationen `bezug` – wer eine Person löscht, löscht damit nicht Auto oder Konto.
- **Mehrere Namen:** Steht im Text oft mehr als einer („Lena und Tom Muster“), nimm `mehrfach: true`; Ablago teilt den Text dann an „und“, Komma, Schrägstrich oder „&“.
- Nur bei Verweisfeldern; `aus_text` nennt ein anderes Feld, und steht das noch im Paket, ist es `text` oder `langtext`.
- Wer `aus_text` nutzt, schreibt im Manifest `dms: ">=0.120.0"`. Neue Felder bzw. die Umwandlung sind eine **Minor-Version**.

`werkzeuge/pruefen.py` prüft Feldart, Quelle, Pflicht und Ablago-Version.

## Auswahl einschränken und Verweise, die aus anderen folgen

Ein Verweisfeld kann nur passende Mappen anbieten – mit `auswahlFilter`, Bedingungen wie bei einer Ansicht (DMS #172). Mit `wert: { art: eigenesFeld, feld: … }` nimmt eine Bedingung den Wert eines anderen Felds derselben Mappe (DMS #173), z. B. bei der Person (Basis): nur Niederlassungen der gewählten Organisation.

```yaml
- key: niederlassung
  label: Niederlassung
  typ: referenz
  ziel: niederlassung
  auswahlFilter: [{ art: feld, feld: organisation, op: zeigtAuf, wert: { art: eigenesFeld, feld: organisation } }]
```

- `feld` ist ein Feld des **Ziel**-Mappentyps, `wert.feld` ein **anderes** Feld dieses Mappentyps. Ist es leer, gilt die Bedingung nicht – dann erscheinen alle.
- **Streng:** Ein neu gewählter Wert, der nicht passt, wird beim Speichern abgelehnt; gespeicherte bleiben gültig, Ablago zeigt dann am Feld, womit sie nicht passen (ab 0.225.0, DMS #887). Nimm den Filter nur, wenn das fachlich so sein muss (eine Zweigstelle gehört zu genau einer Organisation).

Die **Gegenrichtung** heißt `folgtAus` (DMS #886): Ein Verweisfeld füllt sich aus einem anderen Verweisfeld dieser Mappe, über ein Verweisfeld von dessen Ziel – etwa *Organisation* aus *Niederlassung* → *Organisation*.

```yaml
- { key: organisation, label: Organisation, typ: referenz, ziel: organisation, folgtAus: { feld: niederlassung, zielFeld: organisation } }
```

- `feld` ist ein anderes Verweisfeld dieses Mappentyps mit **einer** Mappe, `zielFeld` ein Verweisfeld mit einer Mappe in dessen Ziel, das auf denselben Mappentyp zeigt wie dieses Feld. Keine Kreise.
- Ablago füllt nur ein **leeres** Feld, überschreibt nie und fragt nach, wenn die Angaben nicht zusammenpassen. Bestehende Mappen bleiben, wie sie sind.
- Wer `folgtAus` nutzt, schreibt im Manifest `dms: ">=0.225.0"`. Ein Auswahlfilter allein braucht keine neue Version.

`werkzeuge/pruefen.py` prüft Feldart, die genannten Felder (soweit sie im Paket stehen), Kreise und die Ablago-Version.

## Formate und Datumsgrenzen

Ablago prüft Angaben in Textfeldern nach einem **Format** und Datumsfelder nach **Grenzen** (DMS #535). So landen keine PLZ mit Buchstaben, keine Telefonnummer mit Buchstaben und kein Geburtstag in der Zukunft in den Mappen. Am Handy erscheint die passende Tastatur, Telefon und E-Mail lassen sich antippen.

```yaml
- { key: telefon, label: Telefon, typ: text, maxLen: 40, format: telefon }
- { key: email, label: E-Mail, typ: text, maxLen: 200, format: email }
- { key: internet, label: Internetseite, typ: text, maxLen: 200, format: internetseite }
- { key: iban, label: IBAN, typ: text, maxLen: 42, format: iban }
- { key: plz, label: PLZ, typ: text, maxLen: 10, format: plz, landFeld: land }
- { key: land, label: Land, typ: text, maxLen: 60, standard: Deutschland }
- { key: geburtstag, label: Geburtstag, typ: datum, max: heute }
- { key: einzug, label: Einzug, typ: datum, min: "2000-01-01" }
```

- **`format`** nur bei `typ: text`: `email` (`name@beispiel.de`), `telefon` (Ziffern, `+` am Anfang, Leerzeichen, `/`, `-`, Klammern), `internetseite` (mit oder ohne `https://`), `iban` (Länge des Landes und Prüfziffer, Anzeige in Vierergruppen) oder `plz`.
- **`landFeld`** nur bei `format: plz`: die Kennung eines Text- oder Auswahlfelds desselben Mappentyps mit dem Land. Steht dort Deutschland oder nichts (und ist die Vorgabe Deutschland), sind **genau 5 Ziffern** Pflicht; bei anderen Ländern ist die PLZ frei. Ohne `landFeld` gilt immer Deutschland – gib bei Anschriften deshalb ein Feld *Land* mit.
- **`min`** und **`max`** bei `typ: datum`: `heute` oder ein Datum `"JJJJ-MM-TT"` (in Anführungszeichen, sonst liest YAML es als Datum). Setze Grenzen nur, wo eine Angabe sonst sicher falsch ist – `max: heute` für Geburtstag, Erstzulassung oder „abgelesen am“; nie für Fristen wie „gültig bis“.
- Gespeicherte Werte bleiben gültig: Ablago prüft nur neue und geänderte Angaben. Ein Update übernimmt Format und Grenzen an installierten Feldern, an denen der Administrator weder Format noch Grenzen eingestellt hat; das ist eine Minor-Version.
- **Beispiele müssen passen** – Ablago legt sie mit denselben Prüfungen an. Nimm erfundene, aber gültige Werte: Persona-Namen, Testnummern wie `+49 30 123456`, die Test-IBAN `DE89 3704 0044 0532 0130 00`.
- Wer `format`, `landFeld` oder Datumsgrenzen nutzt, schreibt im Manifest `dms: ">=0.121.0"`.

`werkzeuge/pruefen.py` prüft Feldart, Land-Feld, Grenzen, die Beispiele und die Ablago-Version.

## Wortlisten

Ein Paket kann **gleichbedeutende Wörter** für die Suche mitbringen (ab Ablago 0.127.0): Wer eines sucht, findet auch die anderen. Im Manifest steht `inhalt.wortlisten: inhalt/wortlisten.yaml`, dazu `dms: ">=0.127.0"` – ältere Ablago-Versionen übergehen den Abschnitt stillschweigend. Die Datei ist eine Liste von Gruppen:

```yaml
- woerter: [Kfz, Auto, PKW, Fahrzeug]
- woerter: [Nebenkosten, Betriebskosten]
```

- Je Gruppe 2 bis 20 verschiedene Wörter, je 2 bis 60 Zeichen; Groß-/Kleinschreibung und Umlaute zählen beim Vergleich nicht („Gebühr“ und „gebuhr“ sind dasselbe Wort). Höchstens 1000 Gruppen je Paket.
- Nur Wörter, die im Alltag wirklich dasselbe meinen und zum Thema des Pakets gehören – keine Oberbegriffe („Vertrag“ für alles) und keine Namen von Firmen oder Personen.
- Allgemeine Wörter, die in jeder Ablage vorkommen (Rechnung/Beleg, Vertrag/Vereinbarung), stehen im Paket **Basis**; Fachpakete bringen nur ihre fachlichen Wörter mit. Ein Wort steht in höchstens einem Paket des Katalogs (`werkzeuge/test_pruefen.py` prüft das).
- `tests/erwartung.yaml` nennt die Zahl der Gruppen: `wortlisten: 5`.
- Ablago legt die Gruppen beim Installieren an, ersetzt sie bei einem Update durch die des Pakets und entfernt sie mit dem Paket.

## Automatisierungen

Ein Paket kann **vorgefertigte Automatisierungen** mitbringen (ab Ablago 0.177.0, Ablago #712): Wenn · Und · Dann wie im Editor unter *Werkbank → Ablage aufbauen → Automatisierungen*. Im Manifest steht `inhalt.automatisierungen: inhalt/automatisierungen.yaml`, dazu `dms: ">=0.177.0"`.

```yaml
- schluessel: hu_bald
  name: HU wird bald fällig
  beschreibung: Einen Monat vor der Hauptuntersuchung bekommt der Verantwortliche eine Frist.
  wenn: { art: datum, typ: fahrzeug, feld: hu_faellig, vorlauf: 1, einheit: monate, uhrzeit: "07:00" }
  dann:
    - { art: aufgabe, als: aufgabe, empfaenger: [{ art: feld, feld: verantwortlich, sonst: ersteller }], text: "Für {kennzeichen} wird bald die HU fällig: {datum}." }
```

- **Nach der Installation aus.** Beim Installieren fragt Ablago mit dem Namen jeder Automatisierung, ob sie gleich eingeschaltet werden soll (Vorgabe: ja). In der Werkbank stehen sie als „aus Paket …“. Ein Update ersetzt nur unveränderte; beim Entfernen gehen unveränderte, ausgeschaltete mit.
- **Genau eine Wenn-Karte:** `datum` (*Datum erreicht*, mit `typ`, `feld` als Datumsfeld, `vorlauf`, `einheit` tage/wochen/monate, optional `uhrzeit`, `wiederholung` in Monaten) oder ein Ereignis wie `mappe.angelegt`, `mappe.geaendert`, `dokument.hochgeladen`, `post.angelegt`, `benutzer.abwesenheit_gesetzt`. Mappentypen als eigener Schlüssel oder `paket:typ` einer Abhängigkeit.
- **Zeitplan** (ab Ablago 0.181.0, DMS #678): `{ art: zeitplan, uhrzeit: "07:00", tage: [1, 2, 3, 4, 5], feiertage: true, jeBenutzer: true, profilzeit: true }` – Wochentage 1 = Montag … 7 = Sonntag; `jeBenutzer` läuft je aktivem Benutzer einmal am Tag, `profilzeit` nimmt Uhrzeit, Wochentage und Feiertage aus dem Profil. `rolle` gibt es in Paketen nicht. Dazu die Wenn-Karte `favorit.geaendert`.
- **Dann-Karten:** `aufgabe` (Aufgabe oder Benachrichtigung mit Text und Platzhaltern), `feld` (Felder setzen), `stopp`; ab 0.181.0 außerdem `zusammenfassung` (nur mit Zeitplan `jeBenutzer`), `favoriten` (nur mit `favorit.geaendert`) und `anmeldeschutz` mit `was: sammel` (Zeitplan, nicht je Benutzer) oder `was: konto` (`benutzer.gesperrt`). Karten, die Daten nach draußen schicken (E-Mail, Adresse aufrufen), gibt es in Paketen noch nicht.
- **Keine festen Personen oder Rollen:** Empfänger ist ein Feld der Mappe, das auf Benutzer verweist (`ziel: dms:benutzer`), optional mit `sonst: ersteller`, oder `ersteller` (wer die Mappe angelegt hat).
- **Jede Frist erinnert:** Seit Ablago 0.177.0 legt ein Datumsfeld mit `frist` keine Aufgaben mehr selbst an. Ein Paket mit `dms: ">=0.177.0"` bringt deshalb für jedes Frist-Feld eine Automatisierung *Datum erreicht* mit; `frist.vorlauf` ist nur noch die Vorgabe. `pruefen.py` meldet Fristen ohne Automatisierung.
- `tests/erwartung.yaml` nennt die Zahl: `automatisierungen: 3`.

## Automatisierungsvorlagen

Ein Paket kann **Automatisierungsvorlagen** mitbringen (ab Ablago 0.256.0, Ablago #1044): Abläufe, die man im Menü **Mappe ▾** an *einer* Mappe anwendet – wie „Aufgabe vergeben“ und „Erinnern“. Im Manifest steht `inhalt.ablaufvorlagen: inhalt/ablaufvorlagen.yaml`, dazu `dms: ">=0.256.0"`.

```yaml
- schluessel: wiedervorlage
  name: Wiedervorlage
  beschreibung: In sechs Monaten steht die Mappe wieder unter „Zu erledigen“.
  wann: { art: in, anzahl: 6, einheit: monate }
  fragen: []
  karten:
    - { art: aufgabe, als: aufgabe, empfaenger: [{ art: selbst }], text: "Wiedervorlage: {titel}" }
```

- **Wann:** `sofort`, `datum` (das Datum wird beim Anwenden gefragt) oder `in` mit `anzahl` und `einheit` tage/wochen/monate.
- **Fragen** beim Anwenden: `empfaenger`, `datum`, `text`. `datum` genau dann, wenn `wann.art: datum`; `empfaenger` genau dann, wenn eine Karte den Empfänger `frage` hat; `text` braucht `{eingabe}` in einem Kartentext.
- **Nur die Karte `aufgabe`** (Aufgabe oder Benachrichtigung). Karten, die Daten nach außen schicken (E-Mail, Adresse aufrufen) oder Felder setzen, gibt es in Vorlagen nicht – auch nicht in Updates. Ablago zeigt beim Installieren jede Vorlage mit ihren Karten und weist zurück, was nicht erlaubt ist.
- **Empfänger:** `frage` (die beim Anwenden gewählte Person), `selbst` (wer anwendet), `ersteller` (wer die Mappe angelegt hat) oder `feld` (ein Feld der Mappe mit `ziel: dms:benutzer`, nur mit `typen`). Feste Personen oder Rollen gibt es nicht.
- **Platzhalter** wie in Automatisierungen, dazu `{eingabe}`, `{person}` und `{empfaenger}`. Ablago füllt sie mit den Rechten des Empfängers.
- **`typen`** (eigene Schlüssel oder `paket:typ` einer Abhängigkeit): nur an diesen Mappentypen im Menü; ohne `typen` an allen. **`reihenfolge`** 1–99 (kleiner weiter oben).
- **`ersetzt: aufgabe_vergeben`** bzw. **`ersetzt: erinnern`** überlagert die Vorlage von Ablago (je Paket höchstens einmal). Entfernt man das Paket, gilt wieder die von Ablago. Hat ein Administrator die Vorlage geändert oder überlagert schon ein anderes Paket, bleibt sie, wie sie ist.
- Ein Update ersetzt nur unveränderte Vorlagen; beim Entfernen gehen sie mit – außer solchen mit offenen Abläufen, die als eigene Vorlage bleiben.
- `tests/erwartung.yaml` nennt die Zahl: `ablaufvorlagen: 3`.

## Dateien umwandeln

Ablago liest selbst nur PDF, JPEG und PNG (DMS #577). Ein Paket mit dem Recht `dms:umwandeln` macht aus anderen Dateitypen eine **Fassung**, aus der Ablago Vorschaubild und Volltext erzeugt – z. B. [Bildformate](pakete/bildformate/) für TIFF, WebP, GIF und BMP:

```yaml
dms: ">=0.137.0"
code:
  ereignisse: [datei.umwandeln]
  umwandeln: [image/tiff, image/webp]      # zuständige Dateitypen (MIME); PDF, JPEG und PNG nicht
  rechte:
    lesen: ["*"]
    dokumente: lesen                       # das Original lesen – Schreiben braucht es nicht
    schnittstellen: ["dms:umwandeln"]
```

- **Zurückgeben** darf es nur, was Ablago selbst liest: die Fassung als **PDF, PNG oder JPEG** (`PUT /dokumente/{id}/fassung`, höchstens 50 MB) und auf Wunsch ein Vorschaubild als **JPEG oder PNG**. Mehrseitiges als PDF. Das Original ändert es nie.
- **Kein Netz:** Umwandeln geschieht im Paket. Eine Datei an einen fremden Dienst zu schicken, um sie umzuwandeln, ist nicht erlaubt.
- **Fremde Bibliotheken** (Decoder, Encoder) mit passender Lizenz (siehe [Lizenzen](#lizenzen)), auf feste Commits gebaut, mit ihren Lizenztexten unter `code/lizenzen/` und einem Hinweis im README. Formate, für deren Decoder Patentlizenzen verlangt werden (z. B. HEVC in HEIC), kommen erst nach Rücksprache mit den Pflegern in den Katalog; das README nennt das offen.
- Die Schnittstelle (Ablauf, Ereignis, Formate, Grenzen, Antworten) beschreibt das Entwicklerhandbuch von Ablago unter [Dateien umwandeln](https://help.ablago.app/entwickler/aktuell/pakete-code/#dateien-umwandeln).

### Nur Text aus Dokumenten

Braucht ein Dateityp kein Vorschaubild, sondern nur den Volltext (z. B. [Office und E-Mail](pakete/office_email/) für Word, Excel, E-Mails), nimmt das Paket das Recht `dms:volltext` (DMS #614, ab 0.145.0) – **kein** Schreibrecht auf Dokumente. Ablago meldet ihm jede Datei seiner Typen mit dem Ereignis `datei.volltext` (beim Hochladen, bei neuen Versionen, für den Bestand und bei „Volltext neu erzeugen“); das Paket liest sie und schreibt den Text mit `PUT /dokumente/{id}/volltext` (bis 5 Millionen Zeichen):

```yaml
dms: ">=0.145.0"
code:
  ereignisse: [datei.volltext]
  volltext: [message/rfc822, text/plain]   # zuständige Dateitypen (MIME); PDF, JPEG und PNG nicht
  rechte:
    lesen: ["*"]
    dokumente: lesen                       # die Datei lesen – Schreibrecht braucht es nicht
    schnittstellen: ["dms:volltext"]
```

Dabei gilt:

- **Nichts ausführen:** Makros, Skripte und eingebettete Objekte werden weder gestartet noch ausgewertet; aus Office-Dateien nur die Teile mit dem Text lesen, XML ohne DTD und externe Entitäten, Grenzen gegen ZIP-Bomben.
- **Kein Netz**, wie beim Umwandeln. Der Typ zählt am Inhalt, nicht am Namen; Dateien, die Ablago selbst liest (PDF, JPEG, PNG), lässt das Paket aus.
- **Grund nennen:** Kann das Paket eine Datei nicht lesen, endet es mit Code `0` und einem kurzen Satz als Ergebnis (z. B. „Word lässt sich nicht lesen: mit einem Passwort verschlüsselt“) – den zeigt Ablago am Dokument.
- Ablauf, Ereignis und Grenzen beschreibt das Entwicklerhandbuch von Ablago unter [Volltext liefern](https://help.ablago.app/entwickler/aktuell/pakete-code/#volltext-liefern).

### Archivfassung (PDF/A)

Ein Paket mit dem Recht `dms:archivfassung` (DMS #631, ab 0.149.0) legt zu Dokumenten eine **Archivfassung** ab – ein durchsuchbares PDF/A mit unsichtbarer Textebene genau auf den Wörtern –, z. B. [PDF/A](pakete/pdfa/). Ablago meldet ein Dokument mit dem Ereignis `datei.archivfassung` erst, wenn sein Volltext feststeht; das Paket liest Datei und Wortpositionen und gibt das PDF/A mit `PUT /dokumente/{id}/archivfassung` zurück (höchstens 100 MB):

```yaml
dms: ">=0.149.0"
code:
  ereignisse: [datei.archivfassung]
  archivfassung:
    typen: [application/pdf, image/jpeg, image/png]   # zuständige Dateitypen (MIME); PDF, JPEG und PNG erlaubt
    auswahl:                                          # optional (ab 0.176.0): je Art eine Ja/Nein-Einstellung
      pdf_text: pdf_text                              #   PDFs mit Text
      pdf_scan: pdf_scan                              #   gescannte PDFs
      bilder: bilder                                  #   Fotos und Bilder
  rechte:
    lesen: ["*"]
    dokumente: lesen                                  # Datei und Wortpositionen lesen – Schreiben braucht es nicht
    schnittstellen: ["dms:archivfassung"]
```

- **Nie nachladen:** Die Archivfassung enthält nur, was in der Datei steckt – kein JavaScript, keine Aktionen, keine Verweise auf externe Inhalte; Ablago lehnt sie sonst ab.
- **Genau an den Wörtern:** Die Textebene liegt an den Wortpositionen von Ablago. Fehlen sie (z. B. Scan einer älteren Texterkennung), legt das Paket den Text nicht „ungefähr“ ab, sondern endet mit Code `0` und dem Grund.
- **Wenig einstellen:** eine PDF/A-Stufe fest statt einer Auswahl; jede Einstellung darüber hinaus begründet der Pull Request (Mehrwert gegen Pflege).
- **Werkzeug mit passender Lizenz:** Bibliotheken zum Schreiben des PDF/A brauchen eine Lizenz, die zum Paket passt (z. B. kein AGPL-Werkzeug in einem Paket unter Apache-2.0), mit Lizenztexten unter `code/lizenzen/`. Die Konformität prüft das Paket in seinen Tests (z. B. mit veraPDF), nicht im Paket selbst.
- Ablauf, Ereignis, Wortpositionen und Grenzen beschreibt das Entwicklerhandbuch von Ablago unter [Archivfassung ablegen](https://help.ablago.app/entwickler/aktuell/pakete-code/#archivfassung).

## Signierter Katalog

- Der veröffentlichte Katalog ist signiert (siehe [README, „Katalog signieren“](README.md#katalog-signieren)). Pull Requests ändern daran nichts: Signiert wird nur in der CI auf `main`.
- **Private Schlüssel** (`*.pem`) gehören nie ins Repository, in Issues oder in Pull Requests. Gerät einer doch hinein: sofort dem Maintainer melden (vertraulich, siehe [SECURITY.md](SECURITY.md)).
- `schluessel/*.pub`, `werkzeuge/signieren.py` und der Workflow „Katalog veröffentlichen“ ändert nur der Maintainer (CODEOWNERS).

## Sicherung außer Haus

Ein Paket mit dem Recht `dms:sicherung-lesen` kopiert jede Sicherung von Ablago auf einen externen Speicher und prüft sie dort (DMS #585) – z. B. [Sicherungsziel WebDAV](pakete/sicherung_webdav/):

```yaml
dms: ">=0.142.0"
code:
  ereignisse: [sicherung.fertig]
  rechte:
    schnittstellen: ["dms:sicherung-lesen"]   # keine Mappen, keine Dokumente
  netz: []                                     # Ziel als Einstellung vom Typ adresse
```

- Das Paket bekommt nur die **verschlüsselte** Sicherung aus seinem Ereignis, in Stücken – nie den Schlüssel, nie Inhalte. Es lädt sie **in Teilen** hoch und lädt sie nie ganz in den Speicher.
- **Zugangsdaten** nur als `geheim`; das Ziel als Einstellung vom Typ `adresse`.
- **Löschschutz:** Das Paket listet am Ziel nichts auf und löscht nichts. „Alte Sicherungen extern löschen“ gibt es höchstens als Einstellung mit Vorgabe **aus** und dem Hinweis, dass dafür Löschrechte nötig sind – genau die heben den Schutz gegen Erpressersoftware auf. Das README empfiehlt Zugänge nur mit Schreibrecht (z. B. Nextcloud-Dateiablage, S3 ohne `DeleteObject` mit Object Lock).
- **Ehrlich zurückmelden:** `geprueft` nur, wenn die Prüfsumme bestätigt oder die Datei zurückgelesen ist; sonst `hochgeladen`.
- Ablauf, Ereignis, Lesen in Stücken und Rückmeldung beschreibt das Entwicklerhandbuch von Ablago unter [Sicherung außer Haus](https://help.ablago.app/entwickler/aktuell/pakete-code/#sicherung-ausser-haus).

## Ereignisse zu Mappen

Seit Ablago 0.153.0 (DMS #670) kann ein Paket auf Mappen reagieren – auf `mappe.angelegt`, `mappe.geaendert`, `mappe.geloescht`, `mappe.wiederhergestellt` und `frist.erreicht`. Es bekommt sie nur zu den Mappentypen, die es unter `code.mappentypen` nennt – eigene ohne Präfix, seit Ablago 0.166.0 (DMS #686) auch fremde:

```yaml
dms: ">=0.153.0"
code:
  ereignisse: [mappe.geaendert, frist.erreicht]
  mappentypen: [vertrag]      # eigene Schlüssel, ohne Präfix
  rechte:
    lesen: [vertrag]          # Pflicht: das Paket muss die Typen lesen dürfen
```

- `code.mappentypen` ist Pflicht mit diesen Ereignissen und nur mit ihnen erlaubt.
- **Fremde Mappentypen** (ab `dms: ">=0.166.0"`): Verweise wie in `code.rechte` – `basis:organisation`, `dms:post` – oder `*` für alle, die das Paket lesen darf (nur mit `code.rechte.lesen: ["*"]`). Jeder genannte Typ muss lesbar sein; `dms:benutzer` ist verboten.
- Zugestellt wird nur, was der Paket-Benutzer **gerade lesen darf**: Der Admin kann einem Paket einen Mappentyp verwehren oder einzelne Mappen über Regeln für die Rolle *Paket* ausnehmen. Rechne nicht damit, zu jeder Mappe ein Ereignis zu bekommen.
- Ein Ereignis enthält nur Kennungen, Feldschlüssel und Datum – nie Werte. Das Paket liest mit seinen Rechten nach.
- Ereignisse kommen **mindestens einmal**; `daten.ereignis` ist die Id im Ereigniskatalog – eine Wiederholung erkennt das Paket daran. `mappe.geaendert` fasst schnelle Folgen zusammen.
- Die Vorschau zeigt die Ereignisse mit „– zu: *Typen*“. Ablauf und Felder beschreibt das Entwicklerhandbuch von Ablago unter [Pakete mit Code](https://help.ablago.app/entwickler/aktuell/pakete-code/#ereignisse) und [Ereigniskatalog](https://help.ablago.app/entwickler/aktuell/aufbau/#ereigniskatalog).

## Version zurückziehen

Hat eine veröffentlichte Version einen schweren Fehler, wird sie zurückgezogen. Das ist mehr als eine neue Version mit Korrektur, die meist reicht. Dafür zieht das Ablago-Projekt die Version aus dem Katalog, trägt ihren Tag in `werkzeuge/zurueckgezogen.yaml` ein und **löscht das Release von Hand**. Sonst bleibt die Datei öffentlich ladbar (Registry #156). Releases sind unveränderlich: Den Tag `<id>-v<version>` gibt es danach nie wieder, die Korrektur bekommt eine neue Version.

## Verwaiste Pakete

Antwortet der Pfleger auf Fehler oder nötige Anpassungen drei Monate lang nicht, wird das Paket als *verwaist* markiert und kann von jemand anderem übernommen werden.
