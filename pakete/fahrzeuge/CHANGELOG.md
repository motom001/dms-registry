# Änderungen

## 1.3.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.3.0

- Neu: **gleichbedeutende Wörter** für die Suche – wer „Kfz“ sucht, findet auch „Auto“ und „PKW“; dazu HU/TÜV, Fahrzeugbrief und Fahrzeugschein mit ihren amtlichen Namen, Werkstatt- und Reparaturrechnung.
- Braucht DMS ab 0.127.0 (Wortlisten).

## 1.2.0

- **Grenzen** (dms-registry #55, DMS #535): Die **Erstzulassung** darf nicht in der Zukunft liegen. „HU fällig“ bleibt ohne Grenze.
- Braucht DMS ab 0.121.0. Gespeicherte Angaben bleiben gültig; das Update übernimmt die Grenze nur, wenn du am Feld nichts davon eingestellt hast.

## 1.1.0

- **Halter als Verweis auf eine Person** (dms-registry #52, DMS #534): Am Fahrzeug ist der **Halter** jetzt ein Verweis auf eine **Person** aus dem Paket Basis (Verweisart Bezug: Wer eine Person löscht, löscht damit nicht das Auto). An der Person siehst du unter *Verknüpfungen* ihre Fahrzeuge.
  - **Update:** Das bisherige Textfeld *Halter* bleibt mit allen Werten; das Verweisfeld kommt dazu. Unter **Werkbank → Pakete → Fahrzeuge → Text in Verweise umwandeln** schlägt das DMS je Name eine vorhandene Person vor oder legt eine neue an – erst nach deiner Vorschau, rückgängig zu machen. Updates ändern nichts heimlich.
  - Das Beispiel-Familienauto verweist auf Tom Muster aus den Beispielen von Haushalt.
- Braucht DMS ab 0.120.0, Basis ab 1.1.0 (Person) und Haushalt ab 1.1.0.

## 1.0.3

- **Erkennung** (dms-registry #49, DMS #336/#391): **Kennzeichen** und **Fahrzeug-Identnummer** sind „für die Erkennung“ markiert – Post mit einer davon (Kfz-Steuer, Versicherung, Werkstatt) gehört zu diesem Fahrzeug. Bei der Werkstattrechnung füllt „Aus Dokument ausfüllen“ Werkstatt, Datum und Betrag.
- Behoben: Der Hilfetext der Fahrzeug-Identnummer war nach „ohne I“ abgeschnitten (Komma in YAML ohne Anführungszeichen); er gilt für Neuinstallationen.
- Braucht DMS ab 0.113.0. Das Update übernimmt die Markierung nur an Feldern, an denen du nichts zur Erkennung eingestellt hast.

## 1.0.2

- Lizenz: ab dieser Version **Apache-2.0** (vorher MIT), wie alle Pakete von motom001. Inhalt unverändert.

## 1.0.1

- Beispiele zeigen jetzt aufeinander: Werkstattrechnungen → Familienauto, Familienauto → Kfz-Versicherung aus Haushalt.
- Braucht DMS ab 0.79.0 (Verweise zwischen Beispielen).

## 1.0.0

- Erste Fassung.
