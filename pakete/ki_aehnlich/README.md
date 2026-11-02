# KI lokal – Ähnlichkeit

Das Paket **KI lokal – Ähnlichkeit** lässt das DMS **ähnliche Dokumente** finden und **mit eigenen Worten** suchen: „Rechnung für die Heizung“ findet so auch die Mappe mit „Wartung Gastherme“, obwohl kein Wort übereinstimmt. Es rechnet mit einem kleinen mehrsprachigen Embedding-Modell im **Paket-Läufer** des DMS – abgeschottet, **ohne Netz** und ohne zusätzlichen Dienst. Deine Daten verlassen das DMS nicht.

Im DMS siehst du danach:

- an jeder Mappe mit Dokumenten **„Ähnliche Dokumente“** aus anderen Mappen,
- in der Suche der Startseite mit **„auch in Dokumenten“** zusätzlich **„Ähnliche Treffer“** mit dem Kennzeichen **ähnlich**,
- unter **Werkbank → Pakete → KI lokal – Ähnlichkeit** den Abschnitt **Ähnlichkeit**: wie viele Dokumente schon berechnet sind, die Einstellung „Ähnliche Treffer in der Suche zeigen“ und **Neu berechnen**.

Jeder sieht nur Mappen, die er lesen darf. Was die KI tut, ist ein Vorschlag: Sie ändert keine Mappe und kein Dokument.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; das Paket liest nur deren Volltext.
- **Dokumente lesen** – den Volltext eines Dokuments. Dateien und Volltext ändert es nicht.
- **Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)** – zu jedem Dokument eine Liste von Zahlen, die seinen Inhalt beschreibt. Das DMS vergleicht sie; die Suche fragt das Paket nach dem Vektor des Suchbegriffs.
- **kein Zugriff auf Netzwerk und Internet.** Das Modell liegt im Paket.
- Es reagiert auf **Der Volltext eines Dokuments ist da** – für neue Dokumente und, gedrosselt, für den Bestand.

**Speicher und Zeit:** Das Paket kommt mit den Standardgrenzen des Läufers aus (256 MB, 2 Minuten je Aufruf) und verlangt deshalb keine höheren. Ein Aufruf braucht etwa 31 MB, davon 28 MB für das Modell (siehe [Messung](#messung)).

## So arbeitet es

1. Steht der Volltext eines Dokuments fest (eingebaute Texterkennung, Textebene des PDFs oder ein Paket wie **Texterkennung**), holt das Paket ihn, zerlegt ihn in Wortteile (Tokens) und bildet den Mittelwert ihrer Vektoren. Den Vektor legt es im DMS ab.
2. Den **Bestand** schickt das DMS nach der Installation gedrosselt nach (alle 30 Sekunden bis zu 50 Dokumente, solange das Paket nichts anderes zu tun hat). Den Fortschritt zeigt die Werkbank.
3. In der Suche fragt das DMS das Paket nach dem Vektor des Suchbegriffs (höchstens 1,5 Sekunden) und vergleicht ihn mit den gespeicherten.

Berücksichtigt wird höchstens der erste Megabyte Volltext eines Dokuments.

## Das Modell

[static-similarity-mrl-multilingual-v1](https://huggingface.co/sentence-transformers/static-similarity-mrl-multilingual-v1) von sentence-transformers, **Apache-2.0**, ohne Nutzungsbeschränkungen. Es ist ein *statisches* Embedding-Modell: je Wortteil ein fester Vektor, der Text ist ihr Mittelwert. Zur Laufzeit rechnet kein neuronales Netz – deshalb ist es in WebAssembly ohne Threads und ohne Grafikkarte schnell genug. Es kennt 50 Sprachen, darunter Deutsch und Englisch, und ist auf Ähnlichkeit von Texten trainiert (Matryoshka: die ersten Dimensionen allein taugen schon).

Im Paket stecken die ersten **256 von 1024 Dimensionen**, auf 8 Bit gerundet: 28 MB statt 433 MB. Das passt unter die Grenze von 32 MB je Paket.

**Warum nicht ein anderes Modell?**

| Modell | Lizenz | Größe (8 Bit) | warum nicht |
| --- | --- | --- | --- |
| multilingual-e5-small (Transformer) | MIT | ≈ 118 MB | zu groß für 32 MB; ein Transformer in WebAssembly ohne Threads rechnet je Dokument Sekunden |
| paraphrase-multilingual-MiniLM-L12-v2 | Apache-2.0 | ≈ 118 MB | wie oben |
| all-MiniLM-L6-v2, gte-small | Apache-2.0 / MIT | 23–34 MB | nur Englisch |
| potion-multilingual-128M (statisch) | MIT | ≈ 128 MB | 500 000 Wortteile – zu groß |
| **static-similarity-mrl-multilingual-v1** | **Apache-2.0** | **28 MB** (256 Dim.) | gewählt |

**Grenzen:** Ein statisches Modell achtet nicht auf die Reihenfolge der Wörter und erreicht nicht ganz die Qualität eines Transformers wie multilingual-e5-small. Die Modellkarte nennt es ausdrücklich für Ähnlichkeit, nicht für Suche über lange Dokumente. Für „ähnliche Dokumente“ und „mit eigenen Worten suchen“ im Haushalt reicht das; für Fragen an die Ablage kommt Stufe 2 (Adapter zu einem lokalen KI-Dienst, #45).

## Messung

Gemessen mit `tests/modul_test.mjs` und im Paket-Läufer des DMS (DMS 0.122.0, Standardgrenzen) auf **amd64 mit 2 Kernen** – mit einem Zufallsmodell gleicher Größe (105 879 Wortteile × 256), denn die Rechenzeit hängt nicht von den Zahlen ab:

| | Modul allein | im Paket-Läufer (mit Start des Workers und Laden des Modells) |
| --- | --- | --- |
| Vektor eines Suchbegriffs | 50 ms | ≈ 200 ms; die ganze Suche mit Ähnlichkeit 0,2–0,5 s |
| Dokument mit 49 000 Zeichen | 60–85 ms | ≈ 230 ms |
| Speicher je Aufruf | 30 MB | 31 MB |

Auf einem **Intel N100** erwarten wir ähnliche Werte, also deutlich unter einer Sekunde für den Suchbegriff – gemessen ist das noch nicht. Messungen auf **N100, Raspberry Pi 5 und einem NAS** stehen noch aus und kommen hier dazu. Wie gut das echte Modell auf Deutsch trennt, prüft die CI nach jedem Bau (`tests/ci.sh`, z. B. „Rechnung für die Heizung“ näher an „Wartung der Gastherme“ als an „Kündigung des Handyvertrags“).

## Voraussetzungen

- DMS **0.122.0** oder neuer (Schnittstelle `dms:vektoren`, Ereignis „Der Volltext eines Dokuments ist da“).
- Dokumente mit Volltext – ohne Volltext gibt es keinen Vektor.

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/aehnlich.cpp`](code/aehnlich.cpp) | das Modul (DMS-Paket-ABI 1): Tokenizer (BertNormalizer, BertPreTokenizer, WordPiece wie in `tokenizers`), Mittelwert der Vektoren, Ereignis und Aktion `dms:vektor` |
| [`code/umwandeln.py`](code/umwandeln.py) | beim Bau: Modell und Tokenizer → `code/daten/` (256 Dimensionen, 8 Bit), Zeichentabellen aus Unicode |
| [`code/bauen.sh`](code/bauen.sh) | Bau: Modul mit wasi-sdk; Modell von Hugging Face auf einem festen Commit, große Datei gegen die SHA-256 aus ihrem Git-LFS-Zeiger geprüft (feste Prüfsummen lassen sich zusätzlich eintragen) |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser (wie bei Trennblatt) |
| [`code/lizenzen/`](code/lizenzen/) | Herkunft und Lizenzen von Modell, Vokabular und Zeichentabellen |
| [`tests/`](tests/) | `pruefen.sh` ohne Netz (kleines Testmodell, Laufzeit mit Zufallsmodell), `ci.sh` mit dem echten Modell |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/ki_aehnlich   # lädt das Modell (433 MB) einmal
pakete/ki_aehnlich/tests/pruefen.sh                                                 # ohne Netz
```

Die Schnittstelle beschreibt das Entwicklerhandbuch des DMS unter [Pakete mit Code → Vektoren und Ähnlichkeit](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/#vektoren-und-ahnlichkeit).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Das Modell und sein Vokabular stehen ebenfalls unter Apache-2.0, die Zeichentabellen stammen aus der Unicode-Datenbank – Einzelheiten in [`code/lizenzen/README.md`](code/lizenzen/README.md).
