# Änderungen

## 1.0.0

- Erste Fassung (dms-registry #30, Stufe 1): **Volltext** für Word, Excel und PowerPoint (`.docx`, `.xlsx`, `.pptx`, auch mit Makros und Vorlagen), OpenDocument (`.odt`, `.ods`, `.odp`), RTF, Textdateien und E-Mails (`.eml`, Outlook `.msg`, mit dem Text lesbarer Anhänge) – über das Ereignis „Dokument hochgeladen“ und `PUT /dokumente/{id}/volltext`.
- Makros und eingebettete Objekte werden nie gelesen oder ausgeführt; XML ohne DTD und Entitäten, Grenzen gegen ZIP-Bomben, kein Netz.
- Einzige fremde Bibliothek: zlib 1.3.1. Keine Einstellungen.
- Noch nicht: Vorschaubild und PDF-Ansicht (#72), Dateien von vor der Installation, neue Versionen (brauchen eine Änderung im DMS).
