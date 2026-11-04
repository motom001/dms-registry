# Änderungen

## 1.1.0

- **Nur noch lesen** (DMS #636, dms-registry #101): Den Stand der Kopie („läuft“, „hochgeladen“, „geprüft“, „fehlgeschlagen“) meldet das Paket in der Antwort auf das Ereignis statt per `PUT /sicherungen/{name}/extern`. Ablago gibt ihm dafür einen API-Schlüssel, der nur lesen darf. Endgültige Fehler (z. B. Passwort falsch, Prüfsumme weicht ab) meldet es mit Rückgabewert 2, vorübergehende mit 1.
- Braucht Ablago ab 0.158.1.

## 1.0.1

- Texte: Das Programm heißt jetzt **Ablago** (dms-registry #111). Inhalt, Rechte und Verhalten sind unverändert.

## 1.0.0

- Erste Fassung (DMS #585, dms-registry #71, Stufe 1): bringt jede Sicherung des DMS nach dem Ereignis *Sicherung fertig* auf einen WebDAV-Speicher und prüft sie dort – **Nextcloud** (Hochladen in Teilen mit Chunking v2, auch für Sicherungen mit mehreren GB), **Nextcloud-Dateiablage** („Nur Hochladen“, bis 128 MB am Stück, ohne Lese- und Löschrecht) und **WebDAV allgemein** (Teile mit `Content-Range`, kleine Sicherungen am Stück).
- Liest die verschlüsselte Sicherung in Stücken zu höchstens 8 MB, verteilt lange Arbeit auf mehrere Aufrufe und macht nach einem Abbruch an der letzten Stelle weiter.
- Prüft Größe und Prüfsumme (SHA-256) durch Zurücklesen – bis 2 GB (einstellbar) vollständig, darüber mit 8 Stichproben und einmal im Monat vollständig. Eine Dateiablage meldet ehrlich „hochgeladen“.
- Legt die schlanken Metadaten (`<name>.json`) neben die Sicherung – damit lässt sich die Kopie ohne Gerät wiederherstellen.
- Meldet dem DMS je Sicherung „läuft“, „geprüft“, „hochgeladen“ oder „fehlgeschlagen“ mit verständlichem Grund (z. B. „Benutzer oder Passwort falsch“, „Speicher am Ziel voll“, „Prüfsumme am Ziel weicht ab“).
- *Alte Sicherungen am Ziel löschen* gibt es nur als bewusste Wahl (Vorgabe aus).
- *Verbindung testen* mit den gespeicherten Einstellungen.
- Braucht DMS ab 0.142.0.
