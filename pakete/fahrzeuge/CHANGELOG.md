# Änderungen

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
