# DMS Registry

Die zentrale Ablage für **Pakete** zum [DMS](https://github.com/motom001/dms), dem selbst gehosteten Dokumentenmanagement für Haushalte und Familien.

Ein Paket erweitert das DMS, ohne dass jemand die Werkbank Feld für Feld durchklicken muss:

- **Konfiguration:** Mappentypen mit Feldern, Registern und Trefferlisten, Sichten, Beispiel-Mappen. Beispiele sind ein Basis-Paket mit Organisation und Person oder die Pakete „Haushalt“, „Haus“ und „Fahrzeuge“.
- **Code (geplant):** Ein Paket reagiert auf Ereignisse im DMS, etwa „Dokument hochgeladen“, und arbeitet über die [API](https://motom001.github.io/dms/admin/aktuell/api/) mit eigenen, bei der Installation bestätigten Rechten. Beispiele: ein Bild in PDF/A umwandeln, ein Dokument einordnen. Der Code läuft als WebAssembly abgeschottet im Container des DMS, nie im DMS-Prozess selbst.

Im DMS installierst du Pakete unter **Werkbank → Pakete**. Die Paketverwaltung ist in Arbeit; bis dahin sammelt dieses Repository die Pakete und legt die Regeln fest.

## Aufbau

```
pakete/<paket>/        ein Ordner je Paket, Name = Paket-Id
vorlage/               Vorlage für ein neues Paket – kopieren und loslegen
schema/                JSON-Schemas für manifest.yaml und die Inhalte
werkzeuge/             neues-paket.sh, pruefen.py, katalog.py, webseite.py (laufen auch in der CI)
REGELN.md              was erlaubt ist, was nicht, welche Lizenzen
CONTRIBUTING.md        wie ein Paket hierher kommt
```

Jedes Paket enthält mindestens:

| Datei | Inhalt |
| --- | --- |
| `manifest.yaml` | Id, Name, Version, Lizenz, nötige DMS-Version, Abhängigkeiten, Inhalt, ggf. Code mit Rechten |
| `README.md` | was das Paket kann, für wen, mit Beispiel |
| `LICENSE` | Lizenztext (Open Source, siehe [REGELN.md](REGELN.md)) |
| `CHANGELOG.md` | Änderungen je Version |
| `inhalt/` | Mappentypen, Sichten, Beispiele (YAML) |
| `code/` | nur bei Paketen mit Code: Quellcode, wird in der CI gebaut |
| `tests/` | Erwartungen an das Paket |

## Katalog

Bei jedem Merge auf `main` baut die CI den **Katalog** und legt ihn auf den Branch `gh-pages`:

- **`https://raw.githubusercontent.com/motom001/dms-registry/gh-pages/katalog.json`** – die Standard-Katalogadresse im DMS
- `…/gh-pages/archive/<id>-<version>.zip` – je Paketversion ein Archiv mit genau den Dateien des Paketordners (ohne Ordner davor)

Auf demselben Branch liegt die **Katalog-Webseite** (`werkzeuge/webseite.py`): Pakete ansehen wie im App Store – Übersicht mit Suche und Filter, je Paket eine Seite mit Beschreibung, was angelegt wird, Rechten, Änderungen und älteren Versionen. **„In meinem DMS installieren“** fragt beim ersten Mal nach der Adresse deines DMS (nur im Browser gemerkt, änderbar) und öffnet dort `/werkbank/pakete?installieren=<id>@<version>`; installiert wird erst nach deiner Bestätigung im DMS. Die Webseite sendet nichts an dein DMS.

Mit GitHub Pages (Quelle: Branch `gh-pages`) ist die Webseite unter **`https://motom001.github.io/dms-registry/`** erreichbar, der Katalog dann auch unter `…/katalog.json`.

`katalog.json` (Format: [`schema/katalog.schema.json`](schema/katalog.schema.json)) enthält Format-Version, Erstellungszeit, Quelle und je Paket Id, Name, Beschreibung, Autor, Lizenz, aktuelle Version und **alle Versionen**, neueste zuerst. Je Version stehen darin: nötige DMS-Version, Abhängigkeiten, Inhaltsübersicht (Mappentypen und Sichten mit Namen, Anzahl Beispiele), ob das Paket Code hat, Adresse des Archivs (relativ zu `katalog.json`), **SHA-256** und Größe des Archivs, Zeitpunkt der Veröffentlichung sowie Links auf Quellordner, README und Changelog.

```json
{
  "format": 1, "erstellt": "2026-11-01T10:00:00Z", "quelle": "https://github.com/motom001/dms-registry", "signatur": null,
  "pakete": [{
    "id": "basis", "name": "Basis", "beschreibung": "…", "autor": { "name": "…", "github": "…" }, "lizenz": "CC0-1.0", "aktuell": "1.0.0",
    "versionen": [{
      "version": "1.0.0", "dms": ">=0.63.0", "abhaengigkeiten": {},
      "inhalt": { "mappentypen": [{ "schluessel": "organisation", "name": "Organisation" }], "sichten": [ … ], "beispiele": 2 },
      "code": false, "archiv": "archive/basis-1.0.0.zip", "sha256": "…", "groesse": 4711, "veroeffentlicht": "…",
      "quelle": "…", "readme": "…", "changelog": "…"
    }]
  }]
}
```

Ältere Versionen bleiben im Katalog und als Archiv abrufbar. Ein Archiv mit gleicher Id und Version ändert sich nie: Ändert sich ein Paket ohne neue Version, schlägt die Prüfung im Pull Request fehl. Lokal baust du den Katalog mit `python3 werkzeuge/katalog.py <ordner>`. Das Feld `signatur` ist für eine spätere Signatur des Katalogs vorgesehen und heute `null`.

## Ein Paket erstellen

```sh
git clone https://github.com/<du>/dms-registry && cd dms-registry
werkzeuge/neues-paket.sh mein_paket "Mein Paket"
# pakete/mein_paket/ anpassen: manifest.yaml, README.md, inhalt/ …
python3 werkzeuge/pruefen.py pakete/mein_paket
```

Dann einen Pull Request stellen. Wie das im Einzelnen läuft, steht in [CONTRIBUTING.md](CONTRIBUTING.md).

## Einstellungen von Paketen

Pakete mit Code beschreiben ihre Einstellungen im Manifest unter `code.einstellungen`; das DMS baut daraus ein Formular (**Werkbank → Pakete → *Paket* → Einstellungen**), prüft und speichert die Werte und gibt sie dem Paket. Höchstens zwei Ebenen:

- **Abschnitt:** `abschnitt` (Überschrift), optional `hilfe`, `felder`
- **Liste** gleich aufgebauter Einträge: `liste` (Schlüssel), `name`, `eintrag` (z. B. „Regel“), optional `hilfe`, `sortierbar`, `felder`

Ein **Feld** hat `schluessel`, `name`, `typ` und optional `hilfe`, `pflicht`, `standard`, `optionen` (Auswahl), `min`/`max` (Zahl), `mappentyp` (beim Typ `feld`). Typen: `text`, `mehrzeilig`, `zahl`, `janein`, `datum`, `auswahl`, `mehrfachauswahl`, `geheim` und die Verweise `mappentyp`, `feld`, `benutzer`, `rolle`, `sicht` (gespeichert wird die stabile Id, ausgewählt aus Listen). **`code.aktionen`** (`schluessel`, `name`, optional `hilfe`, `bestaetigen`) werden zu Knöpfen im Formular. Ein Beispiel steht auskommentiert in [`vorlage/manifest.yaml`](vorlage/manifest.yaml).

`werkzeuge/pruefen.py` prüft zusätzlich: Schlüssel eindeutig je Ebene bzw. Liste, `standard` passt zum Typ, Auswahl hat `optionen`, `geheim` und Verweise haben keine Vorgabe, Verweise auf Mappentypen anderer Pakete nur als `<paket>:<schluessel>` und nur auf Abhängigkeiten; auf Mappentypen des DMS nur `dms:ablageort`, `dms:benutzer` oder `dms:rolle`.

## Grundsätze

- **Alles ist Open Source.** Jedes Paket hier steht unter einer freien Lizenz und wird aus seinem Quellcode gebaut. Fertige Programmdateien nimmt die Registry nicht an.
- **So wenig Rechte wie nötig.** Ein Paket sagt vorher, was es lesen, schreiben und wohin es sich verbinden will. Das DMS zeigt das vor der Installation an.
- **Pakete ergänzen, sie zerstören nichts.** Ein Update fügt hinzu, es löscht keine Felder oder Mappen.
- **Freigabe durch den Maintainer.** Wie im DMS gilt: Erst ein Issue, und umgesetzt bzw. aufgenommen wird, was [@motom001](https://github.com/motom001) freigegeben hat.

## Lizenz

Werkzeuge, Schemas und Vorlage dieses Repositorys stehen unter der [AGPL-3.0](LICENSE). Jedes Paket hat seine eigene Lizenz in seinem Ordner.
