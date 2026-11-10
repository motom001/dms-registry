# Compliance

**Selbstkontrolle: Verfahrensdokumentation, Datenschutz, Nachweise.** Ihr beschreibt einmal, wie ihr arbeitet. Ablago hält jeden Tag fest, wie es eingerichtet ist, und legt jeden Monat die Nachweise an. So bleibt die Dokumentation aktuell, ohne dass jemand Einstellungen abschreibt. Das passt für die Tischlerei Brandt genauso wie für Lena zu Hause, die festhalten will, wie sie scannt und wann Papier weg darf.

> Das Paket **unterstützt** die Dokumentation. Es macht nichts „GoBD-konform“, ist kein Zertifikat und keine Rechts- oder Steuerberatung.

## Inhalt

| Mappentyp | wer schreibt | wer liest | wofür |
| --- | --- | --- | --- |
| **Verfahren** | Verwaltung | alle | So machen wir es – je Bereich eine Mappe, mit Versionen in der Historie |
| **Konfiguration** | nur das Paket | Gesamte Verwaltung | So ist Ablago in diesem Monat eingerichtet – je Bereich und Monat eine Mappe, z. B. „Konfiguration · Sicherung · 2026-11“ |
| **Nachweise** | nur das Paket | Gesamte Verwaltung | Was im Monat passiert ist – ein Bericht je Monat („Nachweise · 2026-10“) |

**Bereiche** (in allen drei Typen gleich): Allgemeines, Belegeingang und Scannen, Ablage, Zugang und Berechtigungen, Betrieb, Sicherung, Unveränderbarkeit, Datenschutz, Betriebsprüfung. Was nur im Betrieb gebraucht wird (weitere Programme, ersetzendes Scannen, Betriebsprüfung), zeigt sich nur, wenn Ablago **beruflich genutzt** wird.

### Verfahren

Oben Bereich, Zuständig, Gilt ab und „So machen wir es“. Darunter nur der Abschnitt des gewählten Bereichs, zum Beispiel:

- **Belegeingang und Scannen:** wie Post hereinkommt, Scanablauf, Kontrolle, Papier danach (bleibt / weg nach der Kontrolle / weg nach einer Frist), was im Original bleibt.
- **Sicherung:** Kopie außer Haus und wo, Probe-Wiederherstellung wie oft.
- **Datenschutz:** wann gelöscht wird, wer Fragen zu gespeicherten Daten beantwortet.

Register *Verfahren*, *Unterlagen* (mit Versionen), *Historie*.

### Konfiguration

Bereich, Monat, Status (aktuell/abgelöst), **Änderung** in Worten, Stand vom, Stände in diesem Monat, Abgelöst am, vorheriger Monat, abgelöst durch, Ablago-Version und **Prüfwert (SHA-256)** der JSON-Datei. Im Register *Dateien* liegt je Stand die JSON-Datei als Version. Die Kennung `{Bereich} · {Monat}` ist eindeutig.

### Nachweise

Monat, Stichtag (Monatsende), Zahlen je Bereich, Benutzer zum Stichtag, enthaltene Bereiche, Prüfwert. Die JSON-Datei enthält die Aufstellung der Benutzer und die Listen der Ereignisse. Fehlanmeldungen stehen darin nur gekürzt, ohne volle Adresse und ohne eingegebene Benutzernamen.

## So arbeitet das Paket

- **Jeden Morgen** (Automatisierung **„Konfiguration und Nachweise festhalten“**, 04:30, gleich eingeschaltet, änderbar unter Automatisierungen) holt das Paket die Einrichtung jedes freigegebenen Bereichs und vergleicht sie mit dem letzten Stand.
  - Es zählt nur, was in der Liste **„was zählt“** angehakt ist. Ändert sich nur ein Zeitstempel, passiert nichts.
  - Hat sich etwas geändert, das zählt, kommt eine **neue Version** in die Mappe des Monats. Gibt es für diesen Monat noch keine, legt das Paket sie an, und die vorige gilt als abgelöst.
- **Am ersten Lauf eines Monats** entstehen die **Nachweise des Vormonats**. Verpasste Monate holt der nächste Lauf nach, höchstens zwölf.
- **Erstlauf:** Sobald du in den Einstellungen Bereiche anhakst, hält das Paket den ersten Stand fest.
- Ändert sich die Auswahl „was zählt“ selbst, ist das eine Änderung im Bereich Allgemeines.
- **Aufbewahrung** (Vorschlag beim Installieren, am Mappentyp jederzeit änderbar): Verfahren und Konfiguration 2 Jahre, bei beruflicher Nutzung 10 Jahre; Nachweise 2 Jahre. Die Frist eines aktuellen Stands läuft noch nicht, sie beginnt mit „Abgelöst am“ bzw. „Gilt nicht mehr seit“. **Warum 10 Jahre?** So lange sind Buchungsbelege und die Unterlagen, die sie erklären, im Betrieb meist aufzubewahren. Das ist keine Rechtsberatung; frag im Zweifel deine Steuerberatung.

## Einrichten

1. **Paket-Einstellungen → Bereiche:** je Bereich „Konfiguration lesen“ und „Nachweise erstellen“ anhaken. Vorgabe ist **nichts**. Freigeben kann nur, wer den Bereich selbst verwaltet; Zugang und Nachweise nur mit Gesamter Verwaltung. Am Haken für Nachweise steht: Sie enthalten Benutzer und Fehlanmeldungen.
2. **Was zählt:** je Bereich aufklappen und prüfen. Vorausgewählt ist ein Vorschlag, zum Beispiel zählen bei *Ablage* neue Felder und Feldtypen, Hilfetexte aber nicht.
3. **Rechte prüfen:** Konfiguration und Nachweise sind nach der Installation nur für die Gesamte Verwaltung lesbar. Anlegen und ändern kann sie nur das Paket. Passe die Rechte an, wenn bei euch jemand anderes prüft.
4. **Aufbewahrung** im Assistenten bestätigen.
5. **Verfahren beschreiben:** je Bereich eine Mappe, kurz und in euren Worten.

Speicherbedarf: geschätzt 5–30 MB im Jahr (JSON je Stand und Monat, ohne PDF).

## Einstellungen

| Einstellung | Vorgabe | Bedeutung |
| --- | --- | --- |
| Was zählt (je Bereich) | Vorschlag aus Issue #166 | Nur angehakte Änderungsarten ergeben eine neue Version der Konfiguration. |

Die Haken „Konfiguration lesen“ und „Nachweise erstellen“ je Bereich stellt Ablago selbst dar (DMS #1054).

## Voraussetzungen

- Ablago ab 0.230.0 (vorläufig): Konfiguration und Nachweise als Daten (DMS #1053), Paket-Recht je Bereich (#1054), Rechte und Archivmodus am Mappentyp aus dem Paket (#1051, Entscheidung 10.11.2026), Zusammengesetzt (#1050), berechnete Felder (#1034), Anzeige-Bedingungen und „beruflich genutzt“ (#1032, #1033), „Paket nach Zeitplan ausführen“ (#1082).
- Keine anderen Pakete.

## Rechte und Netzwerkzugriff

- **Konfiguration lesen** und **Nachweise lesen** je Bereich – nur, was der Admin anhakt und der hinterlegte Benutzer selbst verwaltet.
- **Mappen lesen, anlegen und ändern:** Konfiguration, Nachweise (nur ihre berechneten Felder). Verfahren liest das Paket nicht.
- **Dokumente schreiben:** nur die JSON-Dateien in Konfiguration und Nachweisen.
- **Kein Zugriff auf Netzwerk und Internet.** Konfiguration und Nachweise verlassen das Haus nicht. Passwörter und Geheimnisse gibt Ablago nie heraus (DMS #1055).
- Reagiert auf: `zeitplan.ausgefuehrt` (Automatisierung), `paket.einstellungen_geaendert`.

## Noch nicht in diesem Paket

- PDF zum Lesen je Stand (kommt mit „Text setzen“, DMS #1040), Gesamtdokumentation als ein PDF.
- Abgleich von Soll und Ist, z. B. „Probe-Wiederherstellung überfällig“.
- Datenschutz des Betriebs (Verzeichnis von Verarbeitungstätigkeiten, TOM, Datenpannen, Betroffenenanfragen) – eigenes späteres Paket.

## Entwickeln

| Datei | Inhalt |
| --- | --- |
| [`code/bereiche.h`](code/bereiche.h) | Bereiche und Liste „was zählt“: Text in den Einstellungen → Kennung im Vergleich des Kerns |
| [`code/stand.h`](code/stand.h) | Monate, Auswahl, Änderungen in Worten, Zusammenfassung der Nachweise – ohne Ablago testbar |
| [`code/sha256.h`](code/sha256.h) | Prüfwert der JSON-Dateien |
| [`code/compliance.cpp`](code/compliance.cpp) | Ablauf, Lesen und Schreiben über die API, Speicher des Pakets |
| [`tests/stand_test.cpp`](tests/stand_test.cpp) | läuft nativ in `code/bauen.sh` |
| [`tests/einstellungen_test.py`](tests/einstellungen_test.py) | Manifest und `bereiche.h` passen zusammen |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | das gebaute Modul gegen eine Nachbildung von Ablago (Schnittstellen aus DMS #1053, wie angenommen) |
