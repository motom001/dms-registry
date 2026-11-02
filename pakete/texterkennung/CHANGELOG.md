# Änderungen

## 2.1.1

- Name „Texterkennung (Deutsch und Englisch)“ und neue Beschreibung: Das Paket ist das Grundpaket, weitere Sprachen kommen als Zusatzsprachen (Französisch, Spanisch, Italienisch, Niederländisch, Portugiesisch, Polnisch, Türkisch, Russisch, Ukrainisch, Arabisch). Sonst unverändert.

## 2.1.0

Dokumente in mehreren Sprachen (motom001/dms#579). **Braucht DMS 0.139.0.**

- **Sprache je Seite:** Bei *Sprache: Automatisch* erkennt das Paket die Sprache jeder Seite einzeln. Es liest eine Seite zuerst in der Sprache der Seite davor (am Anfang Deutsch), erkennt die Sprache des Texts und liest sie in einer anderen erkannten Sprache ein zweites Mal, wenn deren Sprachdaten da sind – die sicherere Lesung gilt. Bisher entschied die erste Seite mit Text für das ganze Dokument; ein französisches Schreiben hinter einem deutschen Begleitbrief verlor seine Akzente.
- **Mischseiten:** Stehen auf einer Seite zwei Sprachen (je mindestens ein Fünftel des Texts), liest das Paket sie zusätzlich mit beiden zugleich (Tesseract `deu+fra`). Ist das mindestens 2 Prozentpunkte sicherer, gilt diese Lesung und die Seite bekommt beide Sprachen.
- **Sprachen an das DMS:** Der Volltext geht mit den Seiten (getrennt durch Seitenvorschub) und `seitensprachen` an das DMS. Das DMS zeigt „Deutsch, enthält auch Französisch“, durchsucht jede Seite mit den Wortstämmen ihrer Sprache und schlägt bei einem Sprachwechsel „Post teilen?“ vor. Bei festen Sprachen (Deutsch, Englisch, beide) meldet das Paket je Seite die Sprache ihres Texts, ohne zweiten Durchgang.
- **Gemischte PDFs** (Textseiten und gescannte Seiten): Die erkannten Seiten kommen an ihre Stelle zwischen den Textseiten (bisher hinten angehängt); das DMS liefert dafür den Text je Seite.
- Die Meldung am Dokument nennt die Sprachen („3 Seiten, 1230 Zeichen, deu, enthält auch fra, 1 Mischseite, 2× zweiter Durchgang“).
- Ein langes Dokument, das bei der Aktualisierung gerade abschnittsweise erkannt wurde, fängt mit 2.1.0 von vorn an.

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
