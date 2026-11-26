# Änderungen

## 1.0.0

- **Erste Fassung** (dms-registry #243, Messung in #242): KI lokal – Ähnlichkeit mit dem Transformer multilingual-e5-small statt eines statischen Modells. An echten Volltexten des Satzes „Lebensläufe“ findet die Suche das richtige Dokument öfter unter den ersten 5 (70–76 statt 64 %). „Wohin gehört das?“ ist kaum besser (Prüfstand 63,2 statt 61,6 %), lässt sich aber von einem übergroßen Mappentyp seltener ablenken.
- Modell auf 8 Bit gerundet, Wortliste auf lateinische, griechische und kyrillische Schrift gekürzt (84 MB). Je Text zählen die ersten 256 Wortteile.
- Suchbegriff und Dokument mit eigenem Vorsatz (`query:` / `passage:`). Die Art kommt von Ablago (motom001/dms#1706), sonst entscheidet die Länge.
- „Wohin gehört das?“ wie KI lokal – Ähnlichkeit 1.2.0, Schwellen an dieses Modell angepasst.
- Braucht Ablago ab 0.334.0. Neben KI lokal – Ähnlichkeit wählst du in der Werkbank, welches Paket die Vektoren liefert.
