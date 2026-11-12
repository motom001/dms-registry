# Änderungen

## 1.1.0

- Leere Rückseite eines Trennblatts: dieselbe Erkennung wie das neue Paket **Leerseiten** (`gemeinsam/leerseite/`, dms #997), Stufe „vorsichtig“. Lochung, Staub und Schatten am Rand zählen nicht, eine Bleistiftnotiz, ein Stempel oder durchscheinende Schrift schon – solche Rückseiten bleiben jetzt im Brief, statt wegzufallen. Die Einstellung „Leere Rückseite mit entfernen“ bleibt (keine Doppelung: *Leerseiten* sieht nach dem Teilen nur noch die Seiten der Briefe).
- Manifest: Herausgeber `app.ablago`, Kategorie, Symbol und Kurzanleitung stehen jetzt im Manifest. Rechte und Ablago-Version unverändert.

## 1.0.2

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.0.1

- Rechte: nur noch **Post** lesen, anlegen und ändern (`dms:post`) statt aller Mappentypen (`"*"`). Andere Mappen sieht das Paket nicht mehr. Braucht DMS **0.94.0** oder neuer. Verhalten sonst unverändert.

## 1.0.0

- Erste Fassung: teilt einen Sammelscan in einer neuen Post an Trennblättern mit Code-128-Barcode (`DMS-TRENNEN`) in mehrere Posts; Trennblätter und ihre leeren Rückseiten fallen weg.
- Archivnummer-Aufkleber (`DMS-ASN:<nummer>`) setzen die Archivnummer am Dokument der neuen Post.
- Einstellungen: Barcode-Inhalt, Trennblatt behalten, leere Rückseite, Kanäle, Archivnummer, Auflösung, Seitenzahl.
- Eigener Code-128-Leser ohne fremde Bibliotheken; Trennblatt zum Ausdrucken (`vorlage/trennblatt.pdf`).
