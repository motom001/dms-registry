# Änderungen

## 1.1.0

- **Wohin gehört das?** – neue Schnittstelle `dms:klassifizieren` (dms-registry #142, Ablago #939): Auf der Seite *Dokument übernehmen* schlägt das Paket vor, zu welchem Mappentyp neue Post gehört – aus den ähnlichsten schon abgelegten Mappen („8 von 10 ähnlichen Mappen liegen in Rechnung“), bis zu drei Typen mit Sicherheit. Ablago rechnet die ähnlichen Mappen selbst – nur solche, die die Person **und** das Paket lesen dürfen, nur aus Mappentypen, die in Frage kommen und für KI-Dienste zugelassen sind – und gibt dem Paket nur Typ und Ähnlichkeit, **keine Titel und keine Inhalte**. Die Begründung nennt deshalb nur Zahlen und den Mappentyp.
- Ohne ähnliche Mappen (leere Ablage) gibt es keinen Vorschlag statt eines geratenen; bei wenigen Treffern ist die Sicherheit geringer.
- Kein Netz, kein Sprachmodell, das Modell wird dafür nicht geladen; die Grenzen des Läufers (256 MB je Aufruf) reichen.
- Braucht **Ablago ab 0.226.0**. Beim Update zeigt Ablago das neue Recht *Mappentyp vorschlagen* und lässt es dich bestätigen.

## 1.0.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.0.0

- Erste Fassung: Vektoren aus dem Volltext mit static-similarity-mrl-multilingual-v1 (256 Dimensionen, 8 Bit), Vektor eines Suchbegriffs für die Suche des DMS, Tokenizer von bert-base-multilingual-uncased in C.
