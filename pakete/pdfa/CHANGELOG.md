# Änderungen

## 1.0.0

- Erste Fassung (dms-registry #29, DMS #631): legt zu jedem Dokument mit fertigem Volltext eine **Archivfassung** ab – ein durchsuchbares **PDF/A-2b** mit unsichtbarer Textebene genau auf den Wörtern – über die neue Schnittstelle „Archivfassung ablegen“ (`dms:archivfassung`) des DMS 0.149.0. Das Original bleibt das Dokument.
- JPEG unverändert übernommen (ohne EXIF-Metadaten, aufgerichtet nach EXIF), PNG verlustfrei, PDF-Seiten als Bild mit 300 dpi in Graustufen (ab 51 Seiten 200, ab 201 Seiten 150 dpi), TIFF, WebP, GIF und BMP über die Lesefassung des Pakets Bildformate.
- Eine Einstellung: „Nur Scans und Bilder“ (Standard aus).
- Ohne Wortpositionen (ältere Texterkennung) keine Archivfassung, sondern der Grund am Dokument.
- Eigener PDF/A-Schreiber; Bibliotheken aus den Quellen: zlib 1.3.1, libjpeg-turbo 3.1.2, stb_image 2.30; Schrift GlyphLessFont (Tesseract, Apache-2.0), sRGB-Profil (CC0-1.0). Geprüft mit veraPDF (PDF/A-2b) in der CI.
