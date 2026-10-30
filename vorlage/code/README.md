# Code (noch nicht verfügbar)

Pakete mit Code sind geplant. Dieser Ordner zeigt, wohin der Code gehört. Bei Paketen ohne Code löschst du ihn einfach.

**So soll es werden:**
- Der Code wird zu **WebAssembly** gebaut, und zwar **von der CI aus dem Quellcode hier**. Fertige `.wasm`-Dateien werden nicht angenommen.
- Das DMS führt ihn in einem eigenen **Paket-Läufer** aus, abgeschottet: ohne Dateisystem, ohne Netz außer den Adressen aus `manifest.yaml`, mit Grenzen für Speicher und Rechenzeit.
- Das Paket bekommt **Ereignisse**, z. B. `dokument.hochgeladen` (nicht blockierend). Es arbeitet über die **API des DMS** mit dem Schlüssel seines eigenen Dienstkontos, also nur mit den Rechten aus `manifest.yaml`.
- Sprachen: Rust, Go, C/C++, AssemblyScript, JavaScript.

Die genaue Schnittstelle (Funktionen, Ereignisse, Beispiele je Sprache) kommt mit dem Paket-Läufer ins DMS und hierher.
