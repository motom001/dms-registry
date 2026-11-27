# Fahrzeuge

Das Paket **Fahrzeuge** bringt den Mappentyp **Fahrzeug** und die Vertragsarten **Pkw-Kaufvertrag** und **Leasing**. Damit verpasst du die HU nicht, findest Fahrzeugbrief und Versicherung schnell und hast beim Verkauf alle Rechnungen beisammen. Installiert wird es unter **Werkbank → Pakete**; die Pakete **Basis**, **Verträge** und **Rechnungen und Bestellungen** kommen dabei automatisch mit.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Fahrzeug | Pkw, Motorrad, Wohnmobil, Anhänger, E-Bike | Bezeichnung, Art, Kennzeichen (eindeutig), Fahrzeug-Identnummer, Erstzulassung, Halter (Person), Verantwortlich, Versicherung, Finanzierung/Leasing | **HU fällig** (einen Monat vorher) |
| Hauptuntersuchung (ab 2.3.0) | Prüfbericht der HU oder Sicherheitsprüfung | Fahrzeug, Art und Typ der Untersuchung, geprüft am, Prüfstelle, Bericht-Nr., Kilometerstand, Ergebnis, Prüfplakette, Wiedervorführung, Mängel und Hinweise, nächste HU/SP, Kosten, Link zum Digitalen Untersuchungsbericht; Register *Fahrzeugdaten laut Bericht* (HSN, TSN, Gesamtmasse) | **Nachprüfung bis** (nur bei erheblichen oder gefährlichen Mängeln, eine Woche vorher) |
| Gutachten / Abnahme (ab 2.9.0) | Vollgutachten, Änderungsabnahme, Oldtimer-Gutachten, ABE, Teilegutachten | Fahrzeug, Art (amtliche Liste), Gutachtennummer, Datum, Prüforganisation, Gegenstand, Eintragung nötig / eingetragen am, **Passt zum Fahrzeug** | – |
| Zulassungsbescheinigung (ab 2.9.0) | Fahrzeugschein (Teil I) oder Fahrzeugbrief (Teil II), jede Ausgabe einzeln | Fahrzeug, Teil, Nummer, ausgestellt am, Kennzeichen, Anlass, **ersetzt**, nächste HU, technische Daten | – |
| Fahrzeugpapiere (ab 2.9.0) | CoC, Abmeldebescheinigung, Fahrzeugschein und -brief von vor 2005 | Fahrzeug, Art, Datum, Verbleib Original | – |
| Rückruf (ab 2.9.0) | Rückrufaktion: Anschreiben, Erinnerung, Bestätigung der Werkstatt | Fahrzeug, Rückrufcode, KBA-Referenznummer, Grund, Status, durchgeführt am, Werkstatt | **Durchführen bis** (14 Tage vorher) |

**Register:** Das **Fahrzeug** zeigt unter *Rechnungen* alle Rechnungen aus dem Paket Rechnungen und Bestellungen, bei denen *Betrifft* dieses Fahrzeug ist – Werkstatt, Reifen, Zubehör; dazu *Dokumente*, *Verknüpfungen* und *Historie*.

**Technische Daten** (ab 2.9.0): ein eigenes Register am Fahrzeug, nur mit Werten, die man im Alltag braucht – HSN/TSN (Versicherung), Typgenehmigung (ABE und Teilegutachten), Hubraum, Kraftstoff, Emissionsklasse, CO₂ und zulässige Gesamtmasse (Kfz-Steuer), Anhänge- und Stützlast (Anhänger, Fahrradträger), zulässige Reifengrößen (Reifenkauf) und die Feinstaubplakette. Die Hilfe nennt jeweils das Feld der Zulassungsbescheinigung Teil I. Lkw und Zugmaschine sind als Art dazugekommen.

**Zulassungsbescheinigung → Fahrzeug** (ab 2.9.0): Die Automatisierung *Zulassungsbescheinigung ans Fahrzeug übernehmen* (beim Installieren vorausgewählt) trägt Kennzeichen und technische Daten am Fahrzeug ein – **nur in leere Felder**, sie überschreibt nie. So schadet auch ein alter Schein nicht, den du später einscannst. Die nächste HU (Feld X) kommt nur, wenn sie später ist. *Ersetzt* verkettet die Bescheinigungen eines Fahrzeugs.

**An- und Abmeldung** (ab 2.3.0) stehen als Felder am Fahrzeug: *Status* (zugelassen, vorübergehend abgemeldet, außer Betrieb), *Zugelassen seit*, *Abgemeldet am*, *Saisonkennzeichen* und *Zulassungsstelle*. Ab 2.9.0 legst du die Abmeldebescheinigung als **Fahrzeugpapiere** ab; die Automatisierung *Abmeldung am Fahrzeug nachtragen* setzt *Abgemeldet am* und erinnert dich, den Status zu prüfen.

**Digitaler Untersuchungsbericht** (ab 2.10.0): Den Link aus dem QR-Code trägst du an der Hauptuntersuchung ein. Er wirkt wie ein Schlüssel zu deinem Bericht – gib ihn nicht weiter. Mit der Ergänzung **Fahrzeuge: Abruf beim KBA** holt die Aktion „Daten beim KBA abrufen“ die Angaben des Berichts; HSN, TSN und Gesamtmasse kommen über die Automatisierung *Fahrzeugdaten aus dem Prüfbericht übernehmen* ans Fahrzeug, nur in leere Felder.

**Gutachten / Abnahme:** *Passt zum Fahrzeug* zeigt, ob Typgenehmigung oder HSN/TSN des Fahrzeugs im Dokument stehen. Bis Ablago das selbst prüfen kann (motom001/dms#1717), wählst du es von Hand; „nicht gefunden“ heißt nur „selbst prüfen“, nie „passt nicht“. Keine Rechtsberatung. Der Kaufvertrag beim Verkauf ist ein Vertrag (Paket Verträge); ein Tipp erinnert an die Kfz-Versicherung. Fahrzeuge außer Betrieb fallen aus den Ansichten.

**Hauptuntersuchungen** stehen am Fahrzeug unter *Verknüpfungen*. Die nächste HU trägst du vorerst auch am Fahrzeug unter *HU fällig* ein; eine Automatisierung übernimmt das, sobald Ablago ein Feld in einer verknüpften Mappe setzen kann.

**Verweise:**

- **Versicherung** und **Finanzierung/Leasing** sind **Verträge** aus dem Paket Verträge – die Kfz-Versicherung mit der Vertragsart *Versicherung*, ein Leasing mit der Vertragsart *Leasing*. Das Paket Verträge rechnet aus, bis wann du kündigen musst.
- **Rechnungen** zum Fahrzeug sind **Rechnungen** aus dem Paket Rechnungen und Bestellungen mit *Betrifft* = Fahrzeug; Kilometerstand und Arbeiten stehen dort im Abschnitt *Fahrzeug*.
- **Halter** ist eine **Person** aus dem Paket Basis (Verweisart Bezug). An der Person und am Vertrag siehst du unter *Verknüpfungen*, welche Fahrzeuge auf sie verweisen.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** aus dem Paket Basis – beim Fahrzeug der Fahrzeugbrief (Zulassungsbescheinigung Teil II), z. B. im Safe.

**Vertragsarten** (für das Paket Verträge, sie bleiben nach der Installation und du kannst sie ändern):

- **Pkw-Kaufvertrag** mit der Vorlage *Kaufvertrag Gebrauchtwagen*: Am Vertrag wählst du unter *Betrifft* das Fahrzeug, der Verkäufer ist der *Anbieter*, der Käufer der *Kunde*, der Preis der *Betrag* – die Vorlage setzt Kennzeichen, Fahrzeug-Identnummer, Erstzulassung, HU und Preis ein. Ein Muster ohne Gewähr, keine Rechtsberatung.
- **Leasing** mit fester Laufzeit (Vorschlag 36 Monate), das von selbst endet.

**Ansichten:** *Fahrzeuge* mit allen Mappen des Pakets und darunter *Aktuelle Fahrzeuge* (ohne die außer Betrieb), *HU fällig* – Fahrzeuge, deren Hauptuntersuchung in den nächsten drei Monaten fällig oder schon überfällig ist – sowie *Hauptuntersuchungen*, *Zulassungsbescheinigungen*, *Gutachten / Abnahmen*, *Fahrzeugpapiere* und *Offene Rückrufe*. Fahrzeuge außer Betrieb zeigen *Aktuelle Fahrzeuge* und *HU fällig* nicht.

**Gleichbedeutende Wörter für die Suche:** *Kfz, Auto, PKW, Fahrzeug* · *HU, Hauptuntersuchung, TÜV* · *Fahrzeugbrief, Zulassungsbescheinigung Teil II* · *Fahrzeugschein, Zulassungsbescheinigung Teil I* · *Werkstattrechnung, Reparaturrechnung*. Sie stehen in Ablago unter Werkbank → Pakete → Text aus PDF und Texterkennung.

**Beispiele (optional):** das Familienauto der Familie Muster mit seiner Kfz-Versicherung (ein Vertrag) und zwei Werkstattrechnungen (Rechnungen, die das Auto betreffen), eine Hauptuntersuchung mit geringen Mängeln, die erste Zulassungsbescheinigung, ein Teilegutachten für Felgen und ein offener Rückruf – alle Nummern erfunden. Halter, Werkstatt und Ablageort „Safe“ setzt du selbst.

## Quellen

Die Werte der Auswahllisten folgen dem Datenstandard **XKfz 6.1** des Kraftfahrt-Bundesamts im XRepository (https://www.xrepository.de):

| Feld | Codeliste |
| --- | --- |
| Gutachten / Abnahme → Art | `urn:xoev-de:bund:kba:codeliste:artdesgutachtens` (2.0), ergänzt um Oldtimer-Gutachten, ABE und Teilegutachten |
| Gutachten / Abnahme → Prüforganisation | `urn:xoev-de:bund:kba:codeliste:prueforganisation` (2.0), Kurznamen, ergänzt um Hersteller |
| Fahrzeugpapiere → Art | angelehnt an `urn:xoev-de:bund:kba:codeliste:artderunterlage` |
| Fahrzeug → Feinstaubplakette | `urn:xoev-de:bund:kba:codeliste:nummerderfeinstaubplakette` |

## Voraussetzungen

- Ablago ab Version 0.293.2 (Tipp mit Texten je Sprache; Rechnungen und Bestellungen ab 0.248, Vertragsarten als Vorgaben ab 0.236)
- Pakete **Basis** ab 1.7.0, **Verträge** ab 1.1.0 und **Rechnungen und Bestellungen** ab 1.0.0 – werden bei der Installation aus dem Katalog mitinstalliert

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur den Mappentyp, Ansichten, zwei Vertragsarten und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. Je Fahrzeug eine Mappe **Fahrzeug** anlegen und *HU fällig* von der Plakette übernehmen.
2. Die Kfz-Versicherung als **Vertrag** mit der Vertragsart *Versicherung* anlegen und am Fahrzeug auswählen.
3. Rechnungen als **Rechnung** ablegen, unter *Betrifft* das Fahrzeug wählen und die Rechnung als Dokument dazulegen.
4. Nach der HU das neue Datum eintragen – die Erinnerung erledigt sich dann von selbst.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

**Update auf 2.0.0 (Werkstattrechnung zieht um):** Fahrzeuge bringt ab 2.0.0 keine *Werkstattrechnung* mehr mit. Deine Werkstattrechnungen ziehen in die Rechnung des Pakets Rechnungen, **wenn du Rechnungen 1.1.0 installierst oder aktualisierst**; Versicherung und Finanzierung zeigen auf den Vertrag, sobald **Verträge 1.1.0** die Verträge und Versicherungen aus Haushalt übernommen hat. Ablago zeigt vorher, was wohin geht, und du bestätigst mit „Gesamte Verwaltung“. Reihenfolge: erst **Verträge**, dann **Rechnungen** (je allein), dann das Update von Fahrzeuge.

**Update von 1.0.x:** Der Halter war bis 1.0.x ein Textfeld. Das Update legt den Verweis dazu, der Text bleibt. Unter **Werkbank → Pakete → Fahrzeuge → Text in Verweise umwandeln** siehst du in einer Vorschau je Name, welche Person Ablago vorschlägt oder neu anlegt; erst dann wird umgewandelt. Das lässt sich rückgängig machen.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Fahrzeuge“ im Titel.
