# Office und E-Mail

Das DMS liest selbst nur PDF, JPEG und PNG. Mit dem Paket **Office und E-Mail** werden auch **Word-, Excel- und PowerPoint-Dateien**, **OpenDocument** (LibreOffice), **RTF**, **Textdateien** und **E-Mails** (`.eml`, Outlook `.msg`) **im Volltext durchsuchbar**: Das Paket liest den Text aus der Datei und gibt ihn dem DMS. Die Datei selbst bleibt unverändert.

Es läuft im **Paket-Läufer** des DMS: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit. **Makros und eingebettete Objekte führt es nie aus** – es liest nur den Text.

Ein **Vorschaubild** und eine **Ansicht als PDF** bringt das Paket (noch) nicht mit; das ist ein eigener Schritt mit einem Zusatzdienst ([#72](https://github.com/motom001/dms-registry/issues/72)).

## So arbeitet es

1. Eine Datei kommt ins DMS (Hochladen, Eingangsordner, Postfach, API). Das DMS meldet sie allen Paketen (Ereignis **Dokument hochgeladen**).
2. Passt der Dateityp oder die Endung (siehe unten), holt das Paket die Datei, erkennt den Typ **am Inhalt** (nicht am Namen) und löst den Text heraus.
3. Es schreibt den Text als **Volltext** des Dokuments. Am Dokument steht dann „Texterkennung durch Paket Office und E-Mail 1.0.0“ (so nennt das DMS jeden Volltext eines Pakets); die Suche findet das Dokument mit allen Wörtern daraus.

| Datei | Was in den Volltext kommt |
| --- | --- |
| **Word** (`.docx`, `.docm`, `.dotx`) | Text mit Absätzen, Tabellen, Textfeldern und Formeln; danach Fußnoten, Endnoten, Kommentare, Kopf- und Fußzeilen. Gelöschter Text aus der Änderungsverfolgung und Feldbefehle nicht. |
| **Excel** (`.xlsx`, `.xlsm`, `.xltx`) | je Tabellenblatt sein Name und die Zellen Zeile für Zeile: Texte, Zahlen, Ergebnisse von Formeln (nicht die Formeln) |
| **PowerPoint** (`.pptx`, `.pptm`, `.ppsx`) | Folien in ihrer Reihenfolge, mit Notizen |
| **OpenDocument** (`.odt`, `.ods`, `.odp`) | Text, Tabellen mit Blattnamen, Folien |
| **RTF** (`.rtf`) | Text (ohne Schriften, Farben, Bilder, Feldbefehle) |
| **Text** (`.txt`) | der Text (UTF-8, UTF-16 oder Windows-1252) |
| **E-Mail** (`.eml`, auch aus einem mbox-Postfach) | Von, An, Cc, Datum, Betreff, der Text der Nachricht (Klartext; nur HTML: ohne Tags, Skripte und Stile), die Namen der Anhänge – und der Text von Anhängen, die das Paket liest (Office, Text, weitergeleitete E-Mails; bis zur dritten Ebene) |
| **Outlook** (`.msg`) | wie bei `.eml`: Absender, Empfänger, Datum, Betreff, Text, Anhänge |

Kann das Paket eine Datei nicht lesen, steht der Grund in der Übersicht des Pakets (**Werkbank → Pakete → Office und E-Mail → Paket-Läufer**), z. B. „Word lässt sich nicht lesen: mit einem Passwort verschlüsselt“.

## Sicherheit

Office-Dateien und E-Mails können Makros, Skripte und eingebettete Programme enthalten. Das Paket liest davon nichts aus und führt nichts aus:

- **Nur Text:** Aus Office-Dateien liest es nur die XML-Teile mit dem Text. `vbaProject.bin` (Makros in Word, Excel, PowerPoint), `Basic/` und `Scripts/` (Makros in LibreOffice) und eingebettete Objekte (`embeddings/`, OLE-Objekte) öffnet es nicht. Enthält eine Datei Makros, steht in der Übersicht „enthält Makros, nicht ausgeführt“.
- **XML ohne Nachladen:** Eine DOCTYPE-Angabe überspringt es; eigene Entitäten und externe Verweise (XXE) gelten nicht.
- **E-Mails:** HTML wird zu Text – Skripte, Stile, Bilder und Links werden nicht geladen oder ausgeführt. Verschlüsselte Teile (S/MIME, PGP/MIME) bleiben verschlüsselt.
- **ZIP-Bomben:** Jeder Teil darf entpackt höchstens 96 MB groß und höchstens 1000-mal so groß wie gepackt sein; mehr liest das Paket nicht.
- **Kein Netz, kein Dateisystem:** Der Paket-Läufer gibt dem Modul nur die API des DMS.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappen selbst liest das Paket nicht.
- **Dokumente lesen und Volltext schreiben** – es liest die Datei und schreibt den Volltext. Dateien ändert, ersetzt oder löscht es nicht. (Das DMS kennt für Pakete kein schmaleres Recht „nur Volltext schreiben“; mehr als den Volltext schreibt der Code nicht.)
- **Kein Netz.** Alles geschieht im Paket.
- Es reagiert auf **Dokument hochgeladen** (`dokument.hochgeladen`).

Einstellungen hat das Paket keine.

## Grenzen

- **Nur neue Dateien:** Das Paket liest Dateien, die nach der Installation ins DMS kommen. Dateien, die schon vorher da waren, bekommen keinen Volltext – das DMS meldet sie Paketen bisher nicht.
- **Neue Versionen:** Lädst du eine neue Version einer Word-Datei hoch, meldet das DMS sie dem Paket nicht; der Volltext der neuen Version fehlt dann.
- **Volltext neu erzeugen:** Die Wartungsoperation *Volltext neu erzeugen* in der Werkbank entfernt den Text dieser Dateien, ohne dass das Paket ihn neu schreiben kann.
- **Länge:** höchstens etwa 1,8 Millionen Zeichen je Datei (die API des DMS nimmt höchstens 2 MB je Anfrage); längere Texte kürzt das Paket („gekürzt“ in der Übersicht).
- **Größe:** Dateien über 50 MB holt das Paket nicht.
- **Alte Formate:** Word 97–2003 (`.doc`), Excel 97–2003 (`.xls`) und PowerPoint 97–2003 (`.ppt`) liest das Paket nicht. In einer E-Mail nennt es solche Anhänge nur mit Namen. Tipp: in Word, Excel oder LibreOffice öffnen und als `.docx`, `.xlsx` oder `.pptx` speichern.
- **Verschlüsselte Dateien** (Passwort beim Öffnen) liest es nicht.
- **Zeichensätze in E-Mails:** UTF-8, UTF-16, ISO-8859-1, ISO-8859-15 und Windows-1252. Andere (z. B. für Kyrillisch oder Japanisch) kommen nur lesbar an, wenn sie gültiges UTF-8 sind.
- **PDF-Anhänge** einer E-Mail liest das Paket nicht – lege sie als eigenes Dokument ab, dann liest das DMS sie selbst.

Die ersten drei Punkte brauchen eine Änderung im DMS; bis dahin hilft es, eine solche Datei noch einmal hochzuladen.

## Messung

Gemessen am 02.11.2026 auf amd64 mit 2 Kernen (nebenher belastet), Node 22, nur das Herauslösen im Modul (`node tests/modul_test.mjs <ordner> --messen`):

| Datei | Größe | Text | Zeit | Speicher |
| --- | ---: | ---: | ---: | ---: |
| Word, 30.000 Absätze (erfunden) | 94 KB | 1,8 Mio. Zeichen (gekürzt) | 0,09 s | 15 MB |
| Excel, 100.000 Zeilen × 4 Spalten (erfunden) | 1,4 MB | 1,8 Mio. Zeichen (gekürzt) | 0,13 s | 23 MB |
| PowerPoint-Vorlage aus LibreOffice, 13 Folien | 1,6 MB | 3.383 Zeichen | 0,01 s | 4 MB |
| E-Mail, 1,1 MB Text | 1,1 MB | 1,2 Mio. Zeichen | 0,05 s | 13 MB |

Das Modul ist 0,2 MB groß.

## Voraussetzungen

- DMS **0.88.0** oder neuer (Paket-Läufer, Ereignis „Dokument hochgeladen“, Volltext schreiben).

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/office_email.cpp`](code/office_email.cpp) | das Modul (DMS-Paket-ABI 1): Ereignis → Datei über die API → Text → `PUT /dokumente/{id}/volltext` |
| [`code/erkennen.h`](code/erkennen.h) | Dateityp am Inhalt erkennen, an den passenden Leser geben |
| [`code/office.h`](code/office.h), [`code/zip.h`](code/zip.h), [`code/xml.h`](code/xml.h) | Office Open XML und OpenDocument: ZIP (mit zlib), XML, Text je Format |
| [`code/mail.h`](code/mail.h), [`code/cfb.h`](code/cfb.h) | E-Mails (MIME, RFC 2047/2231) und Outlook `.msg` (Compound File) |
| [`code/rtf.h`](code/rtf.h), [`code/zeichen.h`](code/zeichen.h) | RTF; Zeichensätze, Base64, Quoted-Printable, HTML zu Text |
| [`code/bauen.sh`](code/bauen.sh) | Bau: zlib 1.3.1 aus der Quelle (fester Commit, Hash geprüft) |
| [`tests/`](tests/) | `beispiele.py` (Testdateien nur mit der Python-Standardbibliothek, mit erwarteten Texten), `modul_test.mjs` (das Modul mit einer Nachbildung des DMS), `ci.sh` (CI), `pruefen.sh` (alles lokal) |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/office_email
pakete/office_email/tests/pruefen.sh                                               # bauen und alle Tests
```

## Lizenz

Apache-2.0 (siehe `LICENSE`). Im Modul steckt [zlib](https://zlib.net/) 1.3.1 (Lizenz Zlib, Text in [`code/lizenzen/zlib.txt`](code/lizenzen/zlib.txt)); alle Leser für Office, E-Mail und RTF sind Teil dieses Pakets.
