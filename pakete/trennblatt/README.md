# Trennblatt

Mit dem Paket **Trennblatt** scannst du einen ganzen Stapel Briefe auf einmal, und im DMS wird trotzdem **jeder Brief eine eigene Post**. Du legst zwischen zwei Briefe ein Trennblatt mit Barcode. Der Sammelscan kommt wie gewohnt als eine Post ins DMS. Das Paket findet die Trennblätter, teilt den Scan dort und lässt die Trennblätter weg.

Klebt auf einem Brief ein **Archivnummer-Aufkleber** des DMS, bekommt das Dokument der neuen Post gleich diese Archivnummer.

Das Paket läuft im **Paket-Läufer** des DMS: abgeschottet als WebAssembly, ohne Netz.

## So geht’s

1. **Trennblatt drucken:** [`vorlage/trennblatt.pdf`](vorlage/trennblatt.pdf) (A4, mit 100 % drucken). Ein paar Blätter reichen, du kannst sie immer wieder verwenden.
2. **Stapel vorbereiten:** Lege zwischen je zwei Briefe ein Trennblatt. Vor den ersten Brief brauchst du keins, schadet aber auch nicht.
3. **Scannen:** Scanne den ganzen Stapel in ein PDF. Scannst du beidseitig, ist das kein Problem: Die leere Rückseite eines Trennblatts fällt mit weg.
4. **Ins DMS:** Das PDF kommt wie jede andere Post ins DMS, über den Eingangsordner, das E-Mail-Postfach oder **+ Post**.
5. **Fertig:** Nach ein paar Sekunden siehst du unter **Post** für jeden Brief eine neue Post „*Betreff* (Teil 1)“, „(Teil 2)“ … mit Stand **Neu**. Die ursprüngliche Post hat danach Stand **Erledigt**, behält den ganzen Scan und verweist auf die neuen Posts. Es geht also nichts verloren.

```
Brief A · Trennblatt · Brief B · Trennblatt · Brief C (2 Seiten)
   → Post „Scan (Teil 1)“: Brief A
   → Post „Scan (Teil 2)“: Brief B
   → Post „Scan (Teil 3)“: Brief C, beide Seiten
```

### Archivnummer gleich mit

Hast du in der Werkbank unter **Nummernkreise** Archivnummer-Aufkleber gedruckt (Barcode `DMS-ASN:<nummer>`), dann klebe einen davon auf den Brief, bevor du scannst. Das Paket liest den Aufkleber und setzt die Nummer am Dokument der neuen Post. Später findest du das Papieroriginal über diese Nummer, und ein Handscanner springt im Suchfeld direkt zum Dokument. Ein Aufkleber auf dem Trennblatt selbst gilt für den Brief danach.

Liegt kein Trennblatt im Scan, setzt das Paket nur die Archivnummer am Dokument (ein Brief, ein Aufkleber). Gibt es die Nummer schon an einem anderen Dokument, lässt das Paket sie weg und schreibt eine Warnung ins Protokoll.

## Wann das Paket teilt

Das Paket schaut sich ein hochgeladenes PDF an, wenn alles davon stimmt:

- Es liegt in einer **Post** mit Stand **Neu**, die **eingeht** (keine versendete E-Mail).
- Die Post hat **genau dieses eine Dokument**, also einen Sammelscan. Eine E-Mail mit mehreren Anhängen bleibt, wie sie ist.
- Der **Kanal** der Post ist unter „Nur Post aus diesen Kanälen“ gewählt, oder dort ist nichts gewählt.
- Das PDF hat höchstens so viele Seiten wie eingestellt.

Findet es kein Trennblatt oder nur einen Brief, ändert es nichts.

## Was das Paket darf

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen, anlegen und ändern: alle Mappentypen.** Das Paket liest nur die Post, in die der Scan kam, und legt beim Teilen neue Posts an. Andere Mappen fasst es nicht an. Die Post ist ein Mappentyp des DMS, den ein Paket heute nur über „alle Mappentypen“ erreicht. Löschen kann ein Paket nie.
- **Dokumente schreiben.** Das Paket holt die Seiten als Graustufenbild, teilt das PDF und setzt die Archivnummer.
- **Kein Netz.**
- Es reagiert auf **Dokument hochgeladen**.

In der Historie der Posts steht „Paket Trennblatt“ als Urheber.

## Einstellungen

Unter **Werkbank → Pakete → Trennblatt → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Barcode auf dem Trennblatt | `DMS-TRENNEN` | Inhalt des Barcodes, an dem das Paket teilt. Groß- und Kleinschreibung zählen nicht. |
| Trennblatt behalten | Nein | Ja: Jedes Trennblatt bleibt als erste Seite der neuen Post. |
| Leere Rückseite mit entfernen | Ja | Eine leere Seite direkt nach einem Trennblatt (beidseitiger Scan) fällt mit weg. |
| Nur Post aus diesen Kanälen | leer (alle) | Eingangsordner, E-Mail-Postfach, Hochgeladen, Scan, WebDAV, API, Import |
| Archivnummer aus dem Aufkleber übernehmen | Ja | Barcode `DMS-ASN:<nummer>` auf einer Seite setzt die Archivnummer. |
| Auflösung (dpi) | 300 | 150–400. Für Trennblätter reichen 150 dpi, kleine Archivnummer-Aufkleber brauchen 300. |
| Höchstens so viele Seiten | 60 | Längere Scans prüft das Paket nicht. |

### Eigener Barcode

Du willst einen anderen Inhalt als `DMS-TRENNEN`, zum Beispiel weil ein anderes Programm schon so ein Trennblatt nutzt? Dann trag ihn in den Einstellungen ein und erzeuge dein Trennblatt so:

```sh
python3 vorlage/trennblatt.py --text MEIN-TRENNBLATT mein-trennblatt.pdf
```

Das Skript braucht nur Python 3, keine weiteren Pakete. Jedes Trennblatt mit einem Code-128-Barcode dieses Inhalts funktioniert.

## Messung

Im DMS 0.91 (Paket-Läufer mit Standardgrenzen: 256 MB, 120 s) auf amd64 mit 300 dpi:

| Scan | Dauer eines Aufrufs | Speicher |
| --- | --- | --- |
| 5 Seiten (3 Briefe, 2 Trennblätter) | 1,8 s | 9 MB |
| 8 Seiten, beidseitig und schief gescannt | etwa 6 s | 9 MB |

Den größten Teil der Zeit braucht das DMS, um die Seiten zu rastern. Mit dem Standard von 60 Seiten bleibt ein Aufruf deutlich unter der Zeitgrenze. Willst du längere Stapel teilen, setz die Auflösung auf 150 dpi (Archivnummer-Aufkleber werden dann oft nicht mehr gelesen).

## Grenzen

- Das Paket liest **Code 128**, so wie das DMS seine Aufkleber druckt. QR-Codes liest es nicht.
- Barcodes auf stark schiefen Seiten (mehr als etwa 15°) oder auf sehr kleinen Aufklebern bei niedriger Auflösung findet es unter Umständen nicht. Dann bleibt der Scan ungeteilt, und du kannst ihn im DMS von Hand teilen (**Post → Dokument → Seiten bearbeiten**).
- Eine Post mit mehreren Dokumenten teilt das Paket nicht.

## Voraussetzungen

- DMS **0.88.0** oder neuer (Paket-Läufer, Seite als Graustufenbild, Post teilen per API, Archivnummer per API).

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/trennblatt.cpp`](code/trennblatt.cpp) | das Modul (DMS-Paket-ABI 1): Ereignis → Seiten über die API → Barcodes → Post teilen, Archivnummer setzen |
| [`code/barcode.c`](code/barcode.c), [`code/barcode.h`](code/barcode.h) | eigener, kleiner Code-128-Leser (Zeichensätze A, B, C) für Graustufenbilder: tastet Zeilen und Spalten ab, örtliche Schwelle, Kanten auf Bruchteile eines Bildpunkts, liest in beide Richtungen, Prüfziffer |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser (aus dem Paket Texterkennung) |
| [`code/bauen.sh`](code/bauen.sh) | Bau mit dem WASI-SDK, ohne fremde Bibliotheken; danach der Test des Barcode-Lesers, wenn ein C-Compiler da ist |
| [`vorlage/trennblatt.py`](vorlage/trennblatt.py), [`vorlage/pdf.py`](vorlage/pdf.py) | erzeugen [`vorlage/trennblatt.pdf`](vorlage/trennblatt.pdf), nur mit der Standardbibliothek |
| [`tests/barcode_test.c`](tests/barcode_test.c) | künstliche Scans: schief, verrauscht, unscharf, verlaufene Tinte, auf dem Kopf, quer, kleinste Aufkleber; Textseiten ohne Fehllesung |
| [`tests/beispiel.py`](tests/beispiel.py) | Beispiel-PDFs: 3 Briefe mit 2 Trennblättern, dasselbe beidseitig und schief „gescannt“, ein Scan ohne Trennblatt |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | das gebaute Modul in Node mit einer Nachbildung der DMS-Importe und der API |
| [`tests/pruefen.sh`](tests/pruefen.sh) | alles zusammen |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/trennblatt   # Modul und Test des Barcode-Lesers
pakete/trennblatt/tests/pruefen.sh                                                # alle Tests (braucht node und Poppler)
```

Die Schnittstelle beschreibt das Entwicklerhandbuch des DMS unter [Pakete mit Code](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Das Paket enthält keinen fremden Code.
