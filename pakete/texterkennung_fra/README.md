# Texterkennung – Französisch

Dieses **Zusatzpaket** bringt dem Paket [Texterkennung](../texterkennung/) Französisch bei. Es enthält nur die Sprachdaten (`fra.traineddata` aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast)) und ein Modul, das nichts tut.

Mit **Sprache: Automatisch** erkennt das Paket Texterkennung, wenn ein Brief französisch ist, und liest unsichere Seiten dann ein zweites Mal auf Französisch – das bessere Ergebnis gilt. Ohne dieses Zusatzpaket meldet es „Sprachdaten fehlen: fra (Zusatzpaket texterkennung_fra)“ im Protokoll des Pakets und am Ergebnis des Aufrufs.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS:

- **kein Zugriff auf Netzwerk und Internet**
- keine Rechte an Mappen und Dokumenten, keine Ereignisse

Das Paket Texterkennung liest die Sprachdaten, weil dieses Paket von ihm abhängt (DMS ab 0.133.0: ein Paket liest die Daten der Pakete, die von ihm abhängen, als `texterkennung_fra/fra.traineddata`). Wird das Zusatzpaket installiert oder entfernt, lädt der Paket-Läufer die Texterkennung neu – du musst nichts weiter tun. Dokumente, die schon ohne Französisch erkannt wurden, erkennt **Werkbank → Wartungsoperationen → Volltext neu erzeugen → Für alle Dokumente** neu.

## Voraussetzungen

- DMS **0.133.0** oder neuer
- Paket **Texterkennung 2.0.0** oder neuer (kommt als Abhängigkeit mit)

## Weitere Sprachen

Dieses Paket ist das Muster. Für eine weitere Sprache den Ordner kopieren (`texterkennung_<kennung>`, z. B. `texterkennung_tur`), in `manifest.yaml` Id und Namen und in `code/bauen.sh` `SPRACHE` und `SHA256` ändern. Kennungen wie bei Tesseract; die Spracherkennung des Pakets kennt Französisch (`fra`), Spanisch (`spa`), Italienisch (`ita`), Niederländisch (`nld`), Türkisch (`tur`), Polnisch (`pol`), Portugiesisch (`por`), Russisch (`rus`), Ukrainisch (`ukr`) und Arabisch (`ara`). Eine Sprachdatei aus tessdata_fast ist 1–2 MB groß; die Grenze von 32 MB je Paket ist weit weg.

## Lizenz

Apache-2.0 (siehe `LICENSE`); die Sprachdaten stammen aus tessdata_fast (Apache-2.0).
