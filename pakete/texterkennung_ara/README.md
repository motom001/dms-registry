# Texterkennung – Zusatzsprache Arabisch

Dieses **Zusatzpaket** bringt dem Grundpaket [Texterkennung](../texterkennung/) (Deutsch und Englisch) Arabisch bei. Es enthält nur die Sprachdaten (`ara.traineddata` aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast), 1,4 MB) und ein Modul, das nichts tut.

Mit **Sprache: Automatisch** erkennt das Paket Texterkennung, wenn eine Seite arabisch ist, und liest sie dann ein zweites Mal auf Arabisch – das bessere Ergebnis gilt. Ohne dieses Zusatzpaket meldet es „Sprachdaten fehlen: ara (Zusatzpaket texterkennung_ara)“ im Protokoll des Pakets und am Ergebnis des Aufrufs.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago:

- **kein Zugriff auf Netzwerk und Internet**
- keine Rechte an Mappen und Dokumenten, keine Ereignisse

Das Paket Texterkennung liest die Sprachdaten, weil dieses Paket von ihm abhängt (Ablago ab 0.133.0: ein Paket liest die Daten der Pakete, die von ihm abhängen, als `texterkennung_ara/ara.traineddata`). Wird das Zusatzpaket installiert oder entfernt, lädt der Paket-Läufer die Texterkennung neu – du musst nichts weiter tun. Dokumente, die schon ohne Arabisch erkannt wurden, erkennt **Werkbank → Wartungsoperationen → Volltext neu erzeugen → Für alle Dokumente** neu.

## Voraussetzungen

- Ablago **0.133.0** oder neuer
- Paket **Texterkennung 2.0.0** oder neuer (kommt als Abhängigkeit mit)

## Lizenz

Apache-2.0 (siehe `LICENSE`); die Sprachdaten stammen aus tessdata_fast (Apache-2.0).
