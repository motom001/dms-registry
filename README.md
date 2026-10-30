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
werkzeuge/             neues-paket.sh, pruefen.py (läuft auch in der CI)
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

## Ein Paket erstellen

```sh
git clone https://github.com/<du>/dms-registry && cd dms-registry
werkzeuge/neues-paket.sh mein_paket "Mein Paket"
# pakete/mein_paket/ anpassen: manifest.yaml, README.md, inhalt/ …
python3 werkzeuge/pruefen.py pakete/mein_paket
```

Dann einen Pull Request stellen. Wie das im Einzelnen läuft, steht in [CONTRIBUTING.md](CONTRIBUTING.md).

## Grundsätze

- **Alles ist Open Source.** Jedes Paket hier steht unter einer freien Lizenz und wird aus seinem Quellcode gebaut. Fertige Programmdateien nimmt die Registry nicht an.
- **So wenig Rechte wie nötig.** Ein Paket sagt vorher, was es lesen, schreiben und wohin es sich verbinden will. Das DMS zeigt das vor der Installation an.
- **Pakete ergänzen, sie zerstören nichts.** Ein Update fügt hinzu, es löscht keine Felder oder Mappen.
- **Freigabe durch den Maintainer.** Wie im DMS gilt: Erst ein Issue, und umgesetzt bzw. aufgenommen wird, was [@motom001](https://github.com/motom001) freigegeben hat.

## Lizenz

Werkzeuge, Schemas und Vorlage dieses Repositorys stehen unter der [AGPL-3.0](LICENSE). Jedes Paket hat seine eigene Lizenz in seinem Ordner.
