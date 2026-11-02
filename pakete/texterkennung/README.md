# Texterkennung

Das Paket **Texterkennung** ist die Texterkennung des DMS: Es erkennt Text in gescannten PDFs und Fotos und schreibt ihn als **Volltext** ins DMS – damit findet die Suche auch Wörter aus Scans. Es nutzt [Tesseract](https://github.com/tesseract-ocr/tesseract) 5.5.1 als WebAssembly und läuft im **Paket-Läufer** des DMS: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit.

Seit DMS 0.133 liest das DMS selbst nur noch die **Textebene** von PDFs (poppler); seit DMS 0.134 steckt im DMS-Image keine Texterkennung mehr. Scans und Fotos bekommen ihren Text von diesem Paket. Ohne das Paket bleiben sie ohne Volltext („wartet auf Texterkennung – kein Paket installiert“).

## So arbeitet es

1. Ein Dokument kommt ins DMS. Das DMS liest bei PDFs die Textebene und meldet dem Paket das Ereignis **Volltext fertig** – auch, wenn es keinen Text gefunden hat.
2. **Ohne Text** (Scan, Foto) erkennt das Paket das Dokument immer. Bis es fertig ist, steht am Dokument „wartet auf Texterkennung (Paket Texterkennung)“, bei langen Dokumenten mit Fortschritt („Seite 20 von 64“).
3. **Mit Text aus dem PDF** bleibt dieser Text stehen – außer „Vorhandenen Volltext verwerfen und neu erkennen“ ist an. Stecken in einem PDF neben Textseiten auch gescannte Seiten, erkennt das Paket nur diese und setzt ihren Text an ihrer Stelle zwischen die Textseiten.
4. **Werkbank → Wartungsoperationen → Volltext neu erzeugen → Für alle Dokumente** erkennt immer neu, auch wenn der Haken aus ist – etwa nach einem neuen Sprach-Zusatzpaket.

Je Seite erkennt das Paket die **Lage** (quer, auf dem Kopf) und die **Schrift** und richtet die Seite vor dem Lesen auf. Bei **Sprache: Automatisch** erkennt es die **Sprache jeder Seite** (seit 2.1.0): Es liest die Seite zuerst in der Sprache der Seite davor (am Anfang Deutsch), erkennt die Sprache des Texts und liest die Seite in der erkannten Sprache ein zweites Mal, wenn es eine andere ist und ihre Sprachdaten da sind – das sicherere Ergebnis gilt. Stehen auf einer Seite zwei Sprachen, liest es sie zusätzlich mit beiden zugleich; ist das deutlich sicherer (mindestens 2 Prozentpunkte), gilt diese Lesung als **Mischseite**.

Das DMS bekommt den Text mit den **Sprachen je Seite**: Am Dokument steht dann z. B. „Deutsch, enthält auch Französisch“, die Suche nimmt je Seite die Wortstämme ihrer Sprache, und wechselt die Sprache zwischen zwei Seiten ganz, schlägt das DMS an der Post „Post teilen?“ vor (geteilt wird nie von selbst). Fehlen Sprachdaten (z. B. Französisch), steht das im Ergebnis und im Protokoll des Pakets: „Sprachdaten fehlen: fra (Zusatzpaket texterkennung_fra)“.

Lange Dokumente erkennt es **abschnittsweise**: Nach etwa einer Minute gibt es seinen Stand an den Läufer zurück, der es gleich wieder aufruft. Die Zeitgrenze des Läufers (2 Minuten je Aufruf) greift so nicht.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappe selbst liest das Paket nur, wenn du unter „Nur diese Mappentypen“ etwas einträgst.
- **Dokumente schreiben** – es holt Seiten als Graustufenbild und setzt den Volltext. Dateien ändert oder löscht es nicht.
- **Texterkennung übernehmen (dms:texterkennung)** – das DMS gibt Dokumente ohne Text an dieses Paket und zeigt „wartet auf Texterkennung“, bis es den Volltext schreibt.
- **Kein Netz.** Die Sprachdaten liegen im Paket bzw. in Zusatzpaketen.
- Es reagiert auf **Volltext fertig**.

Den Volltext des Pakets erkennst du am Hinweis „Texterkennung durch Paket Texterkennung 2.1.0“ am Dokument und an der Historie („Volltext von einem Paket“).

## Einstellungen

Unter **Werkbank → Pakete → Texterkennung → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Sprache | Automatisch | Automatisch (siehe oben), Deutsch, Englisch oder Deutsch und Englisch (je Seite die sicherere Lesung; dauert doppelt so lang) |
| Vorhandenen Volltext verwerfen und neu erkennen | aus | Aus: Text aus dem PDF bleibt, nur Dokumente ohne Text (und gescannte Seiten in PDFs) werden erkannt. An: jedes PDF und Bild wird neu erkannt und ersetzt den Text aus dem PDF. |
| Seiten selbst aufrichten | an | Lage und Schrift je Seite erkennen (osd) und die Seite vor dem Lesen aufrichten |
| Höchstens so viele Seiten | 100 | 1–1000; längere Dokumente erkennt es bis zu dieser Seite („Grenze erreicht“) |
| Auflösung (dpi) | 300 | 150–400; höher erkennt kleine Schrift besser, braucht aber mehr Zeit und Speicher |
| Nur diese Mappentypen | leer (alle) | Dokumente nur in Mappen dieser Typen |

Wer in Version 1 „Nur Dokumente ohne Text“ ausgeschaltet hatte, schaltet nach dem Update „Vorhandenen Volltext verwerfen und neu erkennen“ ein.

## Weitere Sprachen

Im Paket stecken Deutsch, Englisch und die Lageerkennung (osd). Weitere Sprachen kommen als **Zusatzpakete** `texterkennung_<sprache>` dazu, z. B. [Texterkennung – Französisch](../texterkennung_fra/). Ein Zusatzpaket hängt von diesem Paket ab; das DMS gibt diesem Paket seine Sprachdaten (`texterkennung_fra/fra.traineddata`). So bleibt jedes Paket weit unter der Grenze von 32 MB.

## Messung

Vergleich mit der früheren eingebauten Texterkennung des DMS (bis 0.133: Tesseract nativ, ein Thread, erster Durchgang `deu+eng`). Gemessen am 02.11.2026 auf amd64 mit 2 Kernen (der Rechner war nebenher belastet), DMS 0.134 mit den Standardgrenzen des Läufers (256 MB, 2 Minuten je Aufruf), Paket mit Standardeinstellungen und dem Zusatzpaket Französisch. Beide mit denselben Sprachdaten (tessdata_fast). Testdokumente: erfundene Briefe, als Graustufen-Scan gerendert (300 dpi, Fotos 200 dpi) – also saubere Vorlagen. Zeit beim Paket: vom Hochladen bis „fertig“ (mit Textebene, Zustellung und Schreiben des Volltexts); eingebaut: nur das Lesen der Datei. Richtig: Anteil richtiger Zeichen bzw. gefundener Wörter (ab 4 Buchstaben).

| Dokument | eingebaut: Zeit | Paket: Zeit | eingebaut: Zeichen / Wörter | Paket: Zeichen / Wörter |
| --- | ---: | ---: | ---: | ---: |
| Brief deutsch, 1 Seite | 2,5 s | 5,2 s | 100 % / 100 % | 100 % / 100 % |
| Brief englisch, 1 Seite | 2,6 s | 5,9 s | 100 % / 100 % | 100 % / 100 % |
| Brief französisch, 1 Seite | 2,3 s | 5,0 s | 99,4 % / 97,7 % | 99,7 % / 97,7 % |
| Brief quer eingescannt (90°) | 4,1 s | 4,4 s | 100 % / 100 % | 100 % / 100 % |
| Brief auf dem Kopf (180°) | 3,6 s | 4,4 s | 100 % / 100 % | 100 % / 100 % |
| Foto PNG | 2,1 s | 5,1 s | 100 % / 100 % | 100 % / 100 % |
| Foto JPEG | 2,2 s | 4,0 s | 100 % / 100 % | 100 % / 100 % |
| 10 Seiten | 25,7 s | 34,5 s | – / 100 % | – / 100 % |
| 60 Seiten (Paket: 4 Abschnitte) | 188 s | 242 s | – / 100 % | – / 100 % |

- **Erkennung:** gleich gut; Französisch mit dem Zusatzpaket etwas besser (zweiter Durchgang mit `fra`). Ohne das Zusatzpaket liest das Paket den französischen Brief auf Deutsch (98,3 % / 88,6 %) und meldet die fehlenden Sprachdaten.
- **Zeit:** Bei langen Dokumenten braucht das Paket etwa ein Drittel länger als Tesseract nativ (ein erster Lauf ergab 31 s für 10 und 184 s für 60 Seiten); bei einer einzelnen Seite kommen 1–3 Sekunden für Textebene, Zustellung und Schreiben dazu. Abschnittsweise Erkennung: 60 Seiten in 4 Aufrufen zu je etwa einer Minute, ohne dass die Zeitgrenze greift.
- **Größe:** Modul 2,7 MB, Sprachdaten 15,4 MB (deu 1,5 MB, eng 4,1 MB, osd 10,6 MB) – zusammen weit unter der Grenze von 32 MB.
- **Mehrsprachig (2.1.0):** Ein gescannter Brief mit drei Seiten (deutsch, französisch, Mischseite deutsch/französisch, 200 dpi) mit dem Zusatzpaket Französisch: 10,6 s vom Hochladen bis „fertig“ (zwei zweite Durchgänge, ein Durchgang mit beiden Sprachen); alle sechs Probewörter beider Sprachen findet die Suche. Gemessen am 02.11.2026 auf amd64 (2 Kerne, nebenher belastet), DMS 0.139.
- **arm64:** steht noch aus (beim Bau dieser Version war kein arm64-Rechner verfügbar).

## Grenzen

- Bilder: JPEG und PNG. TIFF, WebP, GIF und BMP liefert das DMS nicht als Seitenbild – sie bleiben ohne Volltext.
- Office-Dateien und E-Mails erkennt es nicht.
- Ein Dokument mit mehr Seiten als eingestellt wird nur bis zu dieser Seite erkannt.
- Schlägt ein Aufruf fehl, versucht es das DMS später erneut (1, 5, 30, 120, 360 Minuten) und zeigt das unter **Werkbank → Pakete → Texterkennung → Paket-Läufer**; danach steht das Dokument auf „Fehler“.

## Voraussetzungen

- DMS **0.139.0** oder neuer (Sprachen je Seite, Text je Seite bei gemischten PDFs); seit 0.133.0: Ereignis „Volltext fertig“ auch ohne Text, Recht „Texterkennung übernehmen“, Fortsetzung langer Aufgaben, Seitenbild für JPEG und PNG, Daten aus Zusatzpaketen. Für ältere DMS-Versionen bleibt Version 2.0.0 im Katalog.

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/texterkennung.cpp`](code/texterkennung.cpp) | das Modul (DMS-Paket-ABI 1): Ereignis → entscheiden → Seiten über die API → Lage (osd) → Tesseract mit Sprache je Seite und Mischseiten → Volltext mit `seitensprachen`; Fortsetzung mit `weiter` |
| [`code/sprache.h`](code/sprache.h) | Spracherkennung aus dem Text (wie im DMS), Sprachen einer Seite (Mischseite), Sprache passend zur Schrift; Test in [`tests/sprache_test.cpp`](tests/sprache_test.cpp) |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser ohne Ausnahmen |
| [`code/bauen.sh`](code/bauen.sh) | Bau: Leptonica 1.85.0 und Tesseract 5.5.1 aus den Quellen (feste Commits), Sprachdaten deu, eng, osd aus tessdata_fast (feste Prüfsummen) |
| [`code/wasi-compat.c`](code/wasi-compat.c), [`code/wasi-thread-shim.h`](code/wasi-thread-shim.h), [`code/stub/`](code/stub/) | was WASI nicht hat (Threads, temporäre Dateien, C++-Ausnahmen) |
| [`code/lizenzen/`](code/lizenzen/) | Lizenzen von Leptonica und Herkunft der Sprachdaten |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/texterkennung   # beim ersten Mal einige Minuten
```

Die Schnittstelle beschreibt das Entwicklerhandbuch des DMS unter [Pakete mit Code](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/) (Volltext fertig, Texterkennung übernehmen, Sprachen je Seite, Fortsetzung).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Im Modul stecken Tesseract (Apache-2.0) und Leptonica (BSD-artig, Text in [`code/lizenzen/leptonica.txt`](code/lizenzen/leptonica.txt)); die Sprachdaten stammen aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) (Apache-2.0).
