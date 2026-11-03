# Regeln für Pakete

**Deutsch** · [English](REGELN.en.md)

> Bei Abweichungen zwischen deutscher und englischer Fassung gilt die deutsche.

## Lizenzen

Jedes Paket steht unter einer dieser Open-Source-Lizenzen (Kennung nach [SPDX](https://spdx.org/licenses/), so in `manifest.yaml` unter `lizenz`):

`MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `MPL-2.0`, `LGPL-3.0-or-later`, `GPL-3.0-or-later`, `AGPL-3.0-or-later`, `CC0-1.0` (nur für reine Konfiguration)

Der vollständige Lizenztext liegt als `LICENSE` im Paketordner. Fremder Code im Paket braucht eine dazu passende Lizenz und einen Hinweis im README.

## Erlaubt

- Mappentypen, Sichten, Rollen, Beispiel-Mappen
- Wortlisten: gleichbedeutende Wörter für die Suche (siehe [Wortlisten](#wortlisten))
- Code, der über die API des DMS arbeitet (sobald der Paket-Läufer verfügbar ist)
- Zugriff auf Netzwerk/Internet nur zu Adressen, die im Manifest stehen (`code.netz`) und deren Zweck das README erklärt. Ohne `code.netz` hat ein Paket keinen Zugriff auf Netzwerk und Internet.

## Verboten

- **Fertige Programmdateien** jeder Art (`.wasm`, `.so`, `.dll`, `.exe`, `.jar`, `.bin` …). Gebaut wird in der CI aus dem Quellcode.
- Verschleierter oder minifizierter Quellcode
- Telemetrie, Tracking, Werbung
- Zugriff auf Netzwerk/Internet zu Adressen, die nicht im Manifest stehen – außer zur Dienst-Adresse, die der Administrator in einer Einstellung vom Typ `adresse` einträgt und bestätigt
- Eine voreingestellte Dienst-Adresse eines fremden Anbieters (Cloud) – auch nicht als `beispiel`
- Mehr Rechte als nötig, z. B. Schreibrecht, wo Lesen reicht
- Echte persönliche Daten in Beispielen, Tests oder Screenshots
- Löschen von Feldern, Registern oder Mappen bei einem Update (ein Textfeld, das ein Verweis mit `aus_text` ablöst, darf aus dem Paket – siehe [Text in Verweis umwandeln](#text-in-verweis-umwandeln))

## So sehen Administratoren die Rechte

Vor der Installation zeigt das DMS die Rechte eines Pakets mit Code, die Katalog-Webseite genauso:

- „Mappen lesen: …“, „Mappen anlegen und ändern: …“, „Dokumente lesen“ bzw. „Dokumente lesen und Volltext schreiben“
- „Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.122.0"`
- „Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die das DMS mitgibt (dms:antworten)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.124.0"`
- „Felder aus Dokumenten vorschlagen („Aus Dokument ausfüllen“) – nur aus dem Text, den das DMS mitgibt (dms:erkennen)“ – nur mit `code.rechte.schnittstellen` und `dms: ">=0.125.0"`
- „Texterkennung für Scans und Bilder übernehmen – das DMS meldet Dokumente ohne Text und zeigt „wartet auf Texterkennung“, bis das Paket den Volltext schreibt (dms:texterkennung)“ – nur mit `code.rechte.schnittstellen`, `dokumente: schreiben` und `dms: ">=0.133.0"`
- „Dateien umwandeln, die das DMS nicht selbst lesen kann – das Paket liest die Originaldatei und liefert eine Fassung (PDF, PNG oder JPEG) für Vorschaubild und Volltext; das Original bleibt unverändert (dms:umwandeln): TIFF, WebP, …“ – nur mit `code.rechte.schnittstellen`, `code.umwandeln`, dem Ereignis `datei.umwandeln`, `dokumente: lesen` und `dms: ">=0.137.0"` (siehe [Dateien umwandeln](#dateien-umwandeln))
- „Volltext für Dateien liefern, die das DMS nicht selbst lesen kann – das Paket liest die Datei und schreibt nur ihren Volltext; Dokumente ändern, ersetzen oder löschen kann es nicht (dms:volltext): Word, E-Mail, …“ – nur mit `code.rechte.schnittstellen`, `code.volltext`, dem Ereignis `datei.volltext`, `dokumente: lesen` und `dms: ">=0.145.0"` (siehe [Nur Text aus Dokumenten](#nur-text-aus-dokumenten))
- „Archivfassung (PDF/A) ablegen – das Paket liest Dokumente mit ihrem Volltext und den Wortpositionen und legt daneben ein durchsuchbares PDF/A ab; das Original bleibt unverändert, ändern, ersetzen oder löschen kann es nichts (dms:archivfassung): PDF, JPEG, PNG, …“ – nur mit `code.rechte.schnittstellen`, `code.archivfassung`, dem Ereignis `datei.archivfassung`, `dokumente: lesen` und `dms: ">=0.149.0"` (siehe [Archivfassung (PDF/A)](#archivfassung-pdfa))
- „Die verschlüsselte Sicherung lesen, um sie außer Haus zu kopieren – kann sie nicht öffnen (kein Schlüssel, keine Inhalte) (dms:sicherung-lesen)“ – nur mit `code.rechte.schnittstellen`, dem Ereignis `sicherung.fertig` und `dms: ">=0.142.0"` (siehe [Sicherung außer Haus](#sicherung-außer-haus))
- „kein Zugriff auf Netzwerk und Internet“ bzw. „Zugriff auf Netzwerk/Internet nur zu: …“; mit einer Dienst-Adresse als Einstellung zusätzlich „der Adresse aus der Einstellung „…“ (trägst du ein und bestätigst sie)“
- „Reagiert auf diese Ereignisse:“ mit einem Ereignis je Zeile

Erklärt sind sie im Administratorhandbuch unter [Pakete mit Code](https://motom001.github.io/dms/admin/aktuell/pakete/#rechte-eines-pakets). Schreibe im README eines Pakets mit Code im Abschnitt „Rechte und Netzwerkzugriff“ (wie in der [Vorlage](vorlage/README.md)) mit denselben Worten, was das Paket darf und wozu.

## Pflicht

- `manifest.yaml`, `README.md`, `LICENSE`, `CHANGELOG.md`, `inhalt/` (ggf. leer), `tests/`
- Paket-Id = Ordnername: Kleinbuchstaben, Ziffern, `_`, beginnt mit einem Buchstaben, höchstens 20 Zeichen
- Bei jeder Änderung eine höhere Version (SemVer) und ein Eintrag im `CHANGELOG.md`
- Deutsche Texte in Feldern und Sichten; das README auf Deutsch, gern zusätzlich auf Englisch
- Ein Pfleger in `CODEOWNERS`

## Einstellungen

- Pakete mit Code **beschreiben** ihre Einstellungen im Manifest (`code.einstellungen`, `code.aktionen`). Das DMS zeigt das Formular, prüft die Werte, speichert sie (Teil der Sicherung) und gibt sie dem Paket.
- **Zugangsdaten nur als `geheim`**, nie als `text` und nie als `standard`. Das DMS verschlüsselt Geheimnisse und zeigt sie nach dem Speichern nicht mehr an.
- **Dienst-Adresse** (ab DMS 0.124.0, `dms: ">=0.124.0"`): Braucht ein Paket einen Dienst, den jeder Haushalt woanders betreibt (z. B. einen KI-Dienst), verlangt es die Adresse als Einstellung vom Typ `adresse` statt einer festen Adresse in `code.netz`. Höchstens eine je Paket, nur in einem Abschnitt, **ohne** `standard` – höchstens ein `beispiel` für einen Dienst im eigenen Netz (z. B. `http://ollama:11434/v1`). Der Administrator bestätigt die Adresse beim Speichern; nur dorthin lässt der Paket-Läufer das Paket ins Netz. Das README erklärt, was wann dorthin geht.
- Einstellungen ändern ist Sache des DMS. Ein Paket speichert seine Einstellungen nicht selbst irgendwo anders und bringt keine eigene Oberfläche dafür mit.

## Kategorien

Jedes Paket gehört zu **einer oder zwei Kategorien** aus einer festen Liste in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml) (Vorlagen für die Ablage, Dateiformate, Texterkennung und Volltext, Sprachen, KI, Suche, Post und Scannen, Sicherung, Für Entwickler). Danach filtert die Katalog-Webseite, und „Ähnliche Pakete“ zeigt Pakete derselben Kategorie. Ein neues Paket nennt sie im Manifest, z. B. `kategorien: [dateiformate, volltext]`; die CI prüft es (`python3 werkzeuge/vorlagen.py --pruefen`). Pakete, deren Manifest das Feld noch nicht hat, stehen übergangsweise unter `pakete:` in `kategorien.yaml` – **das Manifest gewinnt**, und `pruefen.py` weist auf Abweichungen hin. Eine neue Kategorie kommt nur über ein Issue dazu, freie Schlagwörter gibt es nicht. Das DMS liest das Feld nicht; es liest das Manifest Feld für Feld und übergeht Felder, die es nicht kennt – auch ältere DMS-Versionen installieren solche Pakete. Ob ein Paket **nur lokal** läuft, sich mit **einem eingetragenen Dienst** verbindet (Einstellung vom Typ `adresse`) oder **feste Adressen im Internet** nutzt (`code.netz`), liest die Webseite selbst aus dem Manifest – dafür gibt es keine Kategorie.

## Symbol

Im Katalog steht bei jedem Paket ein kleines **Symbol**, damit man auf einen Blick sieht, worum es geht. Du wählst es im Manifest mit `symbol:` aus einer **festen Liste** von [Lucide](https://lucide.dev)-Symbolen – denselben einfarbigen Strichsymbolen wie im DMS. Alle Symbole haben **dieselbe Farbe**; die Farbe zeigt keine Kategorie (dafür gibt es die Kategorie-Chips). Ohne `symbol` zeigt der Katalog den Anfangsbuchstaben, und `pruefen.py` gibt einen Hinweis aus (keinen Fehler). Ein unbekannter Name ist ein Fehler.

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
| `file-text` | Dokumente, Office |
| `files` | mehrere Dokumente, Ähnlichkeit |
| `house` | Haus, Wohnung |
| `image` | Bilder, Bildformate |
| `key-round` | Vermietung, Schlüssel |
| `languages` | Sprachen (mit `kuerzel`) |
| `mail` | Post, E-Mail |
| `message-circle-question-mark` | Fragen, Assistent |
| `scan-barcode` | Trennblätter, Barcodes |
| `scan-text` | Texterkennung |
| `wallet` | Geld, Haushalt |

- **Neues Symbol:** über ein Issue. Dann kommt das SVG unverändert aus `lucide-static` nach `werkzeuge/symbole/<name>.svg` und der Name in `schema/manifest.schema.json` (`symbol`); die CI prüft, dass beides übereinstimmt und das SVG nur einfache Formen enthält. Die Webseite bettet das SVG direkt in die Seite ein, nichts wird aus dem Internet geladen. Lizenz der Symbole: ISC ([`werkzeuge/symbole/LICENSE`](werkzeuge/symbole/LICENSE), NOTICE).
- **Bestehende Pakete:** Ihre Symbole stehen übergangsweise unter `symbole:` in [`werkzeuge/kategorien.yaml`](werkzeuge/kategorien.yaml); mit der nächsten Version wandert das Symbol ins Manifest. Das Manifest gewinnt. Wie `kategorien` liest das DMS `symbol` und `kuerzel` nicht; ältere DMS-Versionen installieren solche Pakete weiter.

## Namen

Schlüssel von Mappentypen, Feldern und Registern sind **im Paket lokal**, z. B. `versicherung`. Das DMS legt sie mit der Paket-Id davor an (`haushalt_versicherung`), damit sich zwei Pakete nicht in die Quere kommen. Angezeigt wird nur der Name („Versicherung“). Verweise auf Typen anderer Pakete schreibst du als `<paket>:<schluessel>`, z. B. `basis:organisation`. Das andere Paket muss dann unter `abhaengigkeiten` stehen. Auf Mappentypen, die das DMS selbst mitbringt, verweist du mit `dms:` – ohne Abhängigkeit: `dms:ablageort` (wo ein Original liegt), `dms:benutzer` und `dms:rolle`. Dafür muss im Manifest `dms: ">=0.75.0"` stehen. Die Paket-Id `dms` ist deshalb vergeben.

Beispiel-Mappen dürfen aufeinander verweisen (ab DMS 0.79.0): Ein Beispiel bekommt einen `schluessel`, ein Verweisfeld eines anderen Beispiels den Wert `{ beispiel: strom }` – oder `{ beispiel: "basis:stadtwerke" }` für ein Beispiel einer Abhängigkeit. Dann muss im Manifest `dms: ">=0.79.0"` stehen.

## Ergänzungen

Ein Paket, das ein anderes erweitert – etwa eine Zusatzsprache die Texterkennung –, sagt das mit `ergaenzt` (motom001/dms#405). Das ergänzte Paket steht auch unter `abhaengigkeiten`:

```yaml
abhaengigkeiten:
  texterkennung: ">=2.0.0"
ergaenzt: { paket: texterkennung, gruppe: Weitere Sprachen }   # oder kurz: ergaenzt: texterkennung
```

Das DMS ab 0.151.0 zeigt Ergänzungen beim Installieren als Häkchen unter dem ergänzten Paket, gruppiert nach `gruppe` (kurze Frage ohne Fragezeichen, höchstens 40 Zeichen; ohne Gruppe: „Ergänzungen“) – auch nachträglich, im Einrichtungsassistenten und in der Sammeldatei. Jede Ergänzung bleibt ein eigenes Paket mit eigener Version. Ältere DMS ignorieren das Feld, deshalb braucht es kein höheres `dms`. Im Katalog steht es je Version als `ergaenzt: { paket, gruppe }`, auf der Katalog-Webseite als eigene Gruppe unter „Passt dazu“.

## Felder für die Erkennung

Das DMS erkennt Post und füllt Mappen aus Dokumenten (DMS #336, #391) – ohne KI, mit Mustern und dem Abgleich mit vorhandenen Mappen. Welche Felder es dafür nutzt, sagt das Paket mit der Feld-Eigenschaft `erkennung`:

```yaml
- key: kundennummer
  label: Kundennummer
  typ: text
  erkennung: { art: nummer, hinweis: "Steht meist oben rechts im Brief" }
- { key: email, label: E-Mail, typ: text, erkennung: {} }   # art ergibt sich aus der Bezeichnung
```

- **Markiere, was ein Schreiben eindeutig zuordnet:** Kunden-, Vertrags-, Versicherungs- oder Aktenzeichen, Kennzeichen, IBAN, Umsatzsteuer-Id, E-Mail-Adresse, Internetseite, Telefon, Name. Hat ein Typ markierte Namen oder Kontaktangaben (`name`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`), gilt er als möglicher **Absender** (Organisation, Person); markiert er nur Nummern, als mögliche **Zielmappe**.
- **Markiere, was „Aus Dokument ausfüllen“ füllen soll:** Datum, Betrag, Anschrift, Vorname/Nachname, Funktion, Verweise (z. B. Werkstatt einer Rechnung). Hat ein Typ markierte Felder, füllt das DMS nur diese.
- **Nicht markieren**, was in fremden Briefen ständig vorkommt und nichts zuordnet – z. B. die IBAN des eigenen Kontos (steht in jeder Lastschrift) oder eine Nummer, die viele Mappen gemeinsam haben.
- Nur bei den Feldarten `text`, `langtext`, `zahl`, `betrag`, `datum`, `auswahl` und `referenz`; nie bei `passwort`. `art` (optional) muss zur Feldart passen: `name`, `vorname`, `nachname`, `funktion`, `nummer`, `iban`, `ustid`, `email`, `internet`, `telefon`, `mobil`, `fax`, `strasse`, `hausnummer`, `plz`, `ort` bei Text; `nummer`, `plz`, `hausnummer`, `betrag` bei Zahl; `datum`, `betrag`, `auswahl`, `verweis` bei der gleichnamigen Feldart. `hinweis` hat höchstens 300 Zeichen; ein Muster nach dem Wort *Muster* (`#` = Ziffer, `A` = Großbuchstabe, z. B. „Muster 100-####“) sucht das DMS gezielt.
- Wer `erkennung` nutzt, schreibt im Manifest `dms: ">=0.113.0"`. Ein Update des Pakets übernimmt die Markierung an installierten Feldern, an denen der Administrator nichts zur Erkennung eingestellt hat; das ist eine Patch-Version (mit neuen Feldern eine Minor-Version).

`werkzeuge/pruefen.py` prüft Feldart, Art und DMS-Version.

## Text in Verweis umwandeln

Steht in einem Paket ein Mensch, eine Firma oder ein anderes Ding als **Text**, wo ein **Verweis** hingehört (z. B. „Halter: Lena Muster“ am Fahrzeug), machst du daraus in einer neuen Version ein Verweisfeld und sagst mit `aus_text`, aus welchem bisherigen Textfeld es sich füllen lässt (DMS #534):

```yaml
- { key: halter_verweis, label: Halter, typ: referenz, ziel: "basis:person", verweisart: bezug, aus_text: halter }
```

- **Neue Kennung:** Das Verweisfeld bekommt eine eigene Kennung – üblich ist die alte mit `_verweis` dahinter. Das alte Textfeld nimmst du aus dem Paket (Feld, Register, Trefferliste, Titel-Vorlage). Neue Installationen bekommen nur noch den Verweis.
- **Nichts geht verloren:** Bei einem Update legt das DMS das Verweisfeld **zusätzlich** an; das alte Textfeld bleibt mit allen Werten. Das gilt nicht als Löschen eines Felds. Erst in der Werkbank (Pakete → Paket → *Text in Verweise umwandeln*) schlägt das DMS je Name eine vorhandene Mappe vor, legt auf Wunsch eine neue an oder überspringt; erst dann wird umgewandelt, mit Eintrag in der Historie und rückgängig zu machen. Updates ändern nichts heimlich.
- **Keine Pflicht:** Ein Verweisfeld mit `aus_text` ist nie `pflicht` – sonst passten vorhandene Mappen nach dem Update nicht mehr.
- **Verweisart:** Für Personen und Organisationen `bezug` – wer eine Person löscht, löscht damit nicht Auto oder Konto.
- **Mehrere Namen:** Steht im Text oft mehr als einer („Lena und Tom Muster“), nimm `mehrfach: true`; das DMS teilt den Text dann an „und“, Komma, Schrägstrich oder „&“.
- Nur bei Verweisfeldern; `aus_text` nennt ein anderes Feld, und steht das noch im Paket, ist es `text` oder `langtext`.
- Wer `aus_text` nutzt, schreibt im Manifest `dms: ">=0.120.0"`. Neue Felder bzw. die Umwandlung sind eine **Minor-Version**.

`werkzeuge/pruefen.py` prüft Feldart, Quelle, Pflicht und DMS-Version.

## Formate und Datumsgrenzen

Das DMS prüft Angaben in Textfeldern nach einem **Format** und Datumsfelder nach **Grenzen** (DMS #535). So landen keine PLZ mit Buchstaben, keine Telefonnummer mit Buchstaben und kein Geburtstag in der Zukunft in den Mappen. Am Handy erscheint die passende Tastatur, Telefon und E-Mail lassen sich antippen.

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
- Gespeicherte Werte bleiben gültig: Das DMS prüft nur neue und geänderte Angaben. Ein Update übernimmt Format und Grenzen an installierten Feldern, an denen der Administrator weder Format noch Grenzen eingestellt hat; das ist eine Minor-Version.
- **Beispiele müssen passen** – das DMS legt sie mit denselben Prüfungen an. Nimm erfundene, aber gültige Werte: Persona-Namen, Testnummern wie `+49 30 123456`, die Test-IBAN `DE89 3704 0044 0532 0130 00`.
- Wer `format`, `landFeld` oder Datumsgrenzen nutzt, schreibt im Manifest `dms: ">=0.121.0"`.

`werkzeuge/pruefen.py` prüft Feldart, Land-Feld, Grenzen, die Beispiele und die DMS-Version.

## Wortlisten

Ein Paket kann **gleichbedeutende Wörter** für die Suche mitbringen (ab DMS 0.127.0): Wer eines sucht, findet auch die anderen. Im Manifest steht `inhalt.wortlisten: inhalt/wortlisten.yaml`, dazu `dms: ">=0.127.0"` – ältere DMS übergehen den Abschnitt stillschweigend. Die Datei ist eine Liste von Gruppen:

```yaml
- woerter: [Kfz, Auto, PKW, Fahrzeug]
- woerter: [Nebenkosten, Betriebskosten]
```

- Je Gruppe 2 bis 20 verschiedene Wörter, je 2 bis 60 Zeichen; Groß-/Kleinschreibung und Umlaute zählen beim Vergleich nicht („Gebühr“ und „gebuhr“ sind dasselbe Wort). Höchstens 1000 Gruppen je Paket.
- Nur Wörter, die im Alltag wirklich dasselbe meinen und zum Thema des Pakets gehören – keine Oberbegriffe („Vertrag“ für alles) und keine Namen von Firmen oder Personen.
- Allgemeine Wörter, die in jeder Ablage vorkommen (Rechnung/Beleg, Vertrag/Vereinbarung), stehen im Paket **Basis**; Fachpakete bringen nur ihre fachlichen Wörter mit. Ein Wort steht in höchstens einem Paket des Katalogs (`werkzeuge/test_pruefen.py` prüft das).
- `tests/erwartung.yaml` nennt die Zahl der Gruppen: `wortlisten: 5`.
- Das DMS legt die Gruppen beim Installieren an, ersetzt sie bei einem Update durch die des Pakets und entfernt sie mit dem Paket.

## Dateien umwandeln

Das DMS liest selbst nur PDF, JPEG und PNG (DMS #577). Ein Paket mit dem Recht `dms:umwandeln` macht aus anderen Dateitypen eine **Fassung**, aus der das DMS Vorschaubild und Volltext erzeugt – z. B. [Bildformate](pakete/bildformate/) für TIFF, WebP, GIF und BMP:

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

- **Zurückgeben** darf es nur, was das DMS selbst liest: die Fassung als **PDF, PNG oder JPEG** (`PUT /dokumente/{id}/fassung`, höchstens 50 MB) und auf Wunsch ein Vorschaubild als **JPEG oder PNG**. Mehrseitiges als PDF. Das Original ändert es nie.
- **Kein Netz:** Umwandeln geschieht im Paket. Eine Datei an einen fremden Dienst zu schicken, um sie umzuwandeln, ist nicht erlaubt.
- **Fremde Bibliotheken** (Decoder, Encoder) mit passender Lizenz (siehe [Lizenzen](#lizenzen)), auf feste Commits gebaut, mit ihren Lizenztexten unter `code/lizenzen/` und einem Hinweis im README. Formate, für deren Decoder Patentlizenzen verlangt werden (z. B. HEVC in HEIC), kommen erst nach Rücksprache mit den Pflegern in den Katalog; das README nennt das offen.
- Die Schnittstelle (Ablauf, Ereignis, Formate, Grenzen, Antworten) beschreibt das Entwicklerhandbuch des DMS unter [Dateien umwandeln](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/#dateien-umwandeln).

### Nur Text aus Dokumenten

Braucht ein Dateityp kein Vorschaubild, sondern nur den Volltext (z. B. [Office und E-Mail](pakete/office_email/) für Word, Excel, E-Mails), nimmt das Paket das Recht `dms:volltext` (DMS #614, ab 0.145.0) – **kein** Schreibrecht auf Dokumente. Das DMS meldet ihm jede Datei seiner Typen mit dem Ereignis `datei.volltext` (beim Hochladen, bei neuen Versionen, für den Bestand und bei „Volltext neu erzeugen“); das Paket liest sie und schreibt den Text mit `PUT /dokumente/{id}/volltext` (bis 5 Millionen Zeichen):

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
- **Kein Netz**, wie beim Umwandeln. Der Typ zählt am Inhalt, nicht am Namen; Dateien, die das DMS selbst liest (PDF, JPEG, PNG), lässt das Paket aus.
- **Grund nennen:** Kann das Paket eine Datei nicht lesen, endet es mit Code `0` und einem kurzen Satz als Ergebnis (z. B. „Word lässt sich nicht lesen: mit einem Passwort verschlüsselt“) – den zeigt das DMS am Dokument.
- Ablauf, Ereignis und Grenzen beschreibt das Entwicklerhandbuch des DMS unter [Volltext liefern](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/#volltext-liefern).

### Archivfassung (PDF/A)

Ein Paket mit dem Recht `dms:archivfassung` (DMS #631, ab 0.149.0) legt zu Dokumenten eine **Archivfassung** ab – ein durchsuchbares PDF/A mit unsichtbarer Textebene genau auf den Wörtern –, z. B. [PDF/A](pakete/pdfa/). Das DMS meldet ein Dokument mit dem Ereignis `datei.archivfassung` erst, wenn sein Volltext feststeht; das Paket liest Datei und Wortpositionen und gibt das PDF/A mit `PUT /dokumente/{id}/archivfassung` zurück (höchstens 100 MB):

```yaml
dms: ">=0.149.0"
code:
  ereignisse: [datei.archivfassung]
  archivfassung:
    typen: [application/pdf, image/jpeg, image/png]   # zuständige Dateitypen (MIME); PDF, JPEG und PNG erlaubt
    nur_scans: nur_scans                              # optional: Ja/Nein-Einstellung „nur Scans und Bilder“
  rechte:
    lesen: ["*"]
    dokumente: lesen                                  # Datei und Wortpositionen lesen – Schreiben braucht es nicht
    schnittstellen: ["dms:archivfassung"]
```

- **Nie nachladen:** Die Archivfassung enthält nur, was in der Datei steckt – kein JavaScript, keine Aktionen, keine Verweise auf externe Inhalte; das DMS lehnt sie sonst ab.
- **Genau an den Wörtern:** Die Textebene liegt an den Wortpositionen des DMS. Fehlen sie (z. B. Scan einer älteren Texterkennung), legt das Paket den Text nicht „ungefähr“ ab, sondern endet mit Code `0` und dem Grund.
- **Wenig einstellen:** eine PDF/A-Stufe fest statt einer Auswahl; jede Einstellung darüber hinaus begründet der Pull Request (Mehrwert gegen Pflege).
- **Werkzeug mit passender Lizenz:** Bibliotheken zum Schreiben des PDF/A brauchen eine Lizenz, die zum Paket passt (z. B. kein AGPL-Werkzeug in einem Paket unter Apache-2.0), mit Lizenztexten unter `code/lizenzen/`. Die Konformität prüft das Paket in seinen Tests (z. B. mit veraPDF), nicht im Paket selbst.
- Ablauf, Ereignis, Wortpositionen und Grenzen beschreibt das Entwicklerhandbuch des DMS unter [Archivfassung ablegen](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/#archivfassung).

## Signierter Katalog

- Der veröffentlichte Katalog ist signiert (siehe [README, „Katalog signieren“](README.md#katalog-signieren)). Pull Requests ändern daran nichts: Signiert wird nur in der CI auf `main`.
- **Private Schlüssel** (`*.pem`) gehören nie ins Repository, in Issues oder in Pull Requests. Gerät einer doch hinein: sofort dem Maintainer melden (vertraulich, siehe [SECURITY.md](SECURITY.md)).
- `schluessel/*.pub`, `werkzeuge/signieren.py` und der Workflow „Katalog veröffentlichen“ ändert nur der Maintainer (CODEOWNERS).

## Sicherung außer Haus

Ein Paket mit dem Recht `dms:sicherung-lesen` kopiert jede Sicherung des DMS auf einen externen Speicher und prüft sie dort (DMS #585) – z. B. [Sicherungsziel WebDAV](pakete/sicherung_webdav/):

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
- Ablauf, Ereignis, Lesen in Stücken und Rückmeldung beschreibt das Entwicklerhandbuch des DMS unter [Sicherung außer Haus](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/#sicherung-ausser-haus).

## Verwaiste Pakete

Antwortet der Pfleger auf Fehler oder nötige Anpassungen drei Monate lang nicht, wird das Paket als *verwaist* markiert und kann von jemand anderem übernommen werden.
