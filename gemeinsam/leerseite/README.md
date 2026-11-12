# Leere Seite erkennen (gemeinsam)

Erkennt, ob eine gescannte Seite leer ist – ohne Bibliotheken, aus einem Graustufenbild (PGM, wie es Ablago über
`GET /dokumente/{id}/seiten/{nr}/scan` liefert). Zwei Pakete binden diesen Ordner beim Bau ein
(`-I gemeinsam/leerseite` in `code/bauen.sh`, dms #997):

| Paket | macht daraus |
| --- | --- |
| [Leerseiten](../../pakete/leerseiten/) | markiert leere Seiten in neuer Post (Schnittstelle `dms:leerseiten`) – Empfindlichkeit einstellbar |
| [Trennblatt](../../pakete/trennblatt/) | lässt die leere Rückseite eines Trennblatts beim Teilen weg – immer „vorsichtig“ |

| Datei | Inhalt |
| --- | --- |
| `leerseite.h` | `ls_pruefe(bild, breite, höhe, zeilenlänge, dpi, stufe, &befund)`: auf etwa 100 dpi verkleinern, Papierton schätzen, Tinte je Stufe, Flecken zusammenfassen; Staub, Lochung (rund, 4–9 mm, nahe am Rand) und Schatten am Rand zählen nicht. Stufen `LS_VORSICHTIG`, `LS_NORMAL`, `LS_STRENG`; `ls_stufe_von("normal")` |

Im Zweifel ist eine Seite **nicht** leer. Die Tests stehen beim Paket Leerseiten (`tests/scans.py`, `tests/modul_test.mjs`)
und beim Trennblatt (Rückseite mit Bleistiftnotiz).

Ändert sich hier etwas, baut die CI beide Pakete neu (`werkzeuge/bauen.py --geaendert`) und lässt ihre Tests laufen.
Veröffentlicht wird die Änderung mit der nächsten Version des jeweiligen Pakets.

Lizenz: Apache-2.0 wie das Repository.
