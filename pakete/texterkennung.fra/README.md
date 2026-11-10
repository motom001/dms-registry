# Texterkennung – Zusatzsprache Französisch

Dieses **Zusatzpaket** bringt dem Grundpaket [Texterkennung](../texterkennung/) (Deutsch und Englisch) Französisch bei. Es enthält nur die Sprachdaten (`fra.traineddata` aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast)) und ein Modul, das nichts tut.

Mit **Sprache: Automatisch** erkennt das Paket Texterkennung, wenn ein Brief französisch ist, und liest unsichere Seiten dann ein zweites Mal auf Französisch – das bessere Ergebnis gilt. Ohne dieses Zusatzpaket meldet es „Sprachdaten fehlen: fra (Zusatzpaket texterkennung.fra)“ im Protokoll des Pakets und am Ergebnis des Aufrufs.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago:

- **kein Zugriff auf Netzwerk und Internet**
- keine Rechte an Mappen und Dokumenten, keine Ereignisse

Das Paket Texterkennung liest die Sprachdaten, weil dieses Paket von ihm abhängt (Ablago ab 0.133.0: ein Paket liest die Daten der Pakete, die von ihm abhängen, als `texterkennung.fra/fra.traineddata`). Wird das Zusatzpaket installiert oder entfernt, lädt der Paket-Läufer die Texterkennung neu – du musst nichts weiter tun. Dokumente, die schon ohne Französisch erkannt wurden, erkennt **Werkbank → Wartungsoperationen → Volltext neu erzeugen → Für alle Dokumente** neu.

## Voraussetzungen

- Ablago **0.133.0** oder neuer
- Paket **Texterkennung 2.0.0** oder neuer (kommt als Abhängigkeit mit)

## Weitere Sprachen

Dieses Paket ist das Muster; fertig im Katalog sind außerdem Spanisch, Italienisch, Niederländisch, Portugiesisch, Polnisch, Türkisch, Russisch, Ukrainisch und Arabisch. Für eine weitere Sprache den Ordner kopieren (`texterkennung.<kennung>`, z. B. `texterkennung.tur`), in `manifest.yaml` Id und Namen (ohne `ersetzt` – das gilt nur für die umgezogenen Sprachen) und in `code/bauen.sh` `SPRACHE` und `SHA256` ändern. Kennungen wie bei Tesseract; die Spracherkennung des Pakets kennt Französisch (`fra`), Spanisch (`spa`), Italienisch (`ita`), Niederländisch (`nld`), Türkisch (`tur`), Polnisch (`pol`), Portugiesisch (`por`), Russisch (`rus`), Ukrainisch (`ukr`) und Arabisch (`ara`). Eine Sprachdatei aus tessdata_fast ist 1–2 MB groß; die Grenze von 32 MB je Paket ist weit weg.

## Lizenz

Apache-2.0 (siehe `LICENSE`); die Sprachdaten stammen aus tessdata_fast (Apache-2.0).
