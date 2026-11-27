# Änderungen

## 1.0.0

- Erste Fassung (dms-registry #294), löst **QR-Code lesen** ab.
- **Codes am Dokument** (Schnittstelle `dms:codes`, Ablago 0.336.0, dms #1723): liest alle gängigen Codes auf allen Seiten (bis 40 Seiten, etwa 20 Sekunden) – QR, Micro-QR, rMQR, Aztec, Data Matrix, PDF417, MaxiCode, EAN-8/-13, UPC-A/-E, Code 39/93/128, ITF, Codabar, GS1 DataBar – und antwortet wie die Leistung `dokument.lesen.barcode@1` mit `{ codes: [{ art, inhalt, seite }] }` in Lesereihenfolge. Feste Namen je Art (`qr`, `ean13`, `code128`, `itf`, `aztec` …) für `codeart` am Feld.
- **Visitenkarten** (`dms:erkennen`): die vCard-Vorschläge aus QR-Code lesen 1.0.2 unverändert; Meldungen nennen jetzt jede Codeart („Code gefunden (EAN-13), aber keine Visitenkarte“).
- Leser: zxing-cpp 2.3.0 (Apache-2.0, darin libzueci unter BSD-3-Clause) aus den Quellen auf festem Commit, gebaut mit WASI-SDK 33 wegen C++-Ausnahmen.
