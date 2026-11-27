# Barcodes

Viele Dokumente tragen einen **Code**: der HU-Bericht einen QR-Code mit dem Link zum Digitalen Untersuchungsbericht, Rechnungen einen GiroCode, Paketscheine und Etiketten Strichcodes, Visitenkarten eine vCard. Das Paket **Barcodes** liest diese Codes und gibt sie Ablago. Ablago merkt sich die Codes am Dokument und trägt beim **Aus Dokument ausfüllen** den passenden in Felder mit der Erkennungsart **Code** ein – zuverlässiger als der erkannte Text.

Es löst das Paket **QR-Code lesen** ab (siehe [Umstieg von QR-Code lesen](#umstieg-von-qr-code-lesen)) und läuft im **Paket-Läufer** von Ablago: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit. Es braucht Ablago 0.336.0 oder neuer.

## So arbeitet es

**Codes am Dokument** (Schnittstelle `dms:codes`, dms #1723):

1. Kommt ein Dokument dazu (oder eine neue Fassung), fragt Ablago das Paket im Hintergrund nach den Codes – einmal je Datei. Bei älteren Dokumenten fragt Ablago beim ersten **Aus Dokument ausfüllen**.
2. Das Paket holt die Seiten als Bild (Scans mit 300 dpi, Fotos in voller Größe) und liest **alle Codes auf allen Seiten** (bis 40 Seiten und etwa 20 Sekunden je Dokument), Seite für Seite von oben nach unten.
3. Ablago merkt sich Art, Inhalt und Seite. Ein Feld mit der Erkennungsart **Code** nimmt den ersten Code, der zu ihm passt – etwa `codeart: qr` und ein Muster für den Link zum Digitalen Untersuchungsbericht am Feld *Digitaler Bericht* der Hauptuntersuchung (Paket Fahrzeuge).

**Visitenkarten** (Schnittstelle `dms:erkennen`, wie bisher in *QR-Code lesen*): Ist das Paket für einen Mappentyp als Erkennung gewählt, liest es beim **Aus Dokument ausfüllen** die erste **vCard** (2.1, 3.0, 4.0) und schlägt die Angaben vor. Gespeichert wird erst, wenn du bestätigst.

| aus der vCard | in das Feld mit der Erkennungsart |
| --- | --- |
| `N` (Nachname; Vorname), sonst `FN` | Vorname, Nachname |
| `ORG` (erster Teil), sonst `FN` | Name oder Firma (nur bei Mappentypen ohne Vor- und Nachname, z. B. Organisation) |
| `TITLE`, sonst `ROLE` | Funktion |
| `EMAIL` | E-Mail-Adresse |
| `TEL` (geschäftlich bevorzugt) / `TEL;TYPE=CELL` / `TEL;TYPE=FAX` | Telefon / Mobil / Fax |
| `URL` | Internetseite |
| `ADR` (geschäftlich bevorzugt) | Straße, Hausnummer (aus der Straße getrennt, wenn es ein eigenes Feld gibt), PLZ, Ort |

Ohne Visitenkarte antwortet das Paket mit dem Grund, z. B. „Code gefunden (EAN-13), aber keine Visitenkarte“, und Ablago füllt wie gewohnt **aus dem erkannten Text** aus. Fotos, Notizen und Geburtstage aus der vCard übernimmt es nie.

## Codearten

Der Name in der Spalte **Art** steht in der Antwort und am Feld (`codeart`). Ablago vergleicht ohne Groß- und Kleinschreibung und Satzzeichen (`EAN-13` = `ean13`).

| Art | Code |
| --- | --- |
| `qr`, `microqr`, `rmqr` | QR-Code, Micro-QR, rechteckiger Micro-QR (rMQR) |
| `aztec` | Aztec-Code (z. B. Fahrkarten) |
| `datamatrix` | Data Matrix (z. B. Briefmarken, Paketscheine) |
| `pdf417` | PDF417 (z. B. Bordkarten, Ausweise) |
| `maxicode` | MaxiCode (Paketdienste) |
| `ean13`, `ean8`, `upca`, `upce` | Artikelnummern (EAN, UPC) |
| `code39`, `code93`, `code128` | Code 39, Code 93, Code 128 (z. B. Sendungsnummern) |
| `itf` | Interleaved 2 of 5 |
| `codabar` | Codabar |
| `databar`, `databarexpanded`, `databarlimited` | GS1 DataBar |

**Inhalt:** wie im Code, Zeilenumbrüche bleiben erhalten (GiroCode, vCard). GS1-Codes (z. B. GS1-128) kommen lesbar mit Klammern: `(01)04012345678901(10)ABC`. Leere Codes und Inhalte über 4000 Zeichen meldet das Paket nicht – gekürzt wären sie falsch.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappen selbst liest das Paket nicht.
- **Dokumente lesen** – nur die Seitenbilder der Dokumente, die Ablago nennt. Dokumente ändert, ersetzt oder löscht es nicht.
- **Codes lesen (dms:codes)** – Ablago prüft jede Antwort mit dem Schema der Leistung `dokument.lesen.barcode@1`.
- **Felder aus Dokumenten vorschlagen (dms:erkennen)** – nur für Visitenkarten.
- **Kein Netz.** Alles geschieht im Paket.
- Es reagiert auf **keine Ereignisse**; Ablago ruft es auf.

## Einstellungen

Unter **Werkbank → Pakete → Barcodes → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Auflösung (dpi) | 300 | Für Scans (150–400). Fotos liest das Paket in ihrer vollen Größe. |
| Visitenkarten – höchstens so viele Seiten je Dokument | 2 | Vorder- und Rückseite einer Karte. Für die Codes eines Dokuments liest das Paket alle Seiten (bis 40). |

## Umstieg von QR-Code lesen

*QR-Code lesen* ist aus dem Katalog genommen; installiert läuft es weiter, bekommt aber keine Updates mehr. Ein automatischer Umzug ist nicht möglich: Pakete mit Code haben keine Inhalte, die Ablago übertragen könnte, und die Wahl der Erkennung gehört zum Mappentyp.

1. **Barcodes** installieren.
2. Überall, wo *QR-Code lesen* als Erkennung gewählt war – am Mappentyp (z. B. *Person*, *Organisation*) oder als Standard unter **Werkbank → Pakete** – **Barcodes** wählen.
3. *QR-Code lesen* entfernen. Hast du die Einstellungen geändert (Auflösung, Seiten), trage sie bei Barcodes neu ein.

## Fremde Daten

Ein Code kann alles Mögliche enthalten, auch absichtlich Präpariertes. Darum:

- Höchstens 200 Codes je Dokument, 50 je Seite, Inhalt bis 4000 Zeichen, immer gültiges UTF-8 (sonst aus Latin-1 umgewandelt); gleiche Codes auf einer Seite nur einmal.
- **Inhalte stehen nie im Protokoll** – nur Anzahl und Arten. Ein Code kann ein Zugangsschlüssel sein.
- vCard-Werte sind auf 300 Zeichen begrenzt, Steuerzeichen werden zu Leerzeichen, eine vCard hat höchstens 200 Zeilen. Ablago prüft jeden Vorschlag gegen die Feldart und speichert nichts ohne deine Bestätigung.
- Das Paket liest nur die Seitenbilder der genannten Dokumente (bei Visitenkarten höchstens drei Dokumente je Aufruf).

## Bibliotheken und Lizenzen

Das Paket steht unter **Apache-2.0**. Der Leser ist **zxing-cpp 2.3.0** (Apache-2.0, Text in [`code/lizenzen/zxing-cpp.txt`](code/lizenzen/zxing-cpp.txt)), aus den Quellen auf dem festen Commit des Tags v2.3.0 gebaut, nur mit den Lesern. Darin enthalten ist **libzueci** für Zeichensätze (BSD-3-Clause, mit einem UTF-8-Decoder unter MIT-Lizenz; Text in [`code/lizenzen/libzueci.txt`](code/lizenzen/libzueci.txt)).

**Bau** (`code/bauen.sh`): zxing-cpp wirft intern Ausnahmen und fängt sie selbst. Das kann erst das **WASI-SDK 33** (WebAssembly-Ausnahmen mit libunwind); das Skript holt diese Version über `werkzeuge/wasi-sdk.sh` mit fester Prüfsumme, alle anderen Pakete bleiben bei Version 25. Das Modul ist etwa 1 MB groß und braucht für zwei A4-Seiten rund 60 MB Speicher (Grenze 256 MB).

## Tests

`tests/pruefen.sh` baut das Modul und ruft es wie Ablago auf (`tests/modul_test.mjs`):

- **dms:codes:** zwei A4-Seiten mit QR, EAN-13, Code 128, Data Matrix, Aztec (gedreht), PDF417 und ITF in Lesereihenfolge; Seitenzahl von Ablago; kaputter QR-Code neben einem heilen; Seite ohne Code; doppelte Codes; GiroCode mit Zeilenumbrüchen; fremde Dokument-Id; Dokument ohne Seiten; Protokoll ohne Inhalte.
- **dms:erkennen:** vCards 2.1, 3.0 und 4.0 für Person und Organisation, gedreht, klein und verrauscht, auf der zweiten Seite neben einem anderen Code, präparierte vCard mit überlangen Werten, Steuerzeichen und Foto, Internetadresse, GiroCode, nur Strichcode, Bild ohne Code, fremde Dokument-Id.

Die Matrizen in `tests/codes/` erzeugen `tests/erzeuge.cpp` (Schreiber von zxing-cpp) und `tests/erzeuge_vcard.mjs` (npm-Paket `qrcode`), beide nur von Hand nötig. Alle Namen, Nummern und Adressen sind erfunden.
