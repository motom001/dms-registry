# Ablago – Paketkatalog

**Deutsch** · [English](README.en.md)

Die zentrale Ablage für **Pakete** für [Ablago](https://ablago.app) – Dokumentenablage für zu Hause und kleine Betriebe.

Ein Paket erweitert Ablago, ohne dass jemand die Werkbank Feld für Feld durchklicken muss:

- **Konfiguration:** Mappentypen mit Feldern, Registern und Trefferlisten, Sichten, Beispiel-Mappen. Beispiele sind ein Basis-Paket mit Organisation und Person oder die Pakete „Haushalt“, „Haus“ und „Fahrzeuge“.
- **Code (ab Ablago 0.88.0):** Ein Paket reagiert auf Ereignisse in Ablago, etwa „Dokument hochgeladen“, und arbeitet über die [API](https://help.ablago.app/admin/aktuell/api/) mit eigenen, bei der Installation bestätigten Rechten. Beispiele: [Texterkennung](pakete/texterkennung/) (Tesseract als WebAssembly), [KI lokal – Ähnlichkeit](pakete/ki_aehnlich/) (kleines Embedding-Modell, ohne Netz), [KI-Assistent](pakete/ki_assistent/) („Frag deine Ablage“ über einen eigenen KI-Dienst wie Ollama), [Bildformate](pakete/bildformate/) (Vorschau und Volltext für TIFF, WebP, GIF und BMP), [Office und E-Mail](pakete/office_email/) (Volltext für Word, Excel, PowerPoint, OpenDocument und E-Mails), [Sicherungsziel WebDAV](pakete/sicherung_webdav/) (jede Sicherung außer Haus auf Nextcloud, NAS oder zum Hoster, dort geprüft) und das kleine [Hallo Post](pakete/hallo_post/). Der Code läuft als WebAssembly abgeschottet im Paket-Läufer von Ablago, nie im Ablago-Prozess selbst; die CI baut ihn aus dem Quellcode (`code/bauen.sh`, [`werkzeuge/bauen.py`](werkzeuge/bauen.py)).

In Ablago installierst du Pakete unter **Werkbank → Pakete**. Die Paketverwaltung ist in Arbeit; bis dahin sammelt dieses Repository die Pakete und legt die Regeln fest.

## Aufbau

```
pakete/<paket>/        ein Ordner je Paket, Name = Paket-Id
gemeinsam/<ordner>/    Quellcode, den mehrere Pakete beim Bau einbinden (z. B. mail/: E-Mails zerlegen für Office und E-Mail und PDF/A)
vorlage/               Vorlage für ein neues Paket – kopieren und loslegen
schema/                JSON-Schemas für manifest.yaml und die Inhalte
werkzeuge/             neues-paket.sh, pruefen.py, katalog.py, signieren.py, webseite.py, sammeldatei.py, sprachen.py (laufen auch in der CI)
werkzeuge/symbole/     erlaubte Symbole für den Katalog (Lucide, ISC) – siehe REGELN.md, „Symbol“
schluessel/            öffentliche Schlüssel, mit denen der Katalog signiert ist (siehe „Katalog signieren“)
REGELN.md              was erlaubt ist, was nicht, welche Lizenzen
CONTRIBUTING.md        wie ein Paket hierher kommt
*.en.md                englische Fassungen von README, REGELN, CONTRIBUTING, SECURITY
```

Jedes Paket enthält mindestens:

| Datei | Inhalt |
| --- | --- |
| `manifest.yaml` | Id, Name, Version, Lizenz, nötige Ablago-Version, Abhängigkeiten, Inhalt, ggf. Code mit Rechten; für den Katalog `kategorien` und `symbol` ([REGELN.md](REGELN.md#symbol)) |
| `README.md` | was das Paket kann, für wen, mit Beispiel |
| `LICENSE` | Lizenztext (Open Source, siehe [REGELN.md](REGELN.md)) |
| `CHANGELOG.md` | Änderungen je Version |
| `inhalt/` | Mappentypen, Sichten, Beispiele (YAML), optional Beispiel-Dokumente unter `inhalt/beispiele/` – nur erfundene Inhalte ([REGELN.md](REGELN.md#beispiel-dokumente)) |
| `code/` | nur bei Paketen mit Code: Quellcode, wird in der CI gebaut |
| `tests/` | Erwartungen an das Paket |

## Katalog

Bei jedem Merge auf `main` baut die CI den **Katalog** und legt ihn auf den Branch `gh-pages`:

- **`https://catalog.ablago.app/katalog.json`** – die Standard-Katalogadresse in Ablago
- `https://catalog.ablago.app/archive/<id>-<version>.zip` – je Paketversion ein Archiv mit genau den Dateien des Paketordners (ohne Ordner davor)
- `https://catalog.ablago.app/katalog.sig` – die Signatur des Katalogs (siehe [Katalog signieren](#katalog-signieren))

Auf demselben Branch liegt die **Katalog-Webseite** (`werkzeuge/webseite.py`): Pakete ansehen wie im App Store – Übersicht mit **„Für den Anfang“** (Liste in [`werkzeuge/empfohlen.yaml`](werkzeuge/empfohlen.yaml)), darunter die weiteren Pakete als kleine Kacheln oder Liste, Suche und Filter nach Kategorie, Autor und **Paketart** (aus dem Inhalt abgeleitet, REGELN „Paketarten“; Sprachen und Ergänzungen nur über Suche, Filter und die Seite ihres Hauptpakets, #165), je Paket eine Seite mit Beschreibung, was angelegt wird, Rechten, Änderungen und älteren Versionen. **„In meinem Ablago installieren“** fragt beim ersten Mal nach der Adresse deines Ablago (nur im Browser gemerkt, änderbar) und öffnet dort `/werkbank/pakete?installieren=<id>@<version>`; installiert wird erst nach deiner Bestätigung in Ablago. Die Webseite sendet nichts an dein Ablago. Die Übersicht gibt es deutsch und englisch (`en/index.html`, oben der Umschalter „Deutsch · English“, auch ohne JavaScript); Paketseiten und Paketbeschreibungen bleiben vorerst deutsch.

**Pakete ohne Internet** (`sammeldatei.html`, motom001/dms#461): Pakete ankreuzen, Ablago-Version wählen (Vorgabe: die neueste; der Link aus Ablago bringt sie im Fragment `#dms=<version>` mit – das geht an keinen Server; die Seite merkt sie sich nur im Browser und entfernt das Fragment aus der Adresse), Abhängigkeiten kommen automatisch mit. Der Browser lädt die Archive, prüft jedes gegen SHA-256 und Größe aus `katalog.json` und packt sie mit dem Verzeichnis `sammeldatei.json` (Format: [`schema/sammeldatei.schema.json`](schema/sammeldatei.schema.json)) in **eine Sammeldatei** – dazu den signierten Katalog (`katalog.json` und `katalog.sig`) –, nichts wird hochgeladen. Ablago prüft beim Hochladen jedes Archiv gegen Größe und Prüfsumme im Verzeichnis und gegen den signierten Katalog (und gegen den offiziellen Katalog, wenn es ihn schon abgerufen hat), lehnt fremde Dateien ab und installiert dann Paket für Paket. Ist die Signatur gültig, muss niemand mehr die Herkunft bestätigen. `werkzeuge/sammeldatei.py` erzeugt dieselbe Datei auf der Kommandozeile und prüft eine Sammeldatei wie Ablago (`--pruefen <datei> [--katalog katalog.json] [--oeffentlich <x.pub> …]`).

Mit GitHub Pages (Quelle: Branch `gh-pages`) ist die Webseite unter **`https://catalog.ablago.app/`** erreichbar, der Katalog dann auch unter `…/katalog.json`.

`katalog.json` (Format: [`schema/katalog.schema.json`](schema/katalog.schema.json)) enthält Format-Version, Erstellungszeit, Quelle und je Paket Id, Name, Beschreibung, Autor, Lizenz, aktuelle Version und **alle Versionen**, neueste zuerst. Je Version stehen darin: nötige Ablago-Version, Abhängigkeiten, Inhaltsübersicht (Mappentypen und Sichten mit Namen, Anzahl Beispiele und – falls vorhanden – `beispieldokumente`, die Anzahl der Beispiel-Dokumente), ob das Paket Code hat, Adresse des Archivs (`archiv`, die Release-Datei, #156), die Kopie auf GitHub Pages (`spiegel`, relativ zu `katalog.json`), **SHA-256** und Größe des Archivs, die Downloads laut GitHub (`downloads`, auch als Summe je Paket), Zeitpunkt der Veröffentlichung sowie Links auf Quellordner, README und Changelog.

```json
{
  "format": 1, "erstellt": "2026-11-01T10:00:00Z", "quelle": "https://github.com/motom001/dms-registry", "signatur": null,
  "pakete": [{
    "id": "basis", "name": "Basis", "beschreibung": "…", "autor": { "name": "…", "github": "…" }, "lizenz": "CC0-1.0", "aktuell": "1.0.0",
    "versionen": [{
      "version": "1.0.0", "dms": ">=0.63.0", "abhaengigkeiten": {},
      "inhalt": { "mappentypen": [{ "schluessel": "organisation", "name": "Organisation" }], "sichten": [ … ], "beispiele": 2 },
      "code": false, "archiv": "https://github.com/motom001/dms-registry/releases/download/basis-v1.0.0/basis-1.0.0.zip",
      "spiegel": "archive/basis-1.0.0.zip", "sha256": "…", "groesse": 4711, "downloads": 42, "veroeffentlicht": "…",
      "quelle": "…", "readme": "…", "changelog": "…"
    }]
  }]
}
```

**Releases und Downloads (#156):** Jede Paketversion liegt als Datei an einem GitHub-Release (Tag `<id>-v<version>`, Datei `<id>-<version>.zip`, Byte für Byte das Archiv aus dem Katalog). Im Repository ist **„Immutable releases“** eingeschaltet: `releases.py anlegen` legt erst einen Entwurf an, lädt die Datei hoch, prüft sie und veröffentlicht dann; danach ändert niemand mehr Datei oder Tag. Je Lauf entstehen höchstens 20 neue Releases (`RELEASES_HOECHSTENS`); bis eine Version ihr Release hat, zeigt der Katalog auf ihr Archiv auf Pages. Zurückziehen: REGELN, „Version zurückziehen“. Dorthin zeigt `archiv`; Ablago lädt von dort und folgt dabei der Weiterleitung von GitHub. GitHub zählt die Downloads selbst – **Ablago sendet dafür nichts**. Der Workflow legt fehlende Releases an (`werkzeuge/releases.py anlegen`) und schreibt einmal am Tag die Zahlen in den Katalog (`… zaehlen`, vor dem Signieren). Die Zahl sind **Downloads, nicht Installationen**: Updates und unsere eigenen Tests zählen mit. Die Webseite zeigt sie gerundet („über 100“), unter 10 gar nicht, und sortiert nicht danach.

**Spiegel auf GitHub Pages:** Release-Dateien lassen sich aus dem Browser nicht abrufen (kein CORS). Die Sammeldatei auf der Webseite nimmt deshalb die Kopie unter `archive/` (`spiegel`). Dort liegt **nur die aktuelle Version** je Paket (#133, `releases.py ausduennen`); ältere Versionen bleiben im Katalog und am Release und lassen sich einzeln herunterladen und installieren. Der Lauf meldet die Größe der Seite und bricht ab 900 MB ab (`releases.py groesse`), `gh-pages` wird ohne Historie veröffentlicht. Git nimmt dort keine Datei über 100 MB an, deshalb Pakete deutlich darunter halten. Ein Archiv mit gleicher Id und Version ändert sich nie: Ändert sich ein Paket ohne neue Version, schlägt die Prüfung im Pull Request fehl. Lokal baust du den Katalog mit `python3 werkzeuge/katalog.py <ordner>`. Das Feld `signatur` bleibt `null`: Die Signatur steht getrennt in `katalog.sig`.

## Katalog signieren

Die CI **signiert** jeden veröffentlichten Katalog (#74, in Ablago: motom001/dms#594). Weil `katalog.json` die Prüfsumme jedes Archivs enthält, belegt **eine** Signatur, dass alle Pakete vom Ablago-Projekt stammen – auch offline in einer Sammeldatei.

- **Verfahren:** Ed25519 über die **exakten Bytes** von `katalog.json`, mit `openssl pkeyutl` (`werkzeuge/signieren.py`).
- **`katalog.sig`** liegt neben `katalog.json` (getrennt, damit ältere Ablago-Versionen den Katalog unverändert lesen):

    ```json
    { "format": 1, "verfahren": "ed25519", "schluessel": "<Kennung>", "signatur": "<Base64>", "erstellt": "2026-11-02T10:00:00Z" }
    ```

- **`erstellt`** steht in `katalog.json` (Zeitpunkt des Baus). Ablago lehnt online signierte Kataloge ab, die älter sind als der zuletzt gesehene.
- **Kennung und Fingerabdruck:** SHA-256 über die 32 Bytes des öffentlichen Schlüssels, hexadezimal – Kennung = die ersten 16 Zeichen, Fingerabdruck = alle 64 in Vierergruppen (`python3 werkzeuge/signieren.py fingerabdruck <datei.pub>`).
- **Zwei Schlüssel:** Der **Signierschlüssel** liegt nur als Secret `KATALOG_SIGNIERSCHLUESSEL` in der Environment `katalog` (nur Branch `main`). Der **Reserveschlüssel** liegt offline beim Maintainer. Beide öffentlichen Schlüssel stehen fest in Ablago und als `schluessel/signier.pub` und `schluessel/reserve.pub` hier; nach jedem Signieren prüft die CI die Signatur damit.
- **Ohne Secret** (in Forks, oder solange es noch nicht angelegt ist) läuft der Bau weiter, aber **ohne** Signatur – mit deutlicher Warnung im Lauf. Eine alte `katalog.sig` wird dann entfernt, weil sie nicht mehr passen würde.
- **Sammeldateien** enthalten den signierten Katalog (`katalog.json` und `katalog.sig`, Byte für Byte). Ablago fragt dann nicht mehr nach der Herkunft. `python3 werkzeuge/sammeldatei.py --pruefen <datei> --oeffentlich schluessel/signier.pub --oeffentlich schluessel/reserve.pub` prüft die Signatur auch hier.

**Fingerabdrücke** (SHA-256 über die 32 Bytes des öffentlichen Schlüssels, wie Ablago und `werkzeuge/signieren.py` sie anzeigen; gleich in der [SECURITY.md von Ablago](https://github.com/motom001/dms/blob/main/SECURITY.md)):

| Schlüssel | Kennung | Fingerabdruck |
| --- | --- | --- |
| Signierschlüssel | `6d868387314e64df` | `6d86 8387 314e 64df 715c a3bd 9856 58d5 f888 c0ea 7cab ac91 a43f 9b99 6052 e728` |
| Reserveschlüssel | `4543c81b5ccf522d` | `4543 c81b 5ccf 522d f5a3 5e76 6660 8774 5f6c ae42 4722 3b6d 91c9 63cc 34b0 3954` |

Ablago kennt diese Schlüssel ab Version 0.144.2; ältere Versionen (0.141.0–0.144.1) prüfen noch mit Testschlüsseln und melden „Signatur ungültig“, sobald der Katalog signiert ist.

### Was nur der Maintainer tun kann (einmalig)

Auf dem **eigenen Rechner** – nicht in einer Chat-Sitzung, nicht in der CI:

```sh
openssl genpkey -algorithm ed25519 -out signier.pem
openssl pkey -in signier.pem -pubout -out signier.pub
openssl genpkey -algorithm ed25519 -out reserve.pem
openssl pkey -in reserve.pem -pubout -out reserve.pub
python3 werkzeuge/signieren.py fingerabdruck signier.pub reserve.pub
```

1. In dms-registry unter **Settings → Environments → New environment** die Environment `katalog` anlegen (die CI legt sie beim ersten Lauf auch selbst an, dann nur noch einstellen). Bei **Deployment branches and tags** „Selected branches and tags“ wählen und nur `main` erlauben.
2. In dieser Environment unter **Environment secrets → Add secret** das Secret `KATALOG_SIGNIERSCHLUESSEL` anlegen. Inhalt: die **komplette** Datei `signier.pem` (mit den Zeilen `-----BEGIN PRIVATE KEY-----` und `-----END PRIVATE KEY-----`).
3. `reserve.pem` **offline** aufbewahren (sicherer Ort, zusätzlich ein Ausdruck) – **nie** in GitHub.
4. `signier.pub` und `reserve.pub` als Kommentar in #74 posten (öffentliche Schlüssel sind unkritisch). Sie kommen dann nach `schluessel/` hier und in `server/src/projektschluessel.ts` von Ablago; die Fingerabdrücke in diese README und in die SECURITY.md von Ablago.
5. Danach `signier.pem` und `reserve.pem` vom Rechner löschen. Die Reserve bleibt nur am Aufbewahrungsort.

Der nächste Lauf von „Katalog veröffentlichen“ (Push auf `main` oder **Actions → Katalog veröffentlichen → Run workflow**) signiert dann. Passt der Schlüssel im Secret nicht zu `schluessel/*.pub`, schlägt der Lauf fehl – nichts wird mit einem falschen Schlüssel veröffentlicht.

**Schlüssel verloren oder bekannt geworden?** Den Reserveschlüssel als neues Secret eintragen; Ablago nimmt ihn ohne Update an. Danach ein neues Reservepaar erzeugen und mit einem Ablago-Release verteilen.

### Eigener Katalog mit eigenem Schlüssel

Wer einen eigenen Katalog betreibt, kann ihn mit `werkzeuge/signieren.py` ebenso signieren und legt seinen öffentlichen Schlüssel als `katalog.schluessel` daneben. Ablago zeigt beim Hinzufügen den Fingerabdruck und übernimmt ihn erst nach Bestätigung (wie SSH beim ersten Kontakt). Einen Schlüsselwechsel kündigt `katalog.schluessel.sig` an (der neue Schlüssel, signiert mit dem alten: `signieren.py signieren-datei`). Anleitung: [Entwicklerhandbuch von Ablago](https://help.ablago.app/entwickler/aktuell/pakete/#eigener-katalog-mit-eigenem-schluessel).

## Ein Paket erstellen

```sh
git clone https://github.com/<du>/dms-registry && cd dms-registry
werkzeuge/neues-paket.sh mein_paket "Mein Paket"
# pakete/mein_paket/ anpassen: manifest.yaml, README.md, inhalt/ …
python3 werkzeuge/pruefen.py pakete/mein_paket
```

Dann einen Pull Request stellen. Wie das im Einzelnen läuft, steht in [CONTRIBUTING.md](CONTRIBUTING.md).

## Einstellungen von Paketen

Pakete mit Code beschreiben ihre Einstellungen im Manifest unter `code.einstellungen`; Ablago baut daraus ein Formular (**Werkbank → Pakete → *Paket* → Einstellungen**), prüft und speichert die Werte und gibt sie dem Paket. Höchstens zwei Ebenen:

- **Abschnitt:** `abschnitt` (Überschrift), optional `hilfe`, `felder`
- **Liste** gleich aufgebauter Einträge: `liste` (Schlüssel), `name`, `eintrag` (z. B. „Regel“), optional `hilfe`, `sortierbar`, `felder`

Ein **Feld** hat `schluessel`, `name`, `typ` und optional `hilfe`, `pflicht`, `standard`, `optionen` (Auswahl), `min`/`max` (Zahl), `mappentyp` (beim Typ `feld`). Typen: `text`, `mehrzeilig`, `zahl`, `janein`, `datum`, `auswahl`, `mehrfachauswahl`, `geheim` und die Verweise `mappentyp`, `feld`, `benutzer`, `rolle`, `sicht` (gespeichert wird die stabile Id, ausgewählt aus Listen). **`code.aktionen`** (`schluessel`, `name`, optional `hilfe`, `bestaetigen`) werden zu Knöpfen im Formular. Ein Beispiel steht auskommentiert in [`vorlage/manifest.yaml`](vorlage/manifest.yaml).

`werkzeuge/pruefen.py` prüft zusätzlich: Schlüssel eindeutig je Ebene bzw. Liste, `standard` passt zum Typ, Auswahl hat `optionen`, `geheim` und Verweise haben keine Vorgabe, Verweise auf Mappentypen anderer Pakete nur als `<paket>:<schluessel>` und nur auf Abhängigkeiten; auf Mappentypen von Ablago nur `dms:benutzer` oder `dms:rolle` (`dms:ablageort` gibt eine Warnung: veraltet, bitte `basis:ablageort`).

## Grundsätze

- **Alles ist Open Source.** Jedes Paket hier steht unter einer freien Lizenz und wird aus seinem Quellcode gebaut. Fertige Programmdateien nimmt die Registry nicht an.
- **So wenig Rechte wie nötig.** Ein Paket sagt vorher, was es lesen, schreiben und wohin es sich verbinden will. Ablago zeigt das vor der Installation an.
- **Pakete ergänzen, sie zerstören nichts.** Ein Update fügt hinzu, es löscht keine Felder oder Mappen.
- **Freigabe durch den Maintainer.** Wie in Ablago gilt: Erst ein Issue, und umgesetzt bzw. aufgenommen wird, was [@motom001](https://github.com/motom001) freigegeben hat. In welcher Reihenfolge, steht im [Fahrplan](ROADMAP.md).

## Lizenz

Werkzeuge, Schemas, Webseite und Vorlage dieses Repositorys stehen unter der [Apache-2.0](LICENSE), Hinweise in [NOTICE](NOTICE) (bis 01.11.2026: AGPL-3.0). Die Symbole in `werkzeuge/symbole/` stammen aus [Lucide](https://lucide.dev) und stehen unter der ISC-Lizenz ([`werkzeuge/symbole/LICENSE`](werkzeuge/symbole/LICENSE)). **Jedes Paket hat seine eigene Lizenz** in seinem Ordner – erlaubt sind die Lizenzen aus [REGELN.md](REGELN.md). Die Pakete, die wir selbst (motom001) veröffentlichen, stehen unter **Apache-2.0**.

Was unter Apache-2.0 steht, darf jeder nutzen, verändern und weitergeben – auch in eigenen Produkten. Wer es weitergibt, legt die Lizenz und die Hinweise aus NOTICE bei und kennzeichnet geänderte Dateien. Den Quellcode einer veränderten Fassung offenzulegen ist nicht Pflicht.

## Sprachen

README, [REGELN](REGELN.md), [CONTRIBUTING](CONTRIBUTING.md) und [SECURITY](SECURITY.md) gibt es auch auf Englisch ([README.en.md](README.en.md), [REGELN.en.md](REGELN.en.md), [CONTRIBUTING.en.md](CONTRIBUTING.en.md), [SECURITY.en.md](SECURITY.en.md)). **Bei Abweichungen gilt die deutsche Fassung.** Issues und Pull Requests sind auf Deutsch oder Englisch willkommen. Die Meldungen von `pruefen.py` und die Paketinhalte bleiben vorerst deutsch.
