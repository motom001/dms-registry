# KI lokal – Ähnlichkeit Stufe 2

Das Paket **KI lokal – Ähnlichkeit Stufe 2** kann dasselbe wie [KI lokal – Ähnlichkeit](../ki_aehnlich/README.md): **ähnliche Dokumente** finden, **mit eigenen Worten** suchen und bei neuer Post vorschlagen, **wohin sie gehört**. Es rechnet aber mit einem **genaueren Modell** (dem Transformer multilingual-e5-small statt eines statischen Modells). Bei der Suche findet es das richtige Dokument deutlich öfter, und es ordnet neue Post besser zu. Dafür braucht es mehr Rechenzeit. Auch dieses Paket rechnet im **Paket-Läufer** von Ablago, **ohne Netz** und ohne zusätzlichen Dienst. Deine Daten verlassen Ablago nicht.

**Nimm entweder dieses Paket oder KI lokal – Ähnlichkeit, nicht beide.** Solange Ablago noch keine Wahl dafür hat (motom001/dms#1707), nimmt es bei zwei installierten Paketen das erste nach Id, also KI lokal – Ähnlichkeit.

| | KI lokal – Ähnlichkeit | **Stufe 2** |
| --- | --- | --- |
| Suche: richtiges Dokument unter den ersten 5 | 62 % | **93 %** |
| „Wohin gehört das?“: richtiger Mappentyp vorn | 59 % | **72 %** |
| dazu 200 Kontoauszüge: richtig / Kontoauszug fälschlich vorn | 51 % / 80 | **68 % / 16** |
| Rechenzeit je Dokument (PC, im Modul, mit Laden des Modells) | unter 0,1 s | 0,2–0,8 s |
| Suchbegriff | unter 0,1 s | ≈ 0,1 s |
| Größe | 28 MB | 84 MB |

Gemessen am privaten Satz „Lebensläufe“ (526 Dokumente aus elf Haushalten, siehe [Messung](#messung)).

**Wann Stufe 2?** Wenn Ablago auf einem PC, einem NAS mit x86-Prozessor oder einem Raspberry Pi 5 läuft und dir die Suche „mit eigenen Worten“ wichtig ist. Beim Installieren rechnet Ablago den Bestand einmal durch. Auf einem Raspberry Pi kann das bei einigen tausend Dokumenten Stunden dauern, die Werkbank zeigt den Fortschritt. Neue Post braucht danach je Dokument etwa eine Sekunde, im Hintergrund.

In Ablago siehst du danach dasselbe wie bei KI lokal – Ähnlichkeit:

- an jeder Mappe mit Dokumenten **„Ähnliche Dokumente“** aus anderen Mappen,
- in der Suche der Startseite mit **„auch in Dokumenten“** zusätzlich **„Ähnliche Treffer“**,
- auf der Seite **Dokument übernehmen** unter **Wohin gehört das?** einen Vorschlag für den Mappentyp,
- unter **Werkbank → Pakete → KI lokal – Ähnlichkeit Stufe 2** den Abschnitt **Ähnlichkeit** mit dem Fortschritt.

Jeder sieht nur Mappen, die er lesen darf. Was die KI tut, ist ein Vorschlag: Sie ändert keine Mappe und kein Dokument.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; das Paket liest nur deren Volltext.
- **Dokumente lesen** – den Volltext eines Dokuments. Dateien und Volltext ändert es nicht.
- **Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)** – zu jedem Dokument eine Liste von 384 Zahlen, die seinen Inhalt beschreibt.
- **Mappentyp vorschlagen („Wohin gehört das?“) (dms:klassifizieren)** – nur aus Typ und Ähnlichkeit der ähnlichsten Mappen, die Ablago mitgibt.
- **kein Zugriff auf Netzwerk und Internet.** Das Modell liegt im Paket.
- Es reagiert auf **Der Volltext eines Dokuments ist da** – für neue Dokumente und, gedrosselt, für den Bestand.

**Speicher und Zeit:** Das Paket kommt mit den Standardgrenzen des Läufers aus (256 MB, 2 Minuten je Aufruf). Ein Aufruf belegt im Modul höchstens etwa 90 MB, davon 84 MB für das Modell.

## So arbeitet es

1. Steht der Volltext eines Dokuments fest, holt das Paket ihn und zerlegt den Anfang in höchstens 256 Wortteile, das entspricht etwa einer Seite. Mit dem Vorsatz „passage: “ rechnet es ihn durch das Modell (12 Schichten) und bildet den Mittelwert. Den Vektor legt es in Ablago ab.
2. Einen Suchbegriff rechnet es mit dem Vorsatz „query: “. Ab Ablago mit motom001/dms#1706 sagt Ablago, ob ein Suchbegriff oder ein Dokument kommt. Bei älteren Versionen gilt ein Text bis 200 Zeichen als Suchbegriff.
3. **Wohin gehört das?** arbeitet wie in KI lokal – Ähnlichkeit 1.2.0 nach **Nähe statt Menge**. Die Schwellen sind an dieses Modell angepasst: ähnlich ab 0,85, sehr ähnlich ab 0,965. Ein Kosinus von 0,85 bei diesem Modell entspricht etwa 0,45 beim statischen Modell.

Weil nur der Anfang zählt, entscheidet bei langen Dokumenten die erste Seite. Für Ähnlichkeit und Mappentyp reicht das; einen Satz auf Seite 7 findet die Volltextsuche.

## Das Modell

[multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) von intfloat (Microsoft), **MIT**, ohne Nutzungsbeschränkungen; ein BERT-Transformer mit 12 Schichten, 384 breit, rund 100 Sprachen. Im Paket:

- **Gewichte auf 8 Bit gerundet**, mit einem Maßstab je Zeile; die Zwischenwerte rundet das Modul je Wortteil ebenfalls auf 8 Bit, ähnlich wie die dynamische Quantisierung von onnxruntime. Gegenüber dem Modell in 32 Bit weichen die Vektoren um weniger als 1 % ab (Kosinus ≥ 0,99, geprüft in `tests/modul_test.mjs`).
- **Wortliste gekürzt** auf lateinische, griechische und kyrillische Schrift, Ziffern, Satz- und Sonderzeichen: 151 585 von 250 002 Wortteilen. Für Texte in diesen Schriften ändert sich nichts. Chinesisch, Arabisch und andere Schriften werden zu „unbekannt“ und tragen nichts bei. So wird das Modell 84 statt 113 MB groß und bleibt im Speicher des Läufers.

**Verworfen** (dms-registry #242):

| Modell | Größe | „Wohin gehört das?“ | Suche Top 5 | warum nicht |
| --- | --- | ---: | ---: | --- |
| static-similarity-mrl, 256 Dim. | 28 MB | 59 % | 62 % | ist KI lokal – Ähnlichkeit (Stufe 1) |
| static-similarity-mrl, 1024 Dim. | 110 MB | 59 % | 68 % | kaum besser als 256 Dim. |
| potion-multilingual-128M | 130 MB | 60 % | 73 % | kaum besser, anderer Tokenizer |
| multilingual-e5-small, 512 Wortteile | 113 MB | 67 % | 91 % | 256 Wortteile sind gleich gut und halb so teuer |

## Messung

Am privaten Satz „Lebensläufe“ (motom001/demo_lebenslaeufe), offline mit den Werkzeugen aus `../ki_aehnlich/tests/modellvergleich/`:
- **„Wohin gehört das?“** wie im Lernlauf des Prüfstands: Die Dokumente kommen der Reihe nach, jedes sieht die Mappen davor.
- **Suche:** Der Titel des Dokuments ist der Suchbegriff.

Gerechnet hat dabei dieses Modul in WebAssembly mit SIMD (Node 22, amd64, 1 Kern):

| | Wert |
| --- | --- |
| Dokument mit 256 Wortteilen (eine Seite), mit Laden des Modells | 0,5–0,8 s |
| Durchschnitt über den Satz | 0,5 s |
| Suchbegriff | 0,1 s |
| Speicher des Moduls | höchstens 89 MB |

Auf einem Raspberry Pi 5 oder einem Intel N100 rechnet es voraussichtlich 2- bis 4-mal so lange. Gemessen ist das noch nicht, die Werte kommen hier dazu.

## Voraussetzungen

- Ablago ab **0.226.0** (Paket-Läufer mit `dms:vektoren`), für „Wohin gehört das?“ ab **0.329.0** (dms #1688). Mit motom001/dms#1706 unterscheidet das Paket Suchbegriff und Dokument sicher.
- Nur **eines** der Pakete KI lokal – Ähnlichkeit und KI lokal – Ähnlichkeit Stufe 2, bis Ablago die Wahl kennt (motom001/dms#1707).

## Für Entwickler

| Datei | Zweck |
| --- | --- |
| [`code/e5.cpp`](code/e5.cpp) | Modul: Tokenizer (SentencePiece/Unigram mit Normalisierung), Transformer in int8 mit SIMD, Schnittstelle |
| [`code/umwandeln.py`](code/umwandeln.py) | beim Bau: Modell und Tokenizer → `code/daten/` (Gewichte int8, gekürzte Wortliste, Normalisierungstabelle aus dem Tokenizer selbst) |
| [`code/bauen.sh`](code/bauen.sh) | Bau: Modul mit wasi-sdk (`-msimd128`), Modell von Hugging Face auf einem festen Commit, gegen die SHA-256 aus dem Git-LFS-Zeiger geprüft; Python-Pakete für den Bau aus `code/requirements.txt` mit Prüfsummen |
| [`code/lizenzen/`](code/lizenzen/) | Herkunft und Lizenzen von Modell und Tokenizer |
| [`tests/ci.sh`](tests/ci.sh), [`tests/modul_test.mjs`](tests/modul_test.mjs) | in der CI nach dem Bau: Vektoren gegen die Referenz in 32 Bit (`tests/erwartung.json`), Ähnlichkeit, Art des Textes, Ereignis, „Wohin gehört das?“, Zeit und Speicher |
| [`tests/referenz.py`](tests/referenz.py), [`tests/nativ.cpp`](tests/nativ.cpp) | Entwicklung: Referenz mit dem Tokenizer von Hugging Face und dem Modell in 32 Bit; das Modul nativ übersetzt, um Wortteile und Vektoren zu vergleichen |
