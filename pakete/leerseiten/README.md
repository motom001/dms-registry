# Leerseiten

Beidseitig gescannte Briefe haben oft leere Rückseiten. Das Paket **Leerseiten** prüft jede Seite neuer Post und **markiert leere Seiten** – auch ohne Trennblatt. In der Post und auf der Seite *Dokument übernehmen* zeigt Ablago dann eine Seitenleiste mit allen Seiten; markierte sind blass und tragen „Leerseite – fällt beim Übernehmen weg“. Übernimmst du die Post in eine Mappe, hat das Dokument dort diese Seiten nicht mehr. **Gelöscht wird nichts:** Das Original bleibt als frühere Version am Dokument.

Das Paket läuft im **Paket-Läufer** von Ablago: abgeschottet als WebAssembly, ohne Netz.

## So geht’s

1. **Scannen** wie gewohnt, gern beidseitig – über den Eingangsordner, **+ Post** oder deinen Scanner.
2. **Post öffnen:** Über dem Dokument steht „3 leere Seiten erkannt · 3 fallen beim Übernehmen weg“, daneben die Seitenleiste.
3. **Prüfen:** Ist eine Seite doch nicht leer, wähle **Doch behalten**. Soll eine andere Seite weg (z. B. ein Deckblatt), wähle **Auch weglassen**.
4. **Übernehmen** in eine Mappe: Das Dokument dort hat die markierten Seiten nicht mehr, die Historie sagt „3 leere Seiten entfernt“, Texterkennung und Archivfassung arbeiten mit der neuen Fassung.

```
Scan mit 8 Seiten: Brief · leer · leer (Lochung) · Bleistiftnotiz · Stempel · durchscheinend · Staub · Brief
   vorsichtig → markiert 2, 3, 7
   normal     → markiert 2, 3, 6, 7
   streng     → markiert 2, 3, 4, 6, 7
```

Nichts fällt weg, solange die Post Post bleibt, beim automatischen Zuordnen und wenn alle Seiten leer sind (ein Dokument fällt nie ganz weg).

## Wann das Paket prüft

Das Paket schaut sich ein hochgeladenes Dokument an, wenn alles davon stimmt:

- Es ist ein **PDF**, **JPEG** oder **PNG** und liegt in einer **Post** mit Stand **Neu**, die **eingeht** (keine versendete E-Mail).
- Der **Kanal** der Post ist unter „Nur Post aus diesen Kanälen“ gewählt (Vorgabe: Scan, Eingangsordner, Hochgeladen), oder dort ist nichts gewählt (alle Kanäle).
- Das Dokument hat höchstens so viele Seiten wie eingestellt.

Findet es keine leere Seite, lässt es die Post, wie sie ist. Im Protokoll des Pakets steht je Seite, was es gesehen hat (Fläche der Tinte, größter Fleck, Löcher, Staub).

## Was als leer gilt

Die Erkennung schätzt zuerst den Ton des Papiers und sucht dann Flecken, die deutlich dunkler sind. Nicht als Inhalt zählen:

- **Rauschen und Staub** – sehr kleine Flecken,
- **Lochung** – runde Flecken von 4–9 mm nahe am Rand,
- **Schatten am Rand** – schmale Flecken am Bildrand, wie sie ein Einzugsscanner macht.

| Empfindlichkeit | als Inhalt zählt | gut für |
| --- | --- | --- |
| **vorsichtig** (Vorgabe) | schon schwache Spuren: Bleistiftnotiz, kleiner Stempel, durchscheinende Schrift von der Vorderseite | alle – im Zweifel bleibt eine Seite |
| **normal** | kräftigere Striche; durchscheinende Schrift zählt nicht | dünnes Papier, beidseitig bedruckte Briefe |
| **streng** | nur mehr als ein paar Striche oder kleine Flecken | sehr dünnes Papier – prüfe die Markierungen |

Im Zweifel ist eine Seite nicht leer. Lieber einmal **Auch weglassen** wählen als etwas verlieren.

## Was das Paket darf

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: Post.** Das Paket liest die Post, in die das Dokument kam. Andere Mappen sieht es nicht; ändern kann es keine Mappe.
- **Dokumente lesen.** Das Paket holt die Seiten als Graustufenbild (100 dpi). Es ändert keine Datei.
- **Markiert leere Seiten in neuer Post – löscht nichts; weggelassen werden sie erst, wenn jemand die Post in eine Mappe übernimmt (dms:leerseiten).** Die Markierung ändert weder Datei noch Post (kein „zuletzt geändert“, kein Eintrag in der Historie). Ob eine Seite wegfällt, entscheidet eine Person beim Übernehmen.
- **kein Zugriff auf Netzwerk und Internet**
- Es reagiert auf **Dokument hochgeladen**.

## Einstellungen

Unter **Werkbank → Pakete → Leerseiten → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Empfindlichkeit | vorsichtig | vorsichtig, normal oder streng (siehe oben) |
| Nur Post aus diesen Kanälen | Scan, Eingangsordner, Hochgeladen | leer = alle Kanäle; E-Mails bringen selten leere Seiten mit |
| Höchstens so viele Seiten | 100 | 1–400. Längere Dokumente prüft das Paket nicht (Zeitgrenze des Paket-Läufers). |

**Trennblatt:** Das Paket [Trennblatt](../trennblatt/) erkennt die leere Rückseite eines Trennblatts seit seiner Version 1.1.0 mit derselben Erkennung (Stufe „vorsichtig“) und lässt sie gleich beim Teilen weg. Das doppelt sich nicht: *Leerseiten* sieht danach nur noch die Seiten der Briefe.

**Ausprobieren:** Einen Reiter „Ausprobieren“ (Dokument hochladen, ohne dass sich etwas ändert) gibt es in Ablago noch nicht (dms #1004). Bis dahin: eine Probeseite als neue Post hochladen und die Markierung ansehen – solange du nicht übernimmst, ändert sich nichts.

## Voraussetzungen

- Ablago **0.255.0** oder neuer (Schnittstelle `dms:leerseiten`, Seitenleiste in der Post und auf *Dokument übernehmen*).

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/leerseiten.cpp`](code/leerseiten.cpp) | das Modul (Ablago-Paket-ABI 1): Ereignis → Post und Kanal prüfen → Seiten über die API → Erkennung → `PUT /dokumente/{id}/leerseiten` |
| [`gemeinsam/leerseite/leerseite.h`](../../gemeinsam/leerseite/leerseite.h) | die Erkennung leerer Seiten, ohne Bibliotheken – auch im Paket Trennblatt |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser (aus dem Paket Trennblatt) |
| [`code/bauen.sh`](code/bauen.sh) | Bau mit dem WASI-SDK |
| [`tests/scans.py`](tests/scans.py) | künstliche Scans (immer dieselben Bytes, nur Standardbibliothek): leer, Lochung und Schatten, Bleistiftnotiz, Stempel, durchscheinende Schrift, Staub, Briefseiten |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | das gebaute Modul in Node mit einer Nachbildung der Ablago-Importe und der API – je Empfindlichkeit, Kanal und Stand |
| [`tests/pruefen.sh`](tests/pruefen.sh), [`tests/ci.sh`](tests/ci.sh) | alles zusammen bzw. die Tests in der CI |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/leerseiten
pakete/leerseiten/tests/pruefen.sh        # braucht node und Poppler (pdftoppm, pdfinfo)
```

Die Schnittstelle beschreibt das Entwicklerhandbuch von Ablago unter [Leerseiten markieren](https://help.ablago.app/entwickler/aktuell/pakete-code/#leerseiten).

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit dem Paketnamen im Titel.

## Lizenz

Apache-2.0 (siehe `LICENSE`). Das Paket enthält keinen fremden Code.
