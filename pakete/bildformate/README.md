# Bildformate

Ablago liest selbst nur PDF, JPEG und PNG. Mit dem Paket **Bildformate** bekommen auch **TIFF-Scans** (auch mehrseitig, wie sie viele Dokumentenscanner speichern), **WebP**, **GIF** und **BMP** ein **Vorschaubild** und einen **Volltext**: Das Paket wandelt jede solche Datei in eine Fassung, die Ablago kennt – daraus macht Ablago das Vorschaubild und liest den Text (bei Scans über das Paket [Texterkennung](../texterkennung/)). **Das Original bleibt das Dokument**; Herunterladen, Weitergeben und Versionen betreffen weiter die Originaldatei.

Es läuft im **Paket-Läufer** von Ablago: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit.

## So arbeitet es

1. Eine TIFF-, WebP-, GIF- oder BMP-Datei kommt in Ablago. Ablago meldet sie dem Paket (Ereignis **Datei umwandeln**); am Dokument steht so lange „wartet auf Umwandlung (Paket Bildformate)“.
2. Das Paket liest die Datei, erkennt den Typ **am Inhalt** (nicht am Namen) und gibt die Fassung zurück:

   | Datei | Fassung | Wie |
   | --- | --- | --- |
   | TIFF (auch mehrseitig; unkomprimiert, LZW, Deflate, PackBits, CCITT G3/G4, JPEG) | **PDF**, eine Seite je Bild | Schwarzweiß-Seiten verlustfrei (1 Bit), Graustufen und Farbe als JPEG (Qualität 90). Die Seitengröße kommt aus der Auflösung des TIFF; fehlt sie, gilt 300 dpi. |
   | WebP | **JPEG** (Qualität 90) | Durchsichtiges kommt auf Weiß. |
   | GIF (bei Animationen das erste Bild) | **PNG** | verlustfrei |
   | BMP | **PNG** | verlustfrei |

3. Ablago macht aus der Fassung das Vorschaubild und den Volltext. Am Dokument steht dann z. B. „Texterkennung durch Paket Texterkennung 2.0.0“ und „aus der umgewandelten Fassung (Bildformate 1.0.0)“ mit **Fassung ansehen**; das Vorschaubild hat den Hinweis „Vorschau aus der umgewandelten Fassung eines Pakets“; in der Historie der Mappe „umgewandelte Fassung erstellt – TIFF → PDF (Bildformate 1.0.0)“.
4. **Vorhandene Dateien:** Beim Installieren gibt Ablago alle vorhandenen TIFF-, WebP-, GIF- und BMP-Dateien an das Paket. Später holt **Werkbank → Wartungsoperationen → Vorschaubilder nachholen** fehlende Fassungen nach (etwa nach einer Wiederherstellung – Fassungen gehen nicht in die Sicherung).

Kann das Paket eine Datei nicht lesen (beschädigt, unbekannte Variante), steht der Grund am Dokument („Umwandlung durch Paket Bildformate: TIFF lässt sich nicht lesen: …“).

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappen selbst liest das Paket nicht.
- **Dokumente lesen** – es liest die Originaldatei. Dokumente ändert, ersetzt oder löscht es nicht.
- **Dateien umwandeln, die Ablago nicht selbst lesen kann – das Paket liest die Originaldatei und liefert eine Fassung (PDF, PNG oder JPEG) für Vorschaubild und Volltext; das Original bleibt unverändert (dms:umwandeln): TIFF, WebP, GIF, BMP** – Ablago gibt diese Dateitypen an das Paket und nimmt die Fassung an.
- **Kein Netz.** Alles geschieht im Paket.
- Es reagiert auf **Eine Datei soll umgewandelt werden** (`datei.umwandeln`).

## Einstellungen

Unter **Werkbank → Pakete → Bildformate → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Höchstens so viele Seiten | 200 | 1–1000; mehrseitige TIFF-Dateien wandelt das Paket bis zu dieser Seite in ein PDF („nur die ersten … von …“) |

## Messung

Gemessen am 02.11.2026 auf amd64 mit 2 Kernen (nebenher belastet), Node 22, nur das Umwandeln im Modul (`node tests/modul_test.mjs <ordner> --messen`), mit erfundenen Testseiten:

| Datei | Größe | Fassung | Zeit | Speicher |
| --- | ---: | --- | ---: | ---: |
| TIFF, 10 Seiten A4, 300 dpi, Schwarzweiß (G4) | 18 KB | PDF, 24 KB | 0,9–1,0 s | 48 MB |
| TIFF, 1 Seite A4, 300 dpi, Farbe (LZW) | 210 KB | PDF, 230 KB | 0,2 s | 36 MB |
| TIFF, 1 Seite A4, 300 dpi, Farbe (JPEG) | 536 KB | PDF, 231 KB | 0,3 s | 36 MB |
| WebP, 4000 × 3000 (12 Megapixel) | 35 KB | JPEG, 309 KB | 0,4 s | 49 MB |
| BMP, 1920 × 1080 | 5,9 MB | PNG, 13 KB | 0,2 s | 30 MB |

In Ablago (Paket-Läufer, mit dem Paket Texterkennung): ein zweiseitiger TIFF-Scan war vom Hochladen bis zum fertigen Volltext nach etwa 5 Sekunden durchsuchbar, die Umwandlung selbst dauerte unter einer Sekunde. Das Modul ist 1,2 MB groß.

## Grenzen

- Höchstens 36 Millionen Bildpunkte je Seite bzw. Bild (A3 mit 400 dpi passt) und 50 MB je Datei und Fassung; größere Dateien gibt Ablago gar nicht erst ab.
- Ein beschädigtes JPEG **innerhalb** eines TIFF beendet den Aufruf (WebAssembly ohne `setjmp`); der Paket-Läufer versucht es dann einige Male und meldet einen Fehler.
- TIFF mit 12 oder 16 Bit je Kanal liest das Paket über libtiff als 8 Bit; Farbprofile werden nicht umgerechnet.
- **HEIC** (Fotos vom iPhone) wandelt es **nicht** um – siehe unten. **Office-Dateien** und E-Mails auch nicht (geplant mit [#30](https://github.com/motom001/dms-registry/issues/30)).

## Warum kein HEIC? Warum kein Office?

- **HEIC/HEIF** speichert Bilder mit **HEVC (H.265)**. Die freien Decoder (libheif mit libde265) stehen unter LGPL-3.0 – das ginge mit einem eigenen Paket unter `LGPL-3.0-or-later`. Für HEVC verlangen aber mehrere Patentpools Lizenzen auch für Software-Decoder; ob und wie das offizielle Katalog-Paket das darf, klären wir vorher (dms-registry #48). Bis dahin: auf dem iPhone *Einstellungen → Kamera → Formate → Maximale Kompatibilität* (dann speichert es JPEG); beim Hochladen über den Browser wandelt iOS Fotos aus der Mediathek meist schon selbst in JPEG.
- **Office** (Word, Excel, PowerPoint, OpenDocument) bräuchte ein ganzes Office-Paket als WebAssembly. LibreOffice ist dafür ein Vielfaches größer als die Grenze von 32 MB je Paket; kleinere Bibliotheken setzen Office-Dateien nicht verlässlich. Das gehört zu [#30](https://github.com/motom001/dms-registry/issues/30) (Office und E-Mail) und kommt als eigenes Paket – die Schnittstelle von Ablago dafür gibt es schon (siehe unten).

## Voraussetzungen

- Ablago **0.137.0** oder neuer (Schnittstelle „Dateien umwandeln“, `dms:umwandeln`).
- Für den Text aus Scans: das Paket [Texterkennung](../texterkennung/) (2.0 oder neuer). Ohne das Paket bekommen umgewandelte Scans ein Vorschaubild, aber erst mit ihm einen Volltext.

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/bildformate.cpp`](code/bildformate.cpp) | das Modul (Ablago-Paket-ABI 1): Ereignis → Original über die API → lesen (libtiff, libwebp, stb_image) → PDF, JPEG oder PNG → `PUT /dokumente/{id}/fassung` |
| [`code/ausgabe.h`](code/ausgabe.h) | ohne Bibliotheken: Bildart (Schwarzweiß, Grau, Farbe), 1-Bit-Packen, PDF schreiben, Dateityp am Inhalt; Test in [`tests/ausgabe_test.cpp`](tests/ausgabe_test.cpp) |
| [`code/bauen.sh`](code/bauen.sh) | Bau: zlib 1.3.1, libjpeg-turbo 3.1.2, libtiff 4.7.1, libwebp 1.5.0 und stb aus den Quellen (feste Commits, Hash geprüft) |
| [`code/stub/setjmp.h`](code/stub/setjmp.h), [`code/wasi-compat.c`](code/wasi-compat.c) | was WASI nicht hat (`setjmp`/`longjmp`, temporäre Dateien) |
| [`code/lizenzen/`](code/lizenzen/) | Lizenztexte der Bibliotheken |
| [`tests/`](tests/) | `beispiele.py` (Testbilder mit Pillow und Vergleich), `modul_test.mjs` (das Modul mit einer Nachbildung von Ablago), `ci.sh` (CI), `pruefen.sh` (alles lokal) |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/bildformate   # beim ersten Mal einige Minuten
pakete/bildformate/tests/pruefen.sh                                                 # bauen und alle Tests
```

libtiff holt der Bau vom Original auf gitlab.com (Tag v4.7.1); so baut auch die CI. Ist gitlab.com nicht erreichbar, nimmt der Bau mit `LIBTIFF_QUELLE=https://github.com/libsdl-org/libtiff` den GitHub-Spiegel – der Commit (`5fe20d0e…`) ist derselbe und wird in beiden Fällen geprüft.

Die Schnittstelle – wie ein Paket mit Ablago spricht und welche Formate es zurückgeben darf – beschreibt das Entwicklerhandbuch von Ablago unter [Dateien umwandeln](https://help.ablago.app/entwickler/aktuell/pakete-code/#dateien-umwandeln).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Im Modul stecken fremde Bibliotheken; ihre Lizenztexte liegen unter [`code/lizenzen/`](code/lizenzen/):

| Bibliothek | Version | Lizenz |
| --- | --- | --- |
| [libtiff](https://libtiff.gitlab.io/libtiff/) (Bau aus dem Original [gitlab.com/libtiff/libtiff](https://gitlab.com/libtiff/libtiff), Tag v4.7.1) | 4.7.1 | libtiff-Lizenz (BSD-artig) – `libtiff.md` |
| [libjpeg-turbo](https://libjpeg-turbo.org/) | 3.1.2 | IJG und BSD-3-Clause – `libjpeg-turbo.md`, `libjpeg-turbo-ijg.txt` |
| [libwebp](https://github.com/webmproject/libwebp) | 1.5.0 | BSD-3-Clause mit Patentzusage von Google – `libwebp.txt`, `libwebp-patente.txt` |
| [zlib](https://zlib.net/) | 1.3.1 | Zlib – `zlib.txt` |
| [stb_image, stb_image_write](https://github.com/nothings/stb) | 2.30 / 1.16 | MIT oder Public Domain – `stb.txt` |

Diese Software beruht teilweise auf der Arbeit der Independent JPEG Group. – This software is based in part on the work of the Independent JPEG Group.
