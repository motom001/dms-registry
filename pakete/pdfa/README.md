# PDF/A

Mit dem Paket **PDF/A** legt Ablago zu jedem Dokument zusätzlich eine **Archivfassung** ab: ein durchsuchbares **PDF/A** – das Format für die **Langzeitaufbewahrung**. Das Original bleibt unverändert das Dokument; die Archivfassung kommt dazu. So nimmt dir Ablago die Umwandlung ab, die sonst irgendwann nötig wird, wenn ein Format oder Programm aus der Mode kommt. Das gilt auch für **E-Mails** (`.eml`, `.msg`): Das Paket setzt sie zu Seiten, die du lesen kannst wie einen Brief (siehe [E-Mails](#e-mails)).

Es läuft im **Paket-Läufer** von Ablago: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit.

## Was ist PDF/A – und warum hilft es?

Ein PDF kann vieles enthalten, was ein Programm in zehn oder zwanzig Jahren vielleicht nicht mehr richtig zeigt: Schriften, die nur auf dem Rechner des Absenders lagen, Farben ohne feste Bedeutung, Skripte, Verweise auf Inhalte im Internet. **PDF/A** ist ein PDF mit strengen Regeln (ISO 19005): Alles, was zum Anzeigen nötig ist, steckt **in der Datei selbst** – Schriften, Farbprofil, Bilder –, und es gibt nichts, was beim Öffnen etwas ausführt oder nachlädt. Ein PDF/A sieht deshalb auch in vielen Jahren noch genauso aus wie heute. Behörden, Archive und Bibliotheken bewahren Dokumente aus diesem Grund als PDF/A auf.

Das Paket schreibt **PDF/A-2b** – „b“ heißt: Das Aussehen ist gesichert. Dazu kommt eine **unsichtbare Textebene genau auf den Wörtern**: Du kannst in der Archivfassung suchen, Text markieren und kopieren, und die Markierung liegt auf dem gedruckten Wort – auch bei Scans und Fotos.

## So arbeitet es

1. Ein Dokument kommt in Ablago. Sobald sein **Volltext feststeht** – bei Scans und Fotos also nach der Texterkennung –, meldet Ablago es dem Paket (Ereignis **Archivfassung erstellen**). Am Dokument steht so lange „Archivfassung wird erstellt“.
2. Das Paket holt die **Wortpositionen** (wo jedes Wort auf der Seite steht) und baut daraus das PDF/A (E-Mails ohne Wortpositionen, siehe unten):

   | Dokument | Archivfassung |
   | --- | --- |
   | **JPEG** (Foto, Scan) | Das Bild kommt **unverändert** hinein (keine zweite JPEG-Kompression, kein Qualitätsverlust); nur Metadaten wie Aufnahmeort und Gerät (EXIF) fallen weg. Hochkant fotografierte Bilder stehen aufrecht, wie Ablago sie zeigt. JPEG in CMYK und andere seltene Varianten rechnet es in sRGB um. |
   | **PNG** (Bildschirmfoto, Grafik) | **verlustfrei**; Durchsichtiges kommt auf Weiß |
   | **PDF** (Scan, Online-Rechnung, Formular) | jede Seite als **Bild mit 300 dpi** (ab 51 Seiten 200 dpi, ab 201 Seiten 150 dpi), darüber die Textebene. Farbige Seiten bleiben **farbig** (Logos, Stempel, Markierungen), graue Seiten werden als Graustufenbild abgelegt und damit nicht größer. Formularfelder sind damit eingefroren (die Werte sind zu sehen, ausfüllen lässt sich nichts mehr); JavaScript, Aktionen und Verweise auf externe Inhalte kommen nie mit. |
   | **TIFF, WebP, GIF, BMP** | aus der Lesefassung des Pakets [Bildformate](../bildformate/), wie oben |
   | **E-Mail** (`.eml`, Outlook `.msg`) | als Text gesetzt, mit Kopfblock, Bildern aus der Mail und der Liste der Anhänge – siehe [E-Mails](#e-mails) |

   Die Seitengröße kommt bei Bildern aus ihrer Auflösung; fehlt sie oder ist sie kleiner als 100 dpi (Handyfotos schreiben 72 dpi hinein), gilt 300 dpi.
3. Ablago prüft die Archivfassung (PDF, PDF/A-Kennung, nichts Externes), legt sie neben das Original und zeigt sie an: „Ansicht: Archivfassung (PDF/A)“ mit **Original anzeigen**. Die Historie der Mappe vermerkt sie („JPEG → PDF/A-2b (PDF/A 1.0.0)“). Herunterladen und Weitergeben bieten die Wahl zwischen Archivfassung und Original.
4. **Vorhandene Dokumente:** Beim Installieren gibt Ablago alle vorhandenen Dokumente mit fertigem Volltext an das Paket. Nach einer neuen Version, einer Änderung am PDF oder *Volltext neu erzeugen* entsteht die Archivfassung neu.
5. **Sicherung:** Original **und** Archivfassung kommen in die Sicherung und in den Vollexport (`<Datei>.pdfa.pdf`).

Was Ablago selbst erledigt: Verschlüsselte PDFs bekommen keine Archivfassung (der Grund steht am Dokument). Ein PDF, das schon gültiges PDF/A ist, gilt selbst als Archivfassung. Bei **digital signierten** PDFs entsteht die Archivfassung trotzdem – sie trägt die Signatur nicht, und Ablago zeigt den Hinweis, die Signatur am Original zu prüfen. Bei **E-Rechnungen** (ZUGFeRD, Factur-X) bleibt die XML im Original; Herunterladen gibt dort das Original zuerst.

Kann das Paket keine Archivfassung bauen, steht der Grund am Dokument und in **Werkbank → Texterkennung → Archivfassung (PDF/A)**, z. B.:

- „Wortpositionen fehlen – Texterkennung aktualisieren (Paket Texterkennung ab 2.2.0) und den Volltext neu erzeugen“: Ein Scan wurde von einer älteren Texterkennung gelesen. Das Paket legt den Text dann **nicht ungefähr** ab, sondern wartet, bis die Wortpositionen da sind (Texterkennung aktualisieren, dann **Werkbank → Wartungsoperationen → Volltext neu erzeugen**).
- „Das Dokument ist zu lang für einen Durchgang“, „größer als 100 MB“.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappen selbst liest das Paket nicht.
- **Dokumente lesen** – es liest die Datei, die Seitenbilder und die Wortpositionen. Dokumente ändert, ersetzt oder löscht es nicht.
- **Archivfassung (PDF/A) ablegen – das Paket liest Dokumente mit ihrem Volltext und den Wortpositionen und legt daneben ein durchsuchbares PDF/A ab; das Original bleibt unverändert, ändern, ersetzen oder löschen kann es nichts (dms:archivfassung): PDF, JPEG, PNG, TIFF, WebP, GIF, BMP, E-Mails (`message/rfc822`, `application/vnd.ms-outlook`, `application/octet-stream` mit Endung `.eml`/`.msg`)** – Ablago gibt diese Dokumente an das Paket und nimmt die Archivfassung an. Die Zeitzone der Ablage (Werkbank → Region) für das Datum im Kopf der E-Mail bringt Ablago im Ereignis mit.
- **Kein Netz.** Alles geschieht im Paket; Farbprofil und Schriften bringt es mit. Auch Bilder, auf die eine E-Mail im Internet verweist, lädt es **nie**.
- Es reagiert auf **Ein Dokument mit fertigem Volltext braucht seine Archivfassung (PDF/A)** (`datei.archivfassung`).

## Einstellungen

Unter **Werkbank → Pakete → PDF/A → Einstellungen** kreuzt du unter „Archivfassung anlegen für …“ an, was eine Archivfassung bekommt (Ablago ab 0.176.0):

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| PDFs mit Text | an | z. B. Online-Rechnungen, Kontoauszüge. Aus spart Platz; diese PDFs bleiben dann nur im Original. |
| Gescannte PDFs | an | PDFs ohne Text oder nur mit Text auf einzelnen Seiten. Den Text liefert das Paket Texterkennung. |
| Fotos und Bilder | an | Immer .jpg, .jpeg und .png; mit dem Paket Bildformate auch .tif, .tiff, .webp, .gif und .bmp. Den Text liefert das Paket Texterkennung. |
| E-Mails (.eml, .msg) | an | Kopf, Text und Bilder der Mail als Seiten; Anhänge nur als Liste (sie bleiben im Original). Bilder aus dem Internet werden nie geladen. Ablago mit der Art `emails` (DMS #946). |

Was du abwählst, steht am Dokument als „ausgelassen – laut Einstellung“. Kreuzt du eine Art später an, holt Ablago die Dokumente nach.

Die PDF/A-Stufe ist fest (**PDF/A-2b**) und nicht wählbar: Sie passt für alles, was ein Haushalt aufbewahrt, und jede weitere Stufe müsste dauerhaft gepflegt und geprüft werden.

## E-Mails

Eine Mail (`.eml` oder Outlook `.msg`) setzt das Paket **selbst** zu Seiten (A4) – ohne Browser, ohne Netz, abgeschottet im Paket-Läufer. Ob es eine Mail ist, entscheidet der Inhalt, nicht der Name.

- **Kopfblock** wie ein Briefkopf: Betreff groß, darunter **Von, An, Cc und Datum** – das Datum in der **Zeitzone der Ablage** (Werkbank → Einstellungen → Region) und deutsch geschrieben, z. B. „02.11.2026, 10:15 Uhr“.
- **Text:** Klartext mit Umbruch an Wortgrenzen, Zitate (`>`) eingerückt mit Strich. Gibt es eine HTML-Fassung (oder nur HTML), nimmt das Paket sie und setzt **Absätze, Überschriften, Listen, Fett, Kursiv, einfache Tabellen und Zeilenumbrüche**; Links stehen als Text mit der Adresse in Klammern. Skripte, Stile, Formulare und Knöpfe gibt es nicht.
- **Bilder in der Mail** (`cid:`, auch `data:`) stehen als JPEG, PNG oder GIF an ihrer Stelle, höchstens so breit wie die Seite.
- **Bilder aus dem Internet** (`http…`) werden **nie geladen** – an ihrer Stelle steht ein kleiner Kasten „externes Bild nicht geladen“. Zählpixel, mit denen Absender sehen wollen, ob eine Mail geöffnet wurde, bleiben so wirkungslos (für die ganz kleinen gibt es nicht einmal einen Kasten).
- **Anhänge** stehen am Ende als Liste mit Name, Art und Größe. Ihr Inhalt kommt nicht in die Archivfassung (PDF/A-2b erlaubt keine eingebetteten Dateien; das Original mit allen Anhängen bleibt ja erhalten). **Weitergeleitete Mails** (als Anhang oder eingebettet) folgen darunter mit eigenem Kopfblock, bis zur dritten Ebene.
- **Verschlüsselte Teile** (S/MIME, PGP/MIME) bleiben verschlüsselt; dort steht „verschlüsselter Teil – nicht lesbar“.
- **Schrift:** Noto Sans, eingebettet nur mit den Zeichen, die vorkommen – der Text ist sichtbar, durchsuchbar und kopierbar. Umlaute, die europäischen Schriften, Griechisch und Kyrillisch werden richtig gezeigt; was die Schrift nicht kann (z. B. chinesische Schriftzeichen, manche Symbole), steht als Rahmen „□“ da, nie als „?“.
- Oben auf jeder Seite steht der Betreff, unten „Seite 1 von 3“.

Am Dokument steht danach z. B. „PDF/A-2b, 2 Seiten, 45 KB; E-Mail mit Kopf und Text, 1 Bild, 3 Anhänge als Liste; 1 externes Bild nicht geladen“.

## Platz und Qualität

- **Fotos und Bild-Scans** (JPEG, PNG): Die Archivfassung ist kaum größer als das Original (Textebene, Schrift und Farbprofil: einige KB).
- **PDFs** werden neu als Bild aufgebaut. Bei **Scans** ist das fast verlustfrei; bei **PDFs aus dem Computer** (Online-Rechnung, Kontoauszug) wird die Archivfassung **größer** als das Original (je Seite etwa 100–400 KB statt weniger KB), etwas **unschärfer** als die Vektorschrift. Farbige Seiten werden etwa ein Viertel größer als graue. Der Text bleibt über die Textebene genau durchsuchbar, und das Original bleibt daneben erhalten. Wer Platz sparen will, wählt „PDFs mit Text“ ab.

Gemessen am 03.11.2026 (PDFs am 12.11.2026, mit Farbe) auf amd64 mit 2 Kernen, Node 22, mit den erfundenen Testdateien aus `tests/beispiele.py` (`node tests/modul_test.mjs <ordner> --messen`; bei PDFs mit dem Rendern der Seiten durch Poppler wie in Ablago):

| Dokument | Original | Archivfassung | Zeit | Speicher |
| --- | ---: | ---: | ---: | ---: |
| Foto, JPEG 1240 × 1754 | 84 KB | 88 KB | 0,01 s | 3 MB |
| CMYK-JPEG 620 × 877 (umgerechnet) | 86 KB | 25 KB | 0,1 s | 6 MB |
| PNG 1240 × 1754, Graustufen | 28 KB | 31 KB | 0,1 s | 13 MB |
| Online-Rechnung, 2 Seiten A4 (wenig Text, farbiges Logo) | 1 KB | 217 KB (grau: 181 KB) | 0,5 s | 55 MB |
| Scan-PDF, 2 Seiten A4, grau | 97 KB | 178 KB | 0,7 s | 46 MB |
| Scan-PDF, 2 Seiten A4, Seite 1 farbig | 113 KB | 190 KB | 0,7 s | 55 MB |
| Prospekt, 1 Seite A4 ganz farbig | 332 KB | 224 KB | 0,4 s | 54 MB |
| PDF mit 60 Seiten (200 dpi, farbiges Logo) | 23 KB | 2,2 MB (grau: 1,7 MB) | 7,2 s | 61 MB |

Farbige Seiten brauchen gegenüber Graustufen etwa 25 MB mehr Speicher und rund die Hälfte mehr Zeit; die Grenzen des Läufers (256 MB, 120 s) reichen weiter. Die Auflösungsstufen (300/200/150 dpi) bleiben deshalb gleich. Größere Seiten als A3 (Pläne) holt das Paket in Farbe mit weniger dpi, damit das Bild in den Speicher passt.

Das Modul ist 0,7 MB groß. Eine E-Mail mit einer Seite wird als Archivfassung etwa 30–50 KB groß (die Teilmengen der Schriften stecken darin), dazu kommen ihre Bilder.

E-Mails aus den Testdateien (`tests/beispiele.py`): eine Seite in 10–25 ms, die 8 Seiten lange Mail in rund 40 ms, je unter 8 MB Speicher.

## Grenzen

- Eine Archivfassung entsteht in **einem Aufruf** des Läufers (höchstens 100 Sekunden) – ein halbes PDF lässt sich nicht als Zwischenstand weitergeben. Sehr lange PDFs (mehrere hundert Seiten) bekommen deshalb unter Umständen keine; der Grund steht am Dokument.
- Höchstens 1000 Seiten und 100 MB je Archivfassung (Grenze von Ablago); Bilder, die das Paket dekodieren muss (PNG, CMYK-JPEG), höchstens 20 Millionen Bildpunkte.
- **Vorhandene Archivfassungen** von PDFs bleiben grau, bis sie neu entstehen – z. B. wenn sich das Original oder sein Text ändert. Ein Update des Pakets erstellt sie nicht neu.
- **E-Mails** (Stufe 1): HTML wird vereinfacht gesetzt – keine Spalten, Farben oder Schriften aus dem Layout der Mail, Tabellen mit mehr als sechs Spalten und verschachtelte Tabellen werden nacheinander gesetzt. Eine bessere HTML-Darstellung folgt mit Stufe 2 ([dms-registry #144](https://github.com/motom001/dms-registry/issues/144)). Fotos in Mails stehen so, wie sie gespeichert sind (EXIF-Ausrichtung wird bei Mails nicht ausgewertet). Fehlt die Zeitzone im Ereignis, gilt Europe/Berlin; kennt das Paket den Namen der Zeitzone nicht, zeigt es UTC mit dem Zusatz „(UTC)“.
- Scans brauchen die **Wortpositionen** der Texterkennung – das Paket [Texterkennung](../texterkennung/) ab 2.2.0. Bei sehr langen Scans (über etwa 150 dicht beschriebene Seiten) schickt die Texterkennung sie nicht für alle Seiten; dann gibt es keine Archivfassung.

## Voraussetzungen

- Ablago **0.149.0** oder neuer (Schnittstelle „Archivfassung ablegen“, `dms:archivfassung`).
- Für Scans und Fotos: das Paket [Texterkennung](../texterkennung/) **2.2.0** oder neuer (Wortpositionen). Ohne Text bekommt ein Scan keine Archivfassung.
- Für TIFF, WebP, GIF und BMP: das Paket [Bildformate](../bildformate/).
- Für E-Mails: Ablago mit der Archiv-Art `emails` (ab 0.221.0, [DMS #946](https://github.com/motom001/dms/issues/946)). Das Paket [Office und E-Mail](../office_email/) braucht es dafür nicht.

## Warum so gebaut? (Werkzeug und Lizenz)

Das Paket bringt einen **eigenen kleinen PDF/A-Schreiber** mit ([`code/pdfa.h`](code/pdfa.h), gut 400 Zeilen): je Seite ein Bild, darüber unsichtbarer Text (Darstellungsart 3) an den Wortpositionen, XMP-Metadaten mit der PDF/A-Kennung, OutputIntent mit eingebettetem sRGB-Profil, eingebettete Schrift, Dokument-ID.

- **Kein Ghostscript, kein MuPDF:** beide stehen unter AGPL-3.0 und passen nicht zu einem Paket unter Apache-2.0; Ghostscript wäre als WebAssembly zudem viel größer als die Grenze von 32 MB.
- **Keine „Bereinigung“ des Original-PDFs** (wie mit qpdf): Ein beliebiges PDF wird erst PDF/A, wenn man Schriften nachbettet, Farben umrechnet, Transparenz und Formulare auflöst – das geht nur mit einem vollständigen PDF-Renderer. Das Rastern über das Seitenbild von Ablago (Poppler, im Kern ohnehin da) ergibt für **jedes** PDF eine gültige Archivfassung, ohne Rendering im Paket.
- **Schrift der Textebene:** GlyphLessFont aus Tesseract (Apache-2.0, 572 Bytes) – eine Schrift ohne sichtbare Zeichen; die Breite jedes Worts stellt die horizontale Skalierung ein, so liegt die Markierung genau auf dem Wort.
- **Farbprofil:** sRGB aus [Compact-ICC-Profiles](https://github.com/saucecontrol/Compact-ICC-Profiles) (CC0-1.0, 736 Bytes, ICC v2).
- **E-Mails ohne Browser:** Ein eigener kleiner Satz ([`code/satz.h`](code/satz.h), [`code/mailsatz.h`](code/mailsatz.h)) statt eines HTML-Renderers: Er kann weniger, lädt aber garantiert nichts nach und passt in den Läufer. Die Schrift **Noto Sans** (SIL OFL 1.1) wird als **Teilmenge** eingebettet ([`code/schrift.h`](code/schrift.h)): Die Glyphen-Nummern bleiben, unbenutzte Glyphen werden leer – so stimmen die Breiten im PDF genau mit der Schrift überein, wie PDF/A es verlangt. Kein Kerning, keine Ligaturen: Der Text bleibt so suchbar, wie er gesetzt ist.
- **Mail-Zerleger gemeinsam:** Die Mails liest derselbe Code wie im Paket [Office und E-Mail](../office_email/) (`gemeinsam/mail/` im Repository) – beide verstehen eine Mail also gleich.

Die Konformität prüft **veraPDF** (Profil PDF/A-2b) in der CI an allen Testdateien (`tests/verapdf.sh`, feste Version mit Prüfsumme); im Paket selbst steckt veraPDF nicht.

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/pdfa.cpp`](code/pdfa.cpp) | das Modul (Ablago-Paket-ABI 1): Ereignis → schon vorhanden? → Wortpositionen → Bild bzw. Seitenbilder über die API → PDF/A → `PUT /dokumente/{id}/archivfassung` |
| [`code/pdfa.h`](code/pdfa.h) | ohne Bibliotheken außer zlib: PDF/A-2b schreiben (Seite für Seite), Textebene, JPEG-Kopf lesen und Metadaten entfernen, EXIF-Ausrichtung, PNG-Prädiktoren; Test in [`tests/pdfa_test.cpp`](tests/pdfa_test.cpp) |
| [`code/satz.h`](code/satz.h) | Seiten setzen: Absätze, Zeilenumbruch, Zitate, Listen, einfache Tabellen, Bilder, Kopf- und Fußzeile; Schriften als Type0/CIDFontType2 mit Teilmenge und ToUnicode |
| [`code/mailsatz.h`](code/mailsatz.h) | eine E-Mail als Seiten: Kopfblock, Klartext, einfaches HTML, `cid:`-Bilder, Anhänge, weitergeleitete Mails, Datum in der Zeitzone der Ablage |
| [`code/schrift.h`](code/schrift.h) | TrueType lesen (cmap, hmtx, glyf) und eine Teilmenge schreiben |
| [`gemeinsam/mail/`](../../gemeinsam/mail/) | der Mail-Zerleger, gemeinsam mit „Office und E-Mail“ |
| [`code/bauen.sh`](code/bauen.sh) | Bau: zlib 1.3.1, libjpeg-turbo 3.1.2 und stb_image aus den Quellen (feste Commits, wie im Paket Bildformate), Schriften und Farbprofil mit Prüfsumme nach `code/daten/` |
| [`code/lizenzen/`](code/lizenzen/) | Lizenztexte der Bibliotheken und Daten |
| [`tests/`](tests/) | `beispiele.py` (erfundene Testdateien – E-Mails nur mit der Standardbibliothek – und Prüfung: Seiten, jedes Wort an seiner Stelle, qpdf), `modul_test.mjs` (das Modul mit einer Nachbildung von Ablago; bei Mails Text, Schriften und Bilder der Seiten), `verapdf.sh` (veraPDF, PDF/A-2b), `ci.sh` (CI), `pruefen.sh` (alles lokal) |

```sh
WASI_SDK=$(werkzeuge/wasi-sdk.sh) python3 werkzeuge/bauen.py pakete/pdfa   # beim ersten Mal einige Minuten
pakete/pdfa/tests/pruefen.sh                                               # bauen und alle Tests (mit veraPDF, braucht Java)
```

Die Schnittstelle beschreibt das Entwicklerhandbuch von Ablago unter [Archivfassung ablegen](https://help.ablago.app/entwickler/aktuell/pakete-code/#archivfassung).

## Lizenz

Apache-2.0 (siehe `LICENSE`). Im Modul und in `code/daten/` stecken fremde Bibliotheken und Daten; ihre Lizenztexte liegen unter [`code/lizenzen/`](code/lizenzen/):

| Bibliothek / Daten | Version | Lizenz |
| --- | --- | --- |
| [libjpeg-turbo](https://libjpeg-turbo.org/) | 3.1.2 | IJG und BSD-3-Clause – `libjpeg-turbo.md`, `libjpeg-turbo-ijg.txt` |
| [zlib](https://zlib.net/) | 1.3.1 | Zlib – `zlib.txt` |
| [stb_image](https://github.com/nothings/stb) | 2.30 | MIT oder Public Domain – `stb.txt` |
| GlyphLessFont (`tessdata/pdf.ttf` aus [Tesseract](https://github.com/tesseract-ocr/tesseract)) | 5.5.1 | Apache-2.0 – `glyphless-font.md` |
| sRGB-Profil (`sRGB-v2-magic.icc` aus [Compact-ICC-Profiles](https://github.com/saucecontrol/Compact-ICC-Profiles)) | Commit `bdd8466` | CC0-1.0 – `srgb-icc-cc0.txt` |
| [Noto Sans](https://notofonts.github.io/) (normal, fett, kursiv, fett-kursiv; unhinted TTF) | Commit `86ce02c` von notofonts.github.io | SIL OFL 1.1 – `noto-sans.md`, `noto-sans-ofl.txt` |

Diese Software beruht teilweise auf der Arbeit der Independent JPEG Group. – This software is based in part on the work of the Independent JPEG Group.
