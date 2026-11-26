# Änderungen

## 1.0.0

- **Erste Fassung** (dms-registry #243, Messung in #242): KI lokal – Ähnlichkeit mit dem Transformer multilingual-e5-small statt eines statischen Modells. Am Satz „Lebensläufe“ findet die Suche das richtige Dokument in 93 statt 62 % unter den ersten 5, „Wohin gehört das?“ trifft den Mappentyp in 72 statt 59 %.
- Modell auf 8 Bit gerundet, Wortliste auf lateinische, griechische und kyrillische Schrift gekürzt (84 MB). Je Text zählen die ersten 256 Wortteile.
- Suchbegriff und Dokument mit eigenem Vorsatz (`query:` / `passage:`). Die Art kommt von Ablago (motom001/dms#1706), sonst entscheidet die Länge.
- „Wohin gehört das?“ wie KI lokal – Ähnlichkeit 1.2.0, Schwellen an dieses Modell angepasst.
