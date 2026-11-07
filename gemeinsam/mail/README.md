# Mail-Zerleger (gemeinsam)

E-Mails zerlegen – `.eml` (RFC 5322 mit MIME, RFC 2047/2231) und Outlook `.msg` (Compound File) –, ohne Bibliotheken
und ohne etwas auszuführen. Zwei Pakete binden diesen Ordner beim Bau ein (`-I gemeinsam/mail` in `code/bauen.sh`):

| Paket | macht daraus |
| --- | --- |
| [Office und E-Mail](../../pakete/office_email/) | den Volltext (`code/mailtext.h`) |
| [PDF/A](../../pakete/pdfa/) | die Archivfassung als Seiten (`code/mailsatz.h`, dms-registry #143) |

| Datei | Inhalt |
| --- | --- |
| `mail.h` | Kopf, Blöcke in der Reihenfolge der Mail (Text, HTML, Alternativen, Anhänge mit Content-ID, eingebettete Mails, verschlüsselte Teile), Datum als Zeitpunkt; Outlook-Nachrichten |
| `cfb.h` | Compound File Binary (OLE2) lesen: Verzeichnis und Datenströme |
| `zeichen.h` | UTF-8, Zeichensätze (Latin-1, Windows-1252, UTF-16), Base64, Quoted-Printable, HTML-Entitäten, HTML zu Text |

Ändert sich hier etwas, baut die CI beide Pakete neu (`werkzeuge/bauen.py --geaendert`) und lässt ihre Tests laufen.
Veröffentlicht wird die Änderung mit der nächsten Version des jeweiligen Pakets.

Lizenz: Apache-2.0 wie das Repository.
