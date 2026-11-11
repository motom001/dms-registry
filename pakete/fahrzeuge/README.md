# Fahrzeuge

Das Paket **Fahrzeuge** bringt den Mappentyp **Fahrzeug** und die Vertragsarten **Pkw-Kaufvertrag** und **Leasing**. Damit verpasst du die HU nicht, findest Fahrzeugbrief und Versicherung schnell und hast beim Verkauf alle Rechnungen beisammen. Installiert wird es unter **Werkbank → Pakete**; die Pakete **Basis**, **Verträge** und **Rechnungen** kommen dabei automatisch mit.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Fahrzeug | Pkw, Motorrad, Wohnmobil, Anhänger, E-Bike | Bezeichnung, Art, Kennzeichen (eindeutig), Fahrzeug-Identnummer, Erstzulassung, Halter (Person), Verantwortlich, Versicherung, Finanzierung/Leasing | **HU fällig** (einen Monat vorher) |

**Register:** Das **Fahrzeug** zeigt unter *Rechnungen* alle Rechnungen aus dem Paket Rechnungen, bei denen *Betrifft* dieses Fahrzeug ist – Werkstatt, Reifen, Zubehör; dazu *Dokumente*, *Verknüpfungen* und *Historie*.

**Verweise:**

- **Versicherung** und **Finanzierung/Leasing** sind **Verträge** aus dem Paket Verträge – die Kfz-Versicherung mit der Vertragsart *Versicherung*, ein Leasing mit der Vertragsart *Leasing*. Das Paket Verträge rechnet aus, bis wann du kündigen musst.
- **Rechnungen** zum Fahrzeug sind **Rechnungen** aus dem Paket Rechnungen mit *Betrifft* = Fahrzeug; Kilometerstand und Arbeiten stehen dort im Abschnitt *Fahrzeug*.
- **Halter** ist eine **Person** aus dem Paket Basis (Verweisart Bezug). An der Person und am Vertrag siehst du unter *Verknüpfungen*, welche Fahrzeuge auf sie verweisen.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** aus dem Paket Basis – beim Fahrzeug der Fahrzeugbrief (Zulassungsbescheinigung Teil II), z. B. im Safe.

**Vertragsarten** (für das Paket Verträge, sie bleiben nach der Installation und du kannst sie ändern):

- **Pkw-Kaufvertrag** mit der Vorlage *Kaufvertrag Gebrauchtwagen*: Am Vertrag wählst du unter *Betrifft* das Fahrzeug, der Verkäufer ist der *Anbieter*, der Käufer der *Kunde*, der Preis der *Betrag* – die Vorlage setzt Kennzeichen, Fahrzeug-Identnummer, Erstzulassung, HU und Preis ein. Ein Muster ohne Gewähr, keine Rechtsberatung.
- **Leasing** mit fester Laufzeit (Vorschlag 36 Monate), das von selbst endet.

**Ansichten:** *Fahrzeuge* und darunter *Alle Fahrzeuge*, *Rechnungen zu Fahrzeugen* und *HU fällig* – Fahrzeuge, deren Hauptuntersuchung in den nächsten drei Monaten fällig oder schon überfällig ist.

**Gleichbedeutende Wörter für die Suche:** *Kfz, Auto, PKW, Fahrzeug* · *HU, Hauptuntersuchung, TÜV* · *Fahrzeugbrief, Zulassungsbescheinigung Teil II* · *Fahrzeugschein, Zulassungsbescheinigung Teil I* · *Werkstattrechnung, Reparaturrechnung*. Sie stehen in Ablago unter Werkbank → Suche.

**Beispiele (optional):** das Familienauto der Familie Muster mit seiner Kfz-Versicherung (ein Vertrag) und zwei Werkstattrechnungen (Rechnungen, die das Auto betreffen). Halter, Werkstatt und Ablageort „Safe“ setzt du selbst.

## Voraussetzungen

- Ablago ab Version 0.243 (für die Pakete Verträge und Rechnungen; Vertragsarten als Vorgaben ab 0.236)
- Pakete **Basis** ab 1.7.0, **Verträge** ab 1.1.0 und **Rechnungen** ab 1.1.0 – werden bei der Installation aus dem Katalog mitinstalliert

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
