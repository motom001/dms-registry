# Fahrzeuge – Abruf beim KBA

Die Ergänzung zum Paket **Fahrzeuge** holt auf Knopfdruck Daten beim **Kraftfahrt-Bundesamt (KBA)** und trägt sie in leere Felder ein:

| Aktion (Menü „Mappe“) | an | holt | braucht |
| --- | --- | --- | --- |
| **Daten beim KBA abrufen** | Hauptuntersuchung | den **Digitalen Untersuchungsbericht**: Art und Typ der Untersuchung, Datum, Bericht-Nr., Kilometerstand, Ergebnis, Prüfplakette, Wiedervorführung, Mängel und Hinweise, nächste HU/SP, Kosten, dazu HSN, TSN und zulässige Gesamtmasse | den Link aus dem QR-Code auf dem Prüfbericht (Feld *Digitaler Untersuchungsbericht*) |
| **Technische Daten beim KBA abrufen** | Fahrzeug | den **elektronischen CoC**: Typgenehmigung, Hubraum, Kraftstoff, Emissionsklasse, CO₂, zulässige Gesamtmasse, Anhänge- und Stützlast, Reifengrößen, bei älteren Datensätzen auch HSN/TSN | die Fahrzeug-Identnummer |

**So läuft es:**

1. Ablago zeigt, was an das KBA geht – Such-ID, Prüfberichtsnummer und Kennnummer der Prüfstelle bzw. die Fahrzeug-Identnummer. Ohne Klick auf **Abrufen** geht nichts raus.
2. Das Paket löst die Rechenaufgabe (Captcha), die die öffentlichen Seiten des KBA stellen, und fragt ab.
3. **Nur leere Felder** werden gefüllt. Was schon anders eingetragen ist, bleibt – die Meldung nennt die Abweichung.
4. HSN, TSN und Gesamtmasse aus dem Prüfbericht kommen über die Automatisierung *Fahrzeugdaten aus dem Prüfbericht übernehmen* (Paket Fahrzeuge) ans Fahrzeug, ebenfalls nur in leere Felder.

**Elektronische CoC** gibt es vor allem für neuere Fahrzeuge – ab dem 5. Juli 2026 gebaute Fahrzeuge haben nur noch ihn. Für ältere Fahrzeuge meldet das KBA meist nichts; dann stehen die Daten in der Zulassungsbescheinigung.

## Datenschutz

- Der Link aus dem QR-Code wirkt wie ein Schlüssel zu deinem Prüfbericht. Gib ihn nicht weiter.
- Das Paket schickt nur die genannten Angaben, nur an die beiden Adressen unten und nur nach deinem Klick. Es speichert nichts außer den Feldern der Mappe.

## Schnittstelle und Quellen

Das KBA bietet für diese Abrufe **keine offizielle Programmierschnittstelle** an. Das Paket arbeitet **auf Basis der von uns erkannten Schnittstelle** – es macht dieselben Aufrufe wie die öffentlichen Seiten des KBA:

- Digitaler Untersuchungsbericht: `https://www.kba-online.de/dub/` (Aufrufe `…/dub/api/altcha`, `…/dub/api/dubAnfrage`)
- Elektronischer CoC: `https://www.kba-online.de/ivicoc_prod/public-access/webapp/` (Aufrufe `…/api/altcha`, `…/api/vin/data`)

Ändert das KBA etwas, meldet die Aktion einen verständlichen Fehler statt falscher Werte. Bitte dann ein Issue anlegen.

Die Bedeutung der Felder folgt amtlichen Beschreibungen:

- **Digitaler Untersuchungsbericht:** XKfz 6.1, Datentyp `Type.DigitalerUntersuchungsbericht`, Codelisten „Art der Untersuchung“, „Typ der Untersuchung“, „Ergebnis der Untersuchung“ – im XRepository: https://www.xrepository.de (Kennung `urn:xoev-de:kba:standard:xkfz`)
- **Elektronischer CoC (IVI):** VO (EU) 2018/858 Art. 37, Durchführungsverordnung (EU) 2024/1061; Datenformat (XSD, Messagebook) bei EUCARIS: https://ecoc.eucaris.net/documentation – das Paket liest IVI 1.x und 2.0

## Voraussetzungen

- Ablago ab Version 0.323
- Paket **Fahrzeuge** ab 2.10.0 – kommt bei der Installation mit

## Rechte und Netz

Das Paket enthält Code (WebAssembly). Es liest nur die Mappe, an der du die Aktion startest, und geht nur zu den beiden Adressen oben ins Netz. Geschrieben wird mit deinem Zugriff, nur in leere Felder.

## Keine Gewähr

Die Daten kommen vom KBA, so wie sie dort stehen. Das Paket ist kein Angebot des KBA.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Fahrzeuge – Abruf beim KBA“ im Titel.
