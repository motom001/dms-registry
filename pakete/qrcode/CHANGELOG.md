# Änderungen

## 1.0.2

- Kurzbeschreibung in Alltagssprache, ohne Fachwörter (dms-registry #80).

## 1.0.1

- Kurzanleitung „So nutzt du es“ im Katalog und nach der Installation in Ablago (dms-registry #198, motom001/dms#1047).
- Manifest: Herausgeber `app.ablago`.

## 1.0.0

- Erste Fassung (dms-registry #53): Liest QR-Codes auf Fotos und Scans und übersetzt eine **Visitenkarte (vCard 2.1, 3.0, 4.0)** in Vorschläge für „Aus Dokument ausfüllen“ (Schnittstelle `dms:erkennen`, DMS #511): Vorname, Nachname, Name der Firma, Funktion, E-Mail, Telefon, Mobil, Fax, Internetseite, Straße, Hausnummer, PLZ, Ort.
- Andere QR-Inhalte (Internetadresse, GiroCode, Text) wertet das Paket nicht aus; es meldet nur, was es gefunden hat, und Ablago liest den Text wie gewohnt. Fotos in der vCard übernimmt es nie.
- QR-Leser: quirc 1.2 (ISC-Lizenz) aus den Quellen, mit bis zu 65 534 Regionen für Fotos mit viel Text und große QR-Codes.
