# Änderungen

## 1.0.2

- Im Manifest steht jetzt `ergaenzt: { paket: texterkennung, gruppe: Weitere Sprachen }` (motom001/dms#405): Ab DMS 0.151.0 erscheint die Sprache beim Installieren der Texterkennung als Häkchen unter „Weitere Sprachen?“ – im selben Schritt, auch nachträglich und im Einrichtungsassistenten. Ältere DMS ignorieren das Feld; am Paket ändert sich sonst nichts.

## 1.0.1

- Symbol im Katalog jetzt im Manifest: `symbol: languages` mit `kuerzel: UK` (ISO-639-1-Code der Sprache). Nur Anzeige im Katalog; das DMS liest die Felder nicht, am Paket ändert sich nichts.

## 1.0.0

- Erste Fassung: Ukrainisch (`ukr.traineddata` aus tessdata_fast, derselbe Stand wie im Paket Texterkennung) für das Paket Texterkennung ab 2.0.0.
