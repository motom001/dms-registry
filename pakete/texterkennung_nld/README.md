# Texterkennung – Zusatzsprache Niederländisch

Dieses **Zusatzpaket** bringt dem Grundpaket [Texterkennung](../texterkennung/) (Deutsch und Englisch) Niederländisch bei. Es enthält nur die Sprachdaten (`nld.traineddata` aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast), 6,1 MB) und ein Modul, das nichts tut.

Mit **Sprache: Automatisch** erkennt das Paket Texterkennung, wenn eine Seite niederländisch ist, und liest sie dann ein zweites Mal auf Niederländisch – das bessere Ergebnis gilt. Ohne dieses Zusatzpaket meldet es „Sprachdaten fehlen: nld (Zusatzpaket texterkennung_nld)“ im Protokoll des Pakets und am Ergebnis des Aufrufs.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS:

- **kein Zugriff auf Netzwerk und Internet**
- keine Rechte an Mappen und Dokumenten, keine Ereignisse

Das Paket Texterkennung liest die Sprachdaten, weil dieses Paket von ihm abhängt (DMS ab 0.133.0: ein Paket liest die Daten der Pakete, die von ihm abhängen, als `texterkennung_nld/nld.traineddata`). Wird das Zusatzpaket installiert oder entfernt, lädt der Paket-Läufer die Texterkennung neu – du musst nichts weiter tun. Dokumente, die schon ohne Niederländisch erkannt wurden, erkennt **Werkbank → Wartungsoperationen → Volltext neu erzeugen → Für alle Dokumente** neu.

## Voraussetzungen

- DMS **0.133.0** oder neuer
- Paket **Texterkennung 2.0.0** oder neuer (kommt als Abhängigkeit mit)

## Lizenz

Apache-2.0 (siehe `LICENSE`); die Sprachdaten stammen aus tessdata_fast (Apache-2.0).
