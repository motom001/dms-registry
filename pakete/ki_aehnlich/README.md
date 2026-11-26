# KI lokal – Ähnlichkeit

Das Paket **KI lokal – Ähnlichkeit** lässt Ablago **ähnliche Dokumente** finden und **mit eigenen Worten** suchen: „Rechnung für die Heizung“ findet so auch die Mappe mit „Wartung Gastherme“, obwohl kein Wort übereinstimmt. Es rechnet mit einem kleinen mehrsprachigen Embedding-Modell im **Paket-Läufer** von Ablago – abgeschottet, **ohne Netz** und ohne zusätzlichen Dienst. Deine Daten verlassen Ablago nicht.

In Ablago siehst du danach:

- an jeder Mappe mit Dokumenten **„Ähnliche Dokumente“** aus anderen Mappen,
- in der Suche der Startseite mit **„auch in Dokumenten“** zusätzlich **„Ähnliche Treffer“** mit dem Kennzeichen **ähnlich**,
- ab 1.1.0 auf der Seite **Dokument übernehmen** unter **Wohin gehört das?** einen Vorschlag für den Mappentyp aus ähnlichen, schon abgelegten Mappen (siehe *Wohin gehört das?* unten),
- unter **Werkbank → Pakete → KI lokal – Ähnlichkeit** den Abschnitt **Ähnlichkeit**: wie viele Dokumente schon berechnet sind, die Einstellung „Ähnliche Treffer in der Suche zeigen“ und **Neu berechnen**.

Jeder sieht nur Mappen, die er lesen darf. Was die KI tut, ist ein Vorschlag: Sie ändert keine Mappe und kein Dokument.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; das Paket liest nur deren Volltext.
- **Dokumente lesen** – den Volltext eines Dokuments. Dateien und Volltext ändert es nicht.
- **Vektoren zu Dokumenten speichern und ähnliche Dokumente finden (dms:vektoren)** – zu jedem Dokument eine Liste von Zahlen, die seinen Inhalt beschreibt. Ablago vergleicht sie; die Suche fragt das Paket nach dem Vektor des Suchbegriffs.
- **Mappentyp vorschlagen („Wohin gehört das?“) – nur aus dem Anfang des Dokuments und der Liste der Mappentypen, die Ablago mitgibt (dms:klassifizieren)** – neu in 1.1.0; beim Update zeigt Ablago das neue Recht und lässt es dich bestätigen.
- **kein Zugriff auf Netzwerk und Internet.** Das Modell liegt im Paket.
- Es reagiert auf **Der Volltext eines Dokuments ist da** – für neue Dokumente und, gedrosselt, für den Bestand.

**Speicher und Zeit:** Das Paket kommt mit den Standardgrenzen des Läufers aus (256 MB, 2 Minuten je Aufruf) und verlangt deshalb keine höheren. Ein Aufruf braucht etwa 31 MB, davon 28 MB für das Modell (siehe [Messung](#messung)).

## So arbeitet es

1. Steht der Volltext eines Dokuments fest (eingebaute Texterkennung, Textebene des PDFs oder ein Paket wie **Texterkennung**), holt das Paket ihn, zerlegt ihn in Wortteile (Tokens) und bildet den Mittelwert ihrer Vektoren. Den Vektor legt es in Ablago ab.
2. Den **Bestand** schickt Ablago nach der Installation gedrosselt nach (alle 30 Sekunden bis zu 50 Dokumente, solange das Paket nichts anderes zu tun hat). Den Fortschritt zeigt die Werkbank.
3. In der Suche fragt Ablago das Paket nach dem Vektor des Suchbegriffs (höchstens 1,5 Sekunden) und vergleicht ihn mit den gespeicherten.

Berücksichtigt wird höchstens der erste Megabyte Volltext eines Dokuments.

## Wohin gehört das?

Ab 1.1.0 (Ablago 0.226.0) gibt das Paket auf der Seite *Dokument übernehmen* einen ersten Hinweis, **wo vergleichbare Post liegt** – lokal, schnell und gelernt aus deiner eigenen Ablage:

1. Ablago fragt das Paket nach dem Vektor des neuen Dokuments (wie bei der Suche) und sucht die **ähnlichsten schon abgelegten Mappen** (je Mappe das beste Dokument, höchstens 10, ab der Schwelle des Modells) – **nur Mappen, die du lesen darfst und die das Paket lesen darf**, und nur aus Mappentypen, die man aus Post anlegen kann, in denen du anlegen darfst. Das Paket arbeitet nur hier, ohne Netz – die Ausnahmen für Dienste im Netz unter „Was Ablago darf“ gelten für es nicht.
2. Davon bekommt das Paket **nur den Mappentyp und das Maß der Ähnlichkeit** – keine Titel, keine Inhalte, keine Ids.
3. Das Paket ordnet nach **Nähe, nicht nach Menge** (ab 1.2.0): Je Typ zählen die drei nächsten Mappen, die nächste voll, jede weitere halb so viel; eine sehr nahe Mappe wiegt mehr als viele mittelmäßige. Typen mit sehr vielen Mappen gleicht es über deren Zahl aus (ab Ablago 0.328.0). Daraus werden bis zu drei Mappentypen. Die Sicherheit hängt davon ab, wie nah die nächste Mappe ist und wie weit der Typ vor den anderen liegt. Die Begründung sagt es in Worten: „Sehr ähnlich zu einer Mappe in Wartung“.
4. Ablago verbindet das mit seinen übrigen Hinweisen (Überschrift im Text, wiedergefundene Mappen, ein KI-Dienst) zu **einem** Vorschlag.

Gibt es noch keine ähnlichen Mappen – etwa in einer leeren Ablage –, schlägt das Paket **nichts** vor statt zu raten. Dafür lädt es das Modell nicht und braucht weder Netz noch Sprachmodell.

## Das Modell

[static-similarity-mrl-multilingual-v1](https://huggingface.co/sentence-transformers/static-similarity-mrl-multilingual-v1) von sentence-transformers, **Apache-2.0**, ohne Nutzungsbeschränkungen. Es ist ein *statisches* Embedding-Modell: je Wortteil ein fester Vektor, der Text ist ihr Mittelwert. Zur Laufzeit rechnet kein neuronales Netz – deshalb ist es in WebAssembly ohne Threads und ohne Grafikkarte schnell genug. Es kennt 50 Sprachen, darunter Deutsch und Englisch, und ist auf Ähnlichkeit von Texten trainiert (Matryoshka: die ersten Dimensionen allein taugen schon).

Im Paket stecken die ersten **256 von 1024 Dimensionen**, auf 8 Bit gerundet: 28 MB statt 433 MB. Das hält Laden und Rechnen klein, auch auf einem Raspberry Pi.

**Warum nicht ein anderes Modell?**

| Modell | Lizenz | Größe (8 Bit) | warum nicht |
| --- | --- | --- | --- |
| multilingual-e5-small (Transformer) | MIT | ≈ 113 MB (gekürzt 84 MB) | deutlich genauer, aber 5- bis 10-mal so viel Rechenzeit – als eigenes Paket **[KI lokal – Ähnlichkeit Stufe 2](../ki_aehnlich2/README.md)** |
| paraphrase-multilingual-MiniLM-L12-v2 | Apache-2.0 | ≈ 118 MB | Transformer wie e5-small, nicht besser |
| all-MiniLM-L6-v2, gte-small | Apache-2.0 / MIT | 23–34 MB | nur Englisch |
| potion-multilingual-128M (statisch) | MIT | ≈ 128 MB | kaum genauer (siehe Messung unten), 500 000 Wortteile |
| **static-similarity-mrl-multilingual-v1** | **Apache-2.0** | **28 MB** (256 Dim.) | gewählt |

**Gemessen (dms-registry #242, 26.11.2026):** am privaten Satz „Lebensläufe“ (526 Dokumente aus elf Haushalten, Mappen und Typen bekannt), offline mit `tests/modellvergleich/`. „Wohin gehört das?“ wie im Lernlauf des Prüfstands: Dokumente der Reihe nach, jedes sieht die Mappen davor; gerechnet mit diesem Paket (1.2.0), die Ähnlichkeiten der anderen Modelle auf die Verteilung des heutigen Modells umgerechnet, damit dieselben Schwellen gelten. Suche: der Titel des Dokuments als Suchbegriff, Treffer unter den ersten 5.

| Modell | Größe im Paket | nächstes Dokument, richtiger Typ | „Wohin gehört das?“ richtig vorn | dazu 200 Kontoauszüge: richtig / Kontoauszug fälschlich vorn | Suche unter den ersten 5 |
| --- | --- | ---: | ---: | ---: | ---: |
| **static-similarity-mrl, 256 Dim. (im Paket)** | **28 MB** | **64,4 %** | **59,1 %** | **50,8 % / 80** | **62,2 %** |
| static-similarity-mrl, 512 Dim. | ≈ 55 MB | 64,2 % | 59,3 % | 52,0 % / 71 | 66,2 % |
| static-similarity-mrl, 1024 Dim. | ≈ 110 MB | 65,1 % | 59,0 % | 51,6 % / 65 | 68,4 % |
| potion-multilingual-128M | ≈ 130 MB | 66,7 % | 59,9 % | 52,9 % / 62 | 72,6 % |
| multilingual-e5-small (Transformer) | ≈ 118 MB | 70,9 % | 67,2 % | 62,3 % / 25 | 91,4 % |

Die statischen Modelle liegen bei „Wohin gehört das?“ innerhalb eines Prozentpunkts; mehr Dimensionen oder potion helfen vor allem der Suche, kosten aber das Vier- bis Fünffache an Platz. Deutlich besser ist nur der Transformer multilingual-e5-small (+8 Punkte bei „Wohin gehört das?“, +29 bei der Suche), dafür mit einem Vielfachen an Rechenzeit. Deshalb bleibt dieses Paket bei static-similarity-mrl mit 256 Dimensionen – schnell auch auf schwachen Geräten –, und e5-small gibt es als eigenes Paket **[KI lokal – Ähnlichkeit Stufe 2](../ki_aehnlich2/README.md)** (#243). Sind beide installiert, wählst du in der Werkbank, welches die Vektoren liefert (ab Ablago 0.334.0).

**Grenzen:** Ein statisches Modell achtet nicht auf die Reihenfolge der Wörter und erreicht nicht ganz die Qualität eines Transformers wie multilingual-e5-small. Die Modellkarte nennt es ausdrücklich für Ähnlichkeit, nicht für Suche über lange Dokumente. Für „ähnliche Dokumente“ und „mit eigenen Worten suchen“ im Haushalt reicht das; für Fragen an die Ablage kommt Stufe 2 (Adapter zu einem lokalen KI-Dienst, #45).

## Messung

Gemessen mit `tests/modul_test.mjs` und im Paket-Läufer von Ablago (Ablago 0.122.0, Standardgrenzen) auf **amd64 mit 2 Kernen** – mit einem Zufallsmodell gleicher Größe (105 879 Wortteile × 256), denn die Rechenzeit hängt nicht von den Zahlen ab:

| | Modul allein | im Paket-Läufer (mit Start des Workers und Laden des Modells) |
| --- | --- | --- |
| Vektor eines Suchbegriffs | 50 ms | ≈ 200 ms; die ganze Suche mit Ähnlichkeit 0,2–0,5 s |
| Dokument mit 49 000 Zeichen | 60–85 ms | ≈ 230 ms |
| Speicher je Aufruf | 30 MB | 31 MB |

Auf einem **Intel N100** erwarten wir ähnliche Werte, also deutlich unter einer Sekunde für den Suchbegriff – gemessen ist das noch nicht. Messungen auf **N100, Raspberry Pi 5 und einem NAS** stehen noch aus und kommen hier dazu. Wie gut das echte Modell auf Deutsch trennt, prüft die CI nach jedem Bau (`tests/ci.sh`, z. B. „Rechnung für die Heizung“ näher an „Wartung der Gastherme“ als an „Kündigung des Handyvertrags“).

## Voraussetzungen

- Ablago **0.226.0** oder neuer (Schnittstelle `dms:klassifizieren`; seit 0.122.0 `dms:vektoren` und das Ereignis „Der Volltext eines Dokuments ist da“).
- Dokumente mit Volltext – ohne Volltext gibt es keinen Vektor.

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/aehnlich.cpp`](code/aehnlich.cpp) | das Modul (Ablago-Paket-ABI 1): Tokenizer (BertNormalizer, BertPreTokenizer, WordPiece wie in `tokenizers`), Mittelwert der Vektoren, Ereignis und Aktion `dms:vektor`, ab 1.1.0 Aktion `dms:klassifizieren` (zählt die Typen ähnlicher Mappen) |
| [`code/umwandeln.py`](code/umwandeln.py) | beim Bau: Modell und Tokenizer → `code/daten/` (256 Dimensionen, 8 Bit), Zeichentabellen aus Unicode |
| [`code/bauen.sh`](code/bauen.sh) | Bau: Modul mit wasi-sdk; Modell von Hugging Face auf einem festen Commit, große Datei gegen die SHA-256 aus ihrem Git-LFS-Zeiger geprüft (feste Prüfsummen lassen sich zusätzlich eintragen) |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser (wie bei Trennblatt) |
| [`code/lizenzen/`](code/lizenzen/) | Herkunft und Lizenzen von Modell, Vokabular und Zeichentabellen |
| [`tests/modellvergleich/`](tests/modellvergleich/) | Modellvergleich #242 am privaten Satz „Lebensläufe“ (offline, nicht in der CI) |
| [`tests/`](tests/) | `pruefen.sh` ohne Netz (kleines Testmodell, Laufzeit mit Zufallsmodell), `ci.sh` mit dem echten Modell |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/ki_aehnlich   # lädt das Modell (433 MB) einmal
pakete/ki_aehnlich/tests/pruefen.sh                                                 # ohne Netz
```

Die Schnittstelle beschreibt das Entwicklerhandbuch von Ablago unter [Pakete mit Code → Vektoren und Ähnlichkeit](https://help.ablago.app/entwickler/aktuell/pakete-code/#vektoren-und-ahnlichkeit).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Das Modell und sein Vokabular stehen ebenfalls unter Apache-2.0, die Zeichentabellen stammen aus der Unicode-Datenbank – Einzelheiten in [`code/lizenzen/README.md`](code/lizenzen/README.md).
