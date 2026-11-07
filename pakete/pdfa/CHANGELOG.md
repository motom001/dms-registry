# Änderungen

## 1.2.0

- **E-Mails als Archivfassung** (dms-registry #143, Stufe 1; Ablago mit der Art `emails`, DMS #946): `.eml` und Outlook `.msg` setzt das Paket **selbst zu Seiten** – ohne Browser, ohne Netz, ohne Wortpositionen. Oben ein **Kopfblock** wie ein Briefkopf (Betreff, Von, An, Cc, Datum in der Zeitzone der Ablage), darunter der Text: Klartext mit eingerückten Zitaten oder einfaches HTML (Absätze, Überschriften, Listen, Fett, Kursiv, einfache Tabellen, Links als Text mit Adresse). **Bilder aus der Mail** (`cid:`) stehen an ihrer Stelle; **Bilder aus dem Internet werden nie geladen** – an ihrer Stelle steht „externes Bild nicht geladen“, Zählpixel bleiben wirkungslos. **Anhänge** stehen am Ende als Liste (Name, Art, Größe), ihr Inhalt nicht; **weitergeleitete Mails** folgen darunter, bis zur dritten Ebene. Verschlüsselte Teile (S/MIME, PGP/MIME) bleiben verschlüsselt. Kopf- und Fußzeile mit „Seite 1 von 3“.
- **Schrift Noto Sans** (SIL OFL 1.1; normal, fett, kursiv, fett-kursiv), eingebettet als **Teilmenge**: sichtbarer, durchsuchbarer, kopierbarer Text. Umlaute, europäische Schriften, Griechisch und Kyrillisch; was die Schrift nicht kann, steht als Rahmen „□“ da, nie als „?“.
- Neue Einstellung **„E-Mails (.eml, .msg)“** (Vorgabe an). Dateitypen `message/rfc822`, `application/vnd.ms-outlook` und `application/octet-stream` mit Endung `.eml`/`.msg`.
- Den Mail-Zerleger teilt das Paket mit „Office und E-Mail“ (`gemeinsam/mail/`).
- Braucht Ablago mit der Art `emails` (vorläufig 0.217.0).

## 1.1.0

- **Ankreuzen statt verneinen** (dms-registry #106, DMS #660): Statt des Hakens „Nur Scans und Bilder“ gibt es unter „Archivfassung anlegen für …“ drei Haken – **PDFs mit Text**, **Gescannte PDFs**, **Fotos und Bilder** (mit den Dateiendungen, getrennt nach „immer“ und „mit Paket Bildformate“) – Vorgabe alle an. Braucht Ablago 0.176.0 (`code.archivfassung.auswahl`).
- Englische Texte kommen mit den Sprachpaketen (Etappe 07d).

## 1.0.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.0.0

- Erste Fassung (dms-registry #29, DMS #631): legt zu jedem Dokument mit fertigem Volltext eine **Archivfassung** ab – ein durchsuchbares **PDF/A-2b** mit unsichtbarer Textebene genau auf den Wörtern – über die neue Schnittstelle „Archivfassung ablegen“ (`dms:archivfassung`) des DMS 0.149.0. Das Original bleibt das Dokument.
- JPEG unverändert übernommen (ohne EXIF-Metadaten, aufgerichtet nach EXIF), PNG verlustfrei, PDF-Seiten als Bild mit 300 dpi in Graustufen (ab 51 Seiten 200, ab 201 Seiten 150 dpi), TIFF, WebP, GIF und BMP über die Lesefassung des Pakets Bildformate.
- Eine Einstellung: „Nur Scans und Bilder“ (Standard aus).
- Ohne Wortpositionen (ältere Texterkennung) keine Archivfassung, sondern der Grund am Dokument.
- Eigener PDF/A-Schreiber; Bibliotheken aus den Quellen: zlib 1.3.1, libjpeg-turbo 3.1.2, stb_image 2.30; Schrift GlyphLessFont (Tesseract, Apache-2.0), sRGB-Profil (CC0-1.0). Geprüft mit veraPDF (PDF/A-2b) in der CI.
