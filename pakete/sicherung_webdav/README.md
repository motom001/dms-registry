# Sicherungsziel WebDAV

Bringt jede Sicherung des DMS **außer Haus** – auf **Nextcloud**, ein **NAS** oder einen **WebDAV-Speicher beim Hoster** – und **prüft** dort, dass sie heil angekommen ist. Gedacht für alle, deren DMS ohne Sicherungs-App des NAS läuft: auf einem Raspberry Pi, einem gemieteten Server oder bei einem Anbieter. Läuft das DMS auf einem NAS mit *Hyper Backup* oder *Hybrid Backup Sync*, reicht meist die App des NAS (siehe [Sicherung außer Haus](https://motom001.github.io/dms/admin/aktuell/sicherung-ausser-haus/) im Administratorhandbuch).

Es läuft im **Paket-Läufer** des DMS: abgeschottet, mit Grenzen für Speicher und Zeit, ins Netz nur zur Adresse, die du einträgst und bestätigst.

## So arbeitet es

1. Das DMS sichert wie immer **zuerst lokal** in den Sicherungsordner. Danach meldet es dem Paket die fertige Sicherung (Ereignis *Sicherung fertig*).
2. Das Paket liest die **verschlüsselte** Sicherung in Stücken und lädt sie **in Teilen** hoch – auch mehrere GB, ohne sie ganz in den Speicher zu laden. Bricht das Netz ab, versucht es das DMS nach 1, 5, 30 Minuten, 2 und 6 Stunden erneut; das Paket macht an der letzten Stelle weiter. Die lokale Sicherung bleibt davon unberührt.
3. Neben die Sicherung legt es die **schlanken Metadaten** (`<name>.json`: Größe, Prüfsumme, Zeitpunkt, Fingerabdruck des Schlüssels – keine Namen, keine Versionen). Mit beiden Dateien lässt sich die Kopie wiederherstellen, auch wenn das Gerät weg ist.
4. Es **prüft**: Größe am Ziel und Prüfsumme (SHA-256) durch Zurücklesen – bis 2 GB jede Sicherung vollständig, größere mit 8 Stichproben und einmal im Monat vollständig.
5. **Werkbank → Sicherung** zeigt je Sicherung „lokal ✓ · extern ✓ geprüft“ – oder „fehlgeschlagen“ mit Grund. Kommt seit mehr als 2 Tagen keine neuere Sicherung am Ziel an oder schlägt eine Kopie endgültig fehl, bekommen die Administratoren eine E-Mail.

| Art des Ziels | Hochladen | Prüfen | Löschen möglich? |
| --- | --- | --- | --- |
| **Nextcloud** (Benutzer + App-Passwort) | in Teilen (Chunking v2), beliebig groß | Größe + Zurücklesen | ja (Zugang darf löschen) |
| **Nextcloud-Dateiablage** (Freigabe „Nur Hochladen“) | am Stück, bis 128 MB | nicht möglich – „hochgeladen“ | **nein** – bester Schutz |
| **WebDAV allgemein** (NAS, Hoster) | bis zur Teilgröße am Stück, größer in Teilen mit `Content-Range` (z. B. Apache mit mod_dav) | Größe + Zurücklesen (mit `Range`) | ja (Zugang darf meist löschen) |

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Die verschlüsselte Sicherung lesen, um sie außer Haus zu kopieren – kann sie nicht öffnen (kein Schlüssel, keine Inhalte) (dms:sicherung-lesen)** – das Paket liest genau die Sicherung aus seinem Ereignis, so wie sie verschlüsselt im Sicherungsordner liegt, und meldet zurück, ob sie angekommen ist. Den Schlüssel der Werkbank, Mappen, Dokumente und andere Dateien des Sicherungsordners bekommt es nie.
- **Zugriff auf Netzwerk/Internet nur zu: der Adresse aus der Einstellung „Adresse“ (trägst du ein und bestätigst sie)** – dorthin geht die verschlüsselte Sicherung, sonst nirgends hin. Weiterleitungen auf andere Server folgt es nicht.
- Es reagiert auf **Eine Sicherung ist fertig (verschlüsselt) und kann außer Haus kopiert werden** (`sicherung.fertig`).

Das Passwort speichert das DMS verschlüsselt wie jedes Passwortfeld und zeigt es nach dem Speichern nicht mehr an. Es steht weder im Protokoll noch in den Meldungen an die Werkbank.

## Einrichten

**Nextcloud** (Beispiel mit der erfundenen Adresse `https://cloud.example.org`):

1. In der Nextcloud einen **eigenen Benutzer** nur für die Sicherungen anlegen (z. B. `dms-sicherung`) und dort unter *Einstellungen → Sicherheit* ein **App-Passwort** erzeugen.
2. Im DMS **Werkbank → Pakete → Sicherungsziel WebDAV → Einstellungen**: *Art des Ziels* **Nextcloud**, *Adresse* `https://cloud.example.org`, *Benutzer* `dms-sicherung`, *Passwort* das App-Passwort, *Ordner* `DMS-Sicherung`. Speichern und die Adresse bestätigen.
3. **Verbindung testen**, dann unter *Werkbank → Sicherung* **Jetzt sichern** und zusehen, wie die Kopie in der Spalte *Wo* ankommt.

**Nextcloud-Dateiablage:** In der Nextcloud einen Ordner anlegen, *Teilen → Link teilen → Nur Hochladen (Dateiablage)* wählen und am besten ein Kennwort setzen. Im DMS *Art des Ziels* **Nextcloud-Dateiablage**, *Adresse* `https://cloud.example.org`, *Freigabe-Link* den Link (`https://cloud.example.org/s/…`), *Passwort* das Kennwort der Freigabe.

**NAS oder Hoster:** WebDAV am NAS bzw. beim Hoster einschalten, einen eigenen Benutzer mit Zugriff nur auf einen Ordner anlegen. Im DMS *Art des Ziels* **WebDAV allgemein**, *Adresse* die WebDAV-Adresse des Ordners (z. B. `https://nas.example.org:5006/sicherung`), Benutzer und Passwort. Sicherungen bis zur Teilgröße (8 MB) gehen überall; größere brauchen einen Server, der Teile mit `Content-Range` annimmt – sonst meldet das Paket das verständlich. Nextcloud kann es immer.

## Schutz gegen Erpressersoftware

Übernimmt jemand dein DMS, kennt er die gespeicherten Zugangsdaten. Damit er die Kopien außer Haus nicht löschen kann:

- **Am besten die Nextcloud-Dateiablage:** Sie kann hochladen, aber nicht auflisten, lesen oder löschen. Papierkorb und Versionen einer normalen Nextcloud helfen **nicht** – derselbe Zugang kann sie leeren.
- Sonst einen **eigenen Benutzer** nur für die Sicherungen und am Ziel **Versionierung oder Schnappschüsse**, die dieser Benutzer nicht löschen kann (z. B. Schnappschüsse des NAS).
- **Alte Sicherungen am Ziel löschen** bleibt am besten **aus** (Vorgabe). Dann listet das Paket am Ziel nichts auf und löscht nichts; aufräumen lässt du das Ziel selbst. Schaltest du es ein, braucht der Zugang Löschrechte – genau das hebt den Schutz auf.
- Der **Schlüssel** der Werkbank gehört nie auf das Ziel – ohne ihn ist die Kopie wertlos, mit ihm wäre sie für jeden lesbar.

## Einstellungen

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Art des Ziels | Nextcloud | Nextcloud, Nextcloud-Dateiablage oder WebDAV allgemein |
| Adresse | – | Nextcloud: Adresse der Nextcloud; WebDAV allgemein: Adresse des Ordners |
| Benutzer, Passwort | – | Zugang; bei Nextcloud ein App-Passwort |
| Ordner | DMS-Sicherung | Ordner im Nextcloud-Konto bzw. Unterordner unter der WebDAV-Adresse; fehlt er, legt ihn das Paket an |
| Freigabe-Link (Dateiablage) | – | nur bei der Dateiablage |
| Teilgröße (MB) | 8 | 5–8; jeder Teil muss in etwa 2 Minuten hochgeladen sein |
| Vollständig zurücklesen bis (MB) | 2048 | darüber Stichproben, einmal im Monat vollständig |
| Alte Sicherungen am Ziel löschen | aus | siehe oben |
| Am Ziel behalten (Anzahl) | 14 | nur mit „löschen“ |

## Grenzen

- Die **Dateiablage** nimmt Sicherungen nur am Stück und höchstens 128 MB (die Datei liegt dafür im Speicher des Aufrufs, 256 MB). Größere melden „fehlgeschlagen“ mit Hinweis auf einen Nextcloud-Benutzer.
- Ein Aufruf darf 2 Minuten dauern; jeder Teil muss in dieser Zeit oben sein. Das ganze Hochladen einer Sicherung verteilt sich auf höchstens 500 Fortsetzungen (gut 8 Stunden) – danach gilt es als fehlgeschlagen.
- Zurücklesen kostet Zeit und Datenvolumen in voller Größe der Sicherung. Wer das nicht will, setzt *Vollständig zurücklesen bis* auf 0 – dann prüft das Paket mit Stichproben und einmal im Monat vollständig.
- S3-kompatible Speicher (mit Object Lock) kommen als eigenes Paket (Stufe 2). SFTP und FTPS gibt es nicht.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit dem Paketnamen im Titel.
