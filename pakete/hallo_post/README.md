# Hallo Post

**Hallo Post** ist das kleinste Beispiel für ein Paket mit Code: Es zählt jede neue Post und nennt die Zahl, wenn du in **Werkbank → Pakete → Hallo Post → Einstellungen** auf **Wie viel Post kam bisher?** klickst. Im Alltag brauchst du es nicht – es zeigt, wie der **Paket-Läufer** des DMS arbeitet, und dient als Vorlage für eigene Pakete.

## Was das Paket darf

- Es reagiert auf **neue Post** und bekommt dabei nur die Id der Post und den Kanal.
- Es liest und ändert **keine Mappen und keine Dokumente** und hat **kein Netz**.
- Es merkt sich nur eine Zahl im eigenen Speicher des Pakets.

Bei der Installation zeigt das DMS genau das und lässt es dich bestätigen.

## Voraussetzungen

- DMS **0.88.0** oder neuer (Paket-Läufer).

## Für Entwickler

Der Code steht in [`code/hallo.c`](code/hallo.c), gebaut wird er mit [`code/bauen.sh`](code/bauen.sh) (WASI-SDK, Clang). Die Schnittstelle beschreibt das Entwicklerhandbuch des DMS unter [Pakete mit Code](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/). Lokal bauen:

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/hallo_post
```
