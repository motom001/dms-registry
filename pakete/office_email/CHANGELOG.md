# Änderungen

## 1.1.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.1.0

- **Eigenes Recht statt Schreibrecht** (DMS #614): Das Paket nutzt das Recht „Volltext liefern“ (`dms:volltext`) mit „Dokumente lesen“ – es darf nur noch den Volltext seiner Dateitypen schreiben, keine Dokumente hochladen oder ersetzen. Braucht DMS 0.145.0.
- **Alle passenden Dateien:** Das DMS meldet sie jetzt mit dem Ereignis „Datei braucht Volltext“ (`datei.volltext`) – beim Hochladen, bei **neuen Versionen**, beim Installieren für **vorhandene Dateien** ohne Text und bei **Volltext neu erzeugen**. Bis das Paket schreibt, steht am Dokument „wartet auf Volltext“; kann es eine Datei nicht lesen, steht der Grund am Dokument.
- **Länger:** bis 5 Millionen Zeichen je Datei (bisher etwa 1,8 Millionen).

## 1.0.0

- Erste Fassung (dms-registry #30, Stufe 1): **Volltext** für Word, Excel und PowerPoint (`.docx`, `.xlsx`, `.pptx`, auch mit Makros und Vorlagen), OpenDocument (`.odt`, `.ods`, `.odp`), RTF, Textdateien und E-Mails (`.eml`, Outlook `.msg`, mit dem Text lesbarer Anhänge) – über das Ereignis „Dokument hochgeladen“ und `PUT /dokumente/{id}/volltext`.
- Makros und eingebettete Objekte werden nie gelesen oder ausgeführt; XML ohne DTD und Entitäten, Grenzen gegen ZIP-Bomben, kein Netz.
- Einzige fremde Bibliothek: zlib 1.3.1. Keine Einstellungen.
- Noch nicht: Vorschaubild und PDF-Ansicht (#72), Dateien von vor der Installation, neue Versionen (brauchen eine Änderung im DMS).
