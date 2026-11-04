# QR-Code lesen

Viele Visitenkarten tragen einen **QR-Code mit einer vCard** – alle Kontaktdaten in maschinenlesbarer Form. Mit dem Paket **QR-Code lesen** übernimmt Ablago diese Angaben beim **Aus Dokument ausfüllen** direkt aus dem QR-Code statt aus dem erkannten Text. Das ist zuverlässiger: keine verwechselten Ziffern in der Telefonnummer, kein abgeschnittener Firmenname.

Es läuft im **Paket-Läufer** von Ablago: abgeschottet, ohne Netz, mit Grenzen für Speicher und Zeit.

## So arbeitet es

1. Du fotografierst oder scannst eine Visitenkarte und legst sie ab, z. B. in einer neuen Person oder Organisation.
2. Du klickst **Aus Dokument ausfüllen**. Ist das Paket für diesen Mappentyp gewählt (siehe unten), gibt Ablago ihm die Dokumente mit.
3. Das Paket holt die Seiten als Bild (bei Scans mit 300 dpi, Fotos in voller Größe), sucht QR-Codes und liest die erste **vCard** (Version 2.1, 3.0 und 4.0).
4. Ablago zeigt die Angaben als **Vorschläge** an den Feldern. Gespeichert wird erst, wenn du bestätigst. Jeder Wert ist vorher gegen die Feldart geprüft; was nicht passt, verwirft Ablago.

| aus der vCard | in das Feld mit der Erkennungsart |
| --- | --- |
| `N` (Nachname; Vorname), sonst `FN` | Vorname, Nachname |
| `ORG` (erster Teil), sonst `FN` | Name oder Firma (nur bei Mappentypen ohne Vor- und Nachname, z. B. Organisation) |
| `TITLE`, sonst `ROLE` | Funktion |
| `EMAIL` | E-Mail-Adresse |
| `TEL` (geschäftlich bevorzugt) / `TEL;TYPE=CELL` / `TEL;TYPE=FAX` | Telefon / Mobil / Fax |
| `URL` | Internetseite |
| `ADR` (geschäftlich bevorzugt) | Straße, Hausnummer (aus der Straße getrennt, wenn es ein eigenes Feld gibt), PLZ, Ort |

Welche Felder eine Erkennungsart haben, steht am Mappentyp (**Werkbank → Ablage aufbauen → Mappentypen → Feld → Für die Erkennung nutzen**); die Mappentypen *Person* und *Organisation* aus dem Paket Basis haben sie schon.

**Kein QR-Code oder keine Visitenkarte?** Dann antwortet das Paket mit dem Grund, z. B. „QR-Code gefunden (Internetadresse), aber keine Visitenkarte“, und Ablago füllt wie gewohnt **aus dem erkannten Text** aus. Andere QR-Inhalte – Internetadressen, **GiroCode** (Überweisung), Text – wertet das Paket bewusst nicht aus.

**Was nicht übernommen wird:** Fotos in der vCard, Notizen, Geburtstage und alles, wofür der Mappentyp kein passendes Feld hat. Verweisfelder (z. B. die *Organisation* an einer Person) gleicht Ablago wie immer selbst mit vorhandenen Mappen ab.

### Paket wählen

Ablago fragt bei **Aus Dokument ausfüllen** genau eine Erkennung. Wähle das Paket dort, wo Visitenkarten ankommen:

- **am Mappentyp** (z. B. *Person* und *Organisation*): in der Erkennung des Mappentyps das Paket *QR-Code lesen* wählen, oder
- **als Standard** für alle Mappentypen: **Werkbank → Pakete → QR-Code lesen → Aus Dokument ausfüllen → Dieses Paket als Standard für alle Mappentypen nutzen**.

Bei Dokumenten ohne QR-Code kostet das nur einen Augenblick (die Seiten werden einmal angesehen), dann liest Ablago den Text.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt Ablago diese Rechte und lässt sie dich bestätigen:

- **Mappen lesen: alle Mappentypen** – Dokumente liegen in Mappen beliebiger Typen; die Mappen selbst liest das Paket nicht.
- **Dokumente lesen** – nur die Seitenbilder der Dokumente, die Ablago beim Ausfüllen nennt. Dokumente ändert, ersetzt oder löscht es nicht.
- **Felder aus Dokumenten vorschlagen (dms:erkennen)** – Ablago gibt die Feldbeschreibung des Mappentyps mit und prüft jede Antwort.
- **Kein Netz.** Alles geschieht im Paket.
- Es reagiert auf **keine Ereignisse**; es arbeitet nur, wenn du **Aus Dokument ausfüllen** klickst.

## Einstellungen

Unter **Werkbank → Pakete → QR-Code lesen → Einstellungen**:

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Auflösung (dpi) | 300 | Für Scans (150–400). Fotos liest das Paket in ihrer vollen Größe. |
| Höchstens so viele Seiten je Dokument | 2 | Vorder- und Rückseite einer Karte. Mehr Seiten kosten Zeit beim Ausfüllen. |

## Fremde Daten

Ein QR-Code kann alles Mögliche enthalten, auch absichtlich Präpariertes. Darum:

- Jeder Wert ist auf 300 Zeichen begrenzt, Steuerzeichen werden zu Leerzeichen, eine vCard hat höchstens 200 Zeilen; ältere vCards in Latin-1 und mit Quoted-Printable werden in UTF-8 umgewandelt.
- Das Paket liest höchstens drei Dokumente je Aufruf und nur die Seitenbilder dieser Dokumente.
- Ablago prüft danach jeden Vorschlag gegen die Feldart (Länge, Muster, Zahl) und speichert nichts ohne deine Bestätigung.

## Bibliotheken und Lizenzen

Das Paket steht unter **Apache-2.0**. Der QR-Leser ist **quirc 1.2** von Daniel Beer (ISC-Lizenz, Text in [`code/lizenzen/quirc.txt`](code/lizenzen/quirc.txt)), aus den Quellen auf dem festen Commit des Tags v1.2 gebaut (`code/bauen.sh`). Abweichend von der Vorgabe ist quirc mit bis zu 65 534 Regionen gebaut, damit es QR-Codes auch auf Fotos mit viel Text und in großen Codes (lange vCards) findet.

## Tests

`tests/pruefen.sh` baut das Modul und ruft es wie Ablago auf (`tests/modul_test.mjs`): vCards 2.1, 3.0 und 4.0 für Person und Organisation, gedreht, klein und verrauscht, auf der zweiten Seite neben einem anderen Code, präparierte vCard mit überlangen Werten, Steuerzeichen und Foto, Internetadresse, GiroCode, Bild ohne Code, fremde Dokument-Id. Die QR-Matrizen in `tests/qr/` erzeugt `tests/erzeuge.mjs` (npm-Paket `qrcode`, nur von Hand nötig). Alle Namen und Adressen sind erfunden.
