# Texterkennung – Zusatzsprache Italienisch

Dieses **Zusatzpaket** bringt dem Grundpaket [Texterkennung](../texterkennung/) (Deutsch und Englisch) Italienisch bei. Es enthält nur die Sprachdaten (`ita.traineddata` aus [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast), 2,7 MB) und ein Modul, das nichts tut.

Mit **Sprache: Automatisch** erkennt das Paket Texterkennung, wenn eine Seite italienisch ist, und liest sie dann ein zweites Mal auf Italienisch – das bessere Ergebnis gilt. Ohne dieses Zusatzpaket meldet es „Sprachdaten fehlen: ita (Zusatzpaket texterkennung_ita)“ im Protokoll des Pakets und am Ergebnis des Aufrufs.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago:

- **kein Zugriff auf Netzwerk und Internet**
- keine Rechte an Mappen und Dokumenten, keine Ereignisse

Das Paket Texterkennung liest die Sprachdaten, weil dieses Paket von ihm abhängt (Ablago ab 0.133.0: ein Paket liest die Daten der Pakete, die von ihm abhängen, als `texterkennung_ita/ita.traineddata`). Wird das Zusatzpaket installiert oder entfernt, lädt der Paket-Läufer die Texterkennung neu – du musst nichts weiter tun. Dokumente, die schon ohne Italienisch erkannt wurden, erkennt **Werkbank → Wartungsoperationen → Volltext neu erzeugen → Für alle Dokumente** neu.

## Voraussetzungen

- Ablago **0.133.0** oder neuer
- Paket **Texterkennung 2.0.0** oder neuer (kommt als Abhängigkeit mit)

## Lizenz

Apache-2.0 (siehe `LICENSE`); die Sprachdaten stammen aus tessdata_fast (Apache-2.0).
