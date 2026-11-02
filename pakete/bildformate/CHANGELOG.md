# Änderungen

## 1.0.1

- Kurzbeschreibung für Einsteiger (#80): sagt jetzt klar, dass das Paket Dateien sichtbar macht und für durchsuchbaren Text bei Scans zusätzlich die Texterkennung nötig ist. Am Paket selbst ändert sich nichts.

## 1.0.0

- Erste Fassung (dms-registry #48, DMS #577): Vorschaubild und Volltext für **TIFF** (auch mehrseitig; unkomprimiert, LZW, Deflate, PackBits, CCITT G3/G4, JPEG) → PDF, **WebP** → JPEG, **GIF** (erstes Bild) und **BMP** → PNG – über die neue Schnittstelle „Dateien umwandeln“ (`dms:umwandeln`) des DMS 0.137.0. Das Original bleibt das Dokument.
- Bibliotheken aus den Quellen: libtiff 4.7.1, libjpeg-turbo 3.1.2, libwebp 1.5.0, zlib 1.3.1, stb_image 2.30 / stb_image_write 1.16.
- Einstellung „Höchstens so viele Seiten“ (Standard 200) für mehrseitige TIFF-Dateien.
- HEIC noch nicht (Patentfragen bei HEVC, siehe README), Office mit #30.
