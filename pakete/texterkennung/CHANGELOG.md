# Änderungen

## 2.0.0

Die Texterkennung wandert aus dem DMS in dieses Paket (DMS 0.133.0, motom001/dms#458; seit DMS 0.134.0 ohne Tesseract im Image, motom001/dms#459). Das Paket ist jetzt **die** Texterkennung des DMS und erkennt so gut wie die bisher eingebaute (siehe Messung im README).

- **Braucht DMS 0.133.0.** Neues Recht „Texterkennung übernehmen“ (`dms:texterkennung`): Das DMS liest selbst nur die Textebene von PDFs; Dokumente ohne Text stehen auf „wartet auf Texterkennung (Paket Texterkennung)“, bis das Paket fertig ist. Das Paket reagiert nur noch auf **Volltext fertig** (statt „Dokument hochgeladen“ und „Texterkennung fertig“).
- **„Vorhandenen Volltext verwerfen und neu erkennen“** (Standard: aus) ersetzt „Nur Dokumente ohne Text“. Aus: Text aus dem PDF bleibt, nur Dokumente ohne Text werden erkannt. An: jedes PDF und Bild wird neu erkannt. **Volltext neu erzeugen → Für alle Dokumente** in der Werkbank erkennt immer neu. Wer „Nur Dokumente ohne Text“ ausgeschaltet hatte, schaltet nach dem Update „verwerfen“ ein.
- **Sprache: Automatisch** (neuer Standard): erster Durchgang Deutsch, Sprache aus dem Text erkennen, bei einer anderen Sprache die Seite in dieser ein zweites Mal lesen, die sicherere Lesung gilt (wie im DMS seit 0.90 – hier aber auch bei sicherem erstem Durchgang, sonst fehlen z. B. die Akzente). Fehlende Sprachdaten stehen im Protokoll des Pakets und im Ergebnis.
- **Seiten selbst aufrichten** (osd): Lage (quer, auf dem Kopf) und Schrift (z. B. Kyrillisch) je Seite erkennen. Neu im Paket: `osd.traineddata`.
- **Lange Dokumente abschnittsweise:** etwa eine Minute je Aufruf, dann setzt der Läufer gleich fort (`weiter`). Die Zeitgrenze von 2 Minuten greift nicht mehr; am Dokument steht „Seite 20 von 64“. Höchstens so viele Seiten: Standard 100 (bis 1000).
- **Gemischte PDFs** (Textseiten und gescannte Seiten): erkennt nur die Seiten ohne Text und hängt ihren Text an den Text aus dem PDF an.
- **Bilder:** JPEG und PNG (das DMS liefert das Seitenbild seit 0.133.0); TIFF liefert das DMS nicht.
- **Weitere Sprachen als Zusatzpakete** (`texterkennung_<sprache>`), Muster: [texterkennung_fra](../texterkennung_fra/).

## 1.0.0

- Erste Fassung: Tesseract 5.5.1 und Leptonica 1.85.0 als WebAssembly, Sprachen Deutsch und Englisch (tessdata_fast), Einstellungen für Sprache, „Nur Dokumente ohne Text“, Seitenzahl, Auflösung und Mappentypen.
