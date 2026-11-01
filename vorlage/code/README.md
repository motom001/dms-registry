# Code

Nur für Pakete mit Code (DMS ab 0.88.0) – bei Paketen ohne Code löschst du diesen Ordner und `code:` im Manifest.

- Der Code wird zu **WebAssembly** gebaut, und zwar **von der CI aus dem Quellcode hier**: `code/bauen.sh` erzeugt `code/modul.wasm` (und legt Daten für das Modul nach `code/daten/`). Beides gehört nicht ins Repository; fertige `.wasm`-Dateien nimmt die Registry nicht an.
- Das DMS führt das Modul im **Paket-Läufer** aus, abgeschottet: ohne Dateisystem, ohne Netz außer den Adressen aus `manifest.yaml`, mit Grenzen für Speicher und Rechenzeit.
- Das Paket bekommt **Ereignisse** (z. B. `dokument.hochgeladen`) und arbeitet über die **API des DMS** mit seinem eigenen Dienstkonto, also nur mit den Rechten aus `manifest.yaml`.

Die Schnittstelle (DMS-Paket-ABI 1) steht im Entwicklerhandbuch: [Pakete mit Code](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/). Beispiele: `pakete/hallo_post` (klein, C) und `pakete/texterkennung` (Tesseract, C++).

Lokal bauen und prüfen:

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/mein_paket
python3 werkzeuge/pruefen.py pakete/mein_paket
```
