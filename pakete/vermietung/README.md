# Vermietung

Das Paket **Vermietung** ist für Vermieter mit wenigen Wohnungen – das vermietete Zweifamilienhaus, die Eigentumswohnung als Altersvorsorge, die Garage nebenan. Es bringt **Mietobjekt**, **Wohnung**, **Mietvertrag**, **Nebenkostenabrechnung** und **Ausgabe Mietobjekt**. Damit liegen Verträge, Kaution, Abrechnungen und Rechnungen je Haus beisammen, das DMS erinnert an die Fristen, und die Belege für die Anlage V sind nach Jahr sortiert. Installiert wird es unter **Werkbank → Pakete**; die Pakete **Basis**, **Haushalt** und **Haus** kommen dabei automatisch mit.

![Die fünf Mappentypen des Pakets mit ihren Feldern, Fristen, Ansichten und Beispielen](https://raw.githubusercontent.com/motom001/dms-registry/main/pakete/vermietung/bilder/ueberblick.png)

> **Kein Ersatz für Steuer- oder Rechtsberatung.** Das Paket hilft beim Ordnen und erinnert an Termine. Ob eine Mieterhöhung zulässig ist, welche Kosten umlagefähig sind und was in die Anlage V gehört, klärst du mit deinem Steuerberater, einem Mieterverein bzw. Haus- und Grundbesitzerverein oder einer Anwältin.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Mietobjekt | vermietetes Haus, Eigentumswohnung, Gewerbe, Garage | Bezeichnung (eindeutig), Art, Anschrift, Baujahr, Anzahl Einheiten, Hausverwaltung, Aktenzeichen Grundsteuer | – |
| Wohnung | eine Einheit im Mietobjekt | Mietobjekt, Bezeichnung (z. B. „EG links“), Lage, Wohnfläche, Zimmer, Zähler | – |
| Mietvertrag | ein Mietverhältnis | Wohnung, Mieter (mehrere), Stand (läuft, gekündigt, beendet), Beginn, gekündigt am, Mietart (Fest-, Staffel-, Indexmiete), Kaltmiete, Vorauszahlung, Kaution mit Konto und Rückzahlung | **Ende** (60 Tage vorher), **Nächste Mieterhöhung möglich ab** (30 Tage vorher) |
| Nebenkostenabrechnung | Betriebskostenabrechnung eines Jahres | Mietobjekt, Abrechnungsjahr, Zeitraum, versendet am, umlagefähige Kosten, Nachzahlungen/Guthaben, Steuerjahr | **Versenden bis** (60 Tage vorher) |
| Ausgabe Mietobjekt | eine Rechnung oder Kosten zum Haus | Mietobjekt, Wohnung, Art (Reparatur, Versicherung, Grundsteuer, Zinsen …), Rechnungsdatum, Betrag, auf Mieter umlegbar, Firma, Steuerjahr | – |

**Register:** Das **Mietobjekt** zeigt seine *Wohnungen*, *Nebenkosten* (Abrechnungen) und *Ausgaben*; die **Wohnung** ihre *Mietverträge* und *Ausgaben*. Dazu überall *Dokumente*, *Verknüpfungen* und *Historie*; der Mietvertrag hat eigene Register für *Miete* und *Kaution*.

**Verweise:**

- **Mieter** sind **Personen**, **Hausverwaltung**, **Firma** und die Bank des Kautionskontos **Organisationen** – beides aus dem Paket Basis.
- **Steuerjahr** ist ein Steuerjahr aus dem Paket Haushalt – dort sammelst du die Unterlagen der Einkommensteuer, zu der die Anlage V gehört.
- **Immobilie (Paket Haus)** ist optional: Führst du Wartungen und Zählerstände des Hauses im Paket Haus, verweist das Mietobjekt auf die Immobilie.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** des DMS – wo der unterschriebene Mietvertrag, das Übergabeprotokoll oder der Kaufvertrag liegen.

**Fristen:** Das DMS erinnert unter **Zu erledigen** und in der Ansicht **Anstehend**:

- **Versenden bis** an der Nebenkostenabrechnung: Trag das Ende des Abrechnungszeitraums plus zwölf Monate ein. Danach sind Nachforderungen an die Mieter in der Regel ausgeschlossen.
- **Nächste Mieterhöhung möglich ab** am Mietvertrag: je nach Vertrag die nächste Staffel, die nächste Indexanpassung oder der früheste Termin für eine Erhöhung – das Datum trägst du selbst ein.
- **Ende** am Mietvertrag: bei befristeten oder gekündigten Verträgen, mit Zeit für Übergabe und Nachmieter.

**Ansichten:** *Vermietung* mit allem und darunter *Mietobjekte*, *Wohnungen*, *Mietverträge* (darunter *Laufende Mietverträge*), *Nebenkostenabrechnungen*, *Ausgaben* (darunter *dieses Jahr*, *letztes Jahr* für die Anlage V und *Umlagefähig letztes Jahr* für die nächste Abrechnung) sowie *Abrechnung offen*, *Mieterhöhung möglich* und *Vertrag endet bald*.

**Beispiele (optional):** das Zweifamilienhaus Gartenstraße 8 der Familie Muster mit zwei Wohnungen, zwei Mietern (einer hat gekündigt), der noch offenen Nebenkostenabrechnung 2025 und drei Ausgaben. Mieter und Verträge hängen schon zusammen; Kautionskonto und Steuerjahr zeigen auf die Beispiele aus Basis und Haushalt, wenn du sie mitinstallierst.

## Voraussetzungen

- DMS ab Version 0.79 (Verweis auf den Ablageort des DMS, Verweise zwischen Beispielen)
- Pakete **Basis** ab 1.1.0 (Person), **Haushalt** ab 1.0.0 und **Haus** ab 1.0.0 – werden bei der Installation aus dem Katalog mitinstalliert

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. Je Haus oder Eigentumswohnung ein **Mietobjekt** anlegen, darin die **Wohnungen**.
2. Mieter als **Person** anlegen (Beziehung „Mieter/in“), dann je Mietverhältnis einen **Mietvertrag** mit dem unterschriebenen Vertrag als Dokument.
3. Rechnungen rund ums Haus als **Ausgabe Mietobjekt** ablegen – mit Steuerjahr und „Auf Mieter umlegbar“, dann findest du sie für die Anlage V und die Nebenkostenabrechnung wieder.
4. Jedes Jahr eine **Nebenkostenabrechnung** mit *Versenden bis* anlegen; die Abrechnungen je Wohnung als Dokumente dazulegen.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Vermietung“ im Titel.
