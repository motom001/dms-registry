# Texterkennung

Das Paket **Texterkennung** erkennt Text in gescannten PDFs und Bildern und schreibt ihn als **Volltext** ins DMS – damit findet die Suche auch Wörter aus Scans. Es nutzt [Tesseract](https://github.com/tesseract-ocr/tesseract) 5.5.1 als WebAssembly und läuft im **Paket-Läufer** des DMS: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit.

Das DMS hat schon eine eingebaute Texterkennung, und die bleibt: Sie ist schneller. Dieses Paket ist das **Referenzpaket für Pakete mit Code** – es zeigt, dass auch eine rechenintensive Aufgabe sicher als Paket läuft – und hilft, wo die eingebaute Erkennung keinen Text findet.

## Was das Paket darf

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappe selbst liest das Paket nur, wenn du unter „Nur diese Mappentypen“ etwas einträgst.
- **Dokumente schreiben** – es holt Seiten als Graustufenbild und setzt den Volltext. Dateien ändert oder löscht es nicht.
- **Kein Netz.** Die Sprachdaten liegen im Paket.
- Es reagiert auf **Dokument hochgeladen** und **Texterkennung fertig**.

Den Volltext eines Pakets erkennst du an der Historie („Volltext von einem Paket“) und am Hinweis „Texterkennung durch Paket Texterkennung 1.0.0“ am Dokument. Die eingebaute Texterkennung überschreibt ihn nicht.

## Einstellungen

Unter **Werkbank → Pakete → Texterkennung → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Sprache | Deutsch | Deutsch, Englisch oder beide (je Seite die sicherere Erkennung; dauert doppelt so lang) |
| Nur Dokumente ohne Text | Ja | Ja: Das Paket wartet auf die Texterkennung des DMS und erkennt nur, wenn sie keinen Text fand. Nein: Es erkennt jedes neue PDF und Bild und ersetzt den Volltext. |
| Höchstens so viele Seiten | 30 | Längere Dokumente erkennt es bis zu dieser Seite; die Übersicht meldet „Grenze erreicht“. |
| Auflösung (dpi) | 300 | 150–400; höher erkennt kleine Schrift besser, braucht aber mehr Zeit und Speicher. |
| Nur diese Mappentypen | leer (alle) | Dokumente nur in Mappen dieser Typen |

## Messung

Brief mit gemischtem Text, A4 quer gescannt mit 300 dpi; DMS 0.88.0 mit Standardgrenzen des Läufers (256 MB, 120 s). Gemessen auf amd64 (2 Kerne):

| | Paket (WebAssembly) | eingebaute Texterkennung (Tesseract nativ, ein Thread) |
| --- | --- | --- |
| 10 Seiten | 14,3 s | 6,5 s |
| Speicher je Aufruf | etwa 30 MB | – |

Das Paket ist also gut doppelt so langsam wie die eingebaute Erkennung; bei den Standardgrenzen schafft ein Aufruf rund 80 Seiten. Eine Messung auf arm64 folgt.

## Grenzen

- Ein Dokument mit mehr Seiten als eingestellt wird nur bis zu dieser Seite erkannt.
- Dauert ein Aufruf länger als die Zeitgrenze des Läufers (2 Minuten), bricht das DMS ihn ab, versucht es später erneut (1, 5, 30, 120, 360 Minuten) und zeigt das unter **Werkbank → Pakete → Texterkennung → Paket-Läufer**. Dann die Seitenzahl oder Auflösung senken.
- Office-Dateien und E-Mails erkennt es nicht – nur PDFs und Bilder.

## Voraussetzungen

- DMS **0.88.0** oder neuer (Paket-Läufer, Volltext schreiben, Seite als Graustufenbild).

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/texterkennung.cpp`](code/texterkennung.cpp) | das Modul (DMS-Paket-ABI 1): Ereignis → Seiten über die API → Tesseract → Volltext |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser ohne Ausnahmen |
| [`code/bauen.sh`](code/bauen.sh) | Bau: Leptonica 1.85.0 und Tesseract 5.5.1 aus den Quellen (feste Commits), Sprachdaten aus tessdata_fast (feste Prüfsummen) |
| [`code/wasi-compat.c`](code/wasi-compat.c), [`code/wasi-thread-shim.h`](code/wasi-thread-shim.h), [`code/stub/`](code/stub/) | was WASI nicht hat (Threads, temporäre Dateien, C++-Ausnahmen) |
| [`code/lizenzen/`](code/lizenzen/) | Lizenzen von Leptonica und Herkunft der Sprachdaten |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/texterkennung   # beim ersten Mal einige Minuten
```

Die Schnittstelle beschreibt das Entwicklerhandbuch des DMS unter [Pakete mit Code](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Im Modul stecken Tesseract (Apache-2.0) und Leptonica (BSD-artig, Text in [`code/lizenzen/leptonica.txt`](code/lizenzen/leptonica.txt)); die Sprachdaten stammen aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) (Apache-2.0).
