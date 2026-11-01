# Änderungen

## 1.0.1

- Rechte: nur noch **Post** lesen, anlegen und ändern (`dms:post`) statt aller Mappentypen (`"*"`). Andere Mappen sieht das Paket nicht mehr. Braucht DMS **0.94.0** oder neuer. Verhalten sonst unverändert.

## 1.0.0

- Erste Fassung: teilt einen Sammelscan in einer neuen Post an Trennblättern mit Code-128-Barcode (`DMS-TRENNEN`) in mehrere Posts; Trennblätter und ihre leeren Rückseiten fallen weg.
- Archivnummer-Aufkleber (`DMS-ASN:<nummer>`) setzen die Archivnummer am Dokument der neuen Post.
- Einstellungen: Barcode-Inhalt, Trennblatt behalten, leere Rückseite, Kanäle, Archivnummer, Auflösung, Seitenzahl.
- Eigener Code-128-Leser ohne fremde Bibliotheken; Trennblatt zum Ausdrucken (`vorlage/trennblatt.pdf`).
