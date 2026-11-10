# Änderungen

## 1.1.0

- **Neue Id `texterkennung.pol`** (bisher `texterkennung_pol`, dms-registry #173, motom001/dms#1084): Der Punkt heißt „ergänzt die Texterkennung“. Ablago ab 0.229.0 nimmt das als gewöhnliches Update – die Vorschau sagt „Das Paket heißt jetzt …“, danach steht dieselbe Installation unter der neuen Id da. Braucht **Ablago 0.229.0** und **Texterkennung 2.5.0** (liest die Sprachdaten unter beiden Namen). Ältere Ablago-Versionen behalten 1.0.3 unter der alten Id.
- Herausgeber `app.ablago` im Manifest. Die Sprachdaten sind unverändert.

## 1.0.3

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.0.2

- Im Manifest steht jetzt `ergaenzt: { paket: texterkennung, gruppe: Weitere Sprachen }` (motom001/dms#405): Ab DMS 0.151.0 erscheint die Sprache beim Installieren der Texterkennung als Häkchen unter „Weitere Sprachen?“ – im selben Schritt, auch nachträglich und im Einrichtungsassistenten. Ältere DMS ignorieren das Feld; am Paket ändert sich sonst nichts.

## 1.0.1

- Symbol im Katalog jetzt im Manifest: `symbol: languages` mit `kuerzel: PL` (ISO-639-1-Code der Sprache). Nur Anzeige im Katalog; das DMS liest die Felder nicht, am Paket ändert sich nichts.

## 1.0.0

- Erste Fassung: Polnisch (`pol.traineddata` aus tessdata_fast, derselbe Stand wie im Paket Texterkennung) für das Paket Texterkennung ab 2.0.0.
