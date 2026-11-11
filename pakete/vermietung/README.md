# Vermietung

Das Paket **Vermietung** ist für Vermieter mit wenigen Wohnungen – das vermietete Zweifamilienhaus, die Eigentumswohnung als Altersvorsorge, die Garage nebenan. Es bringt **Mietobjekt**, **Wohnung** und **Nebenkostenabrechnung**; Mietverträge sind **Verträge** aus dem Paket Verträge (Vertragsart *Miete*), Ausgaben **Rechnungen** aus dem Paket Rechnungen. Damit liegen Verträge, Kaution, Abrechnungen und Rechnungen je Haus beisammen, Ablago erinnert an die Fristen, und die Belege für die Anlage V sind nach Jahr sortiert. Installiert wird es unter **Werkbank → Pakete**; die Pakete **Basis**, **Haus**, **Verträge** und **Rechnungen** kommen dabei automatisch mit.

> **Kein Ersatz für Steuer- oder Rechtsberatung.** Das Paket hilft beim Ordnen und erinnert an Termine. Ob eine Mieterhöhung zulässig ist, welche Kosten umlagefähig sind und was in die Anlage V gehört, klärst du mit deinem Steuerberater, einem Mieterverein bzw. Haus- und Grundbesitzerverein oder einer Anwältin.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Mietobjekt | vermietetes Haus, Eigentumswohnung, Gewerbe, Garage | Bezeichnung (eindeutig), Art, Anschrift, Baujahr, Anzahl Einheiten, Hausverwaltung, Aktenzeichen Grundsteuer | – |
| Wohnung | eine Einheit im Mietobjekt | Mietobjekt, Bezeichnung (z. B. „EG links“), Lage, Wohnfläche, Zimmer, Zähler | – |
| Nebenkostenabrechnung | Betriebskostenabrechnung eines Jahres | Mietobjekt, Abrechnungsjahr, Zeitraum, versendet am, umlagefähige Kosten, Nachzahlungen/Guthaben, Steuerjahr, Rechnungen | **Versenden bis** (60 Tage vorher) |

**Mietverträge** legst du als **Vertrag** (Paket Verträge) mit der Vertragsart *Miete* an: *Betrifft* = die Wohnung, *Kunde* = die Mieter; Mietart, Kaltmiete, Vorauszahlung, nächste Mieterhöhung und Kaution stehen im Abschnitt *Miete*. Das Paket Verträge rechnet Status, *Kündigen bis* und Ende aus. **Ausgaben** legst du als **Rechnung** (Paket Rechnungen) an: *Betrifft* = Mietobjekt oder Wohnung, dazu im Abschnitt *Vermietung* *Umlagefähig* und *Kostenart*.

**Register:** Das **Mietobjekt** zeigt seine *Wohnungen*, *Nebenkosten* (Abrechnungen) und *Ausgaben* (Rechnungen, die es betreffen); die **Wohnung** ihre *Mietverträge* und *Ausgaben*. Dazu überall *Dokumente*, *Verknüpfungen* und *Historie*.

**Verweise:**

- **Mieter** sind **Personen**, **Hausverwaltung**, **Firma** und die Bank des Kautionskontos **Organisationen** – beides aus dem Paket Basis.
- **Steuerjahr** ist ein Steuerjahr aus dem Paket Haushalt, wenn es installiert ist – dort sammelst du die Unterlagen der Einkommensteuer, zu der die Anlage V gehört.
- **Immobilie (Paket Haus)** ist optional: Führst du Wartungen und Zählerstände des Hauses im Paket Haus, verweist das Mietobjekt auf die Immobilie.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** aus dem Paket Basis – wo der unterschriebene Mietvertrag, das Übergabeprotokoll oder der Kaufvertrag liegen.

**Fristen:** Ablago erinnert unter **Zu erledigen** und in der Ansicht **Anstehend**:

- **Versenden bis** an der Nebenkostenabrechnung: Trag das Ende des Abrechnungszeitraums plus zwölf Monate ein. Danach sind Nachforderungen an die Mieter in der Regel ausgeschlossen.
- **Nächste Mieterhöhung möglich ab** am Mietvertrag (Abschnitt *Miete*): je nach Vertrag die nächste Staffel, die nächste Indexanpassung oder der früheste Termin für eine Erhöhung – das Datum trägst du selbst ein.
- **Kündigen bis** und **Endet am** am Mietvertrag rechnet das Paket Verträge aus und erinnert über seine Automatisierung „Vertrag rechtzeitig kündigen“.

**Ansichten:** *Vermietung* mit allem und darunter *Mietobjekte*, *Wohnungen*, *Mietverträge*, *Nebenkostenabrechnungen*, *Ausgaben* (darunter *dieses Jahr*, *letztes Jahr* für die Anlage V und *Umlagefähig letztes Jahr* für die nächste Abrechnung) sowie *Abrechnung offen*, *Mieterhöhung möglich* und *Vertrag endet bald*.

**Gleichbedeutende Wörter für die Suche:** *Nebenkosten, Betriebskosten* · *Nebenkostenabrechnung, Betriebskostenabrechnung* · *Kaltmiete, Nettokaltmiete, Grundmiete* · *Kaution, Mietkaution, Mietsicherheit* · *Mieter, Mietpartei*. Sie stehen in Ablago unter Werkbank → Suche.

**Beispiele (optional):** das Zweifamilienhaus Gartenstraße 8 der Familie Muster mit zwei Wohnungen, zwei Mietverträgen (einer ist gekündigt), der noch offenen Nebenkostenabrechnung 2025 und drei Rechnungen. Mieter, Verträge, Rechnungen und Abrechnung hängen schon zusammen; die Bank des Kautionskontos zeigt auf das Beispiel aus Basis, wenn du es mitinstallierst.

## Voraussetzungen

- Ablago ab Version 0.243 (für die Pakete Verträge und Rechnungen)
- Pakete **Basis** ab 1.7.0, **Haus** ab 1.0.0, **Verträge** ab 1.1.0 und **Rechnungen** ab 1.1.0 – werden bei der Installation aus dem Katalog mitinstalliert; **Haushalt** ist nicht nötig (dann bleibt das Steuerjahr leer)

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten, Automatisierungen und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. Je Haus oder Eigentumswohnung ein **Mietobjekt** anlegen, darin die **Wohnungen**.
2. Mieter als **Person** anlegen (Beziehung „Mieter/in“), dann je Mietverhältnis einen **Vertrag** mit der Vertragsart *Miete* und dem unterschriebenen Vertrag als Dokument.
3. Rechnungen rund ums Haus als **Rechnung** ablegen – *Betrifft* = Mietobjekt oder Wohnung, mit Steuerjahr und „Umlagefähig“, dann findest du sie für die Anlage V und die Nebenkostenabrechnung wieder.
4. Jedes Jahr eine **Nebenkostenabrechnung** mit *Versenden bis* anlegen; die Abrechnungen je Wohnung als Dokumente dazulegen.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

**Update auf 2.0.0 (Mietvertrag und Ausgabe ziehen um):** Vermietung bringt ab 2.0.0 keine *Mietverträge* und *Ausgaben* mehr mit. Deine Mappen ziehen um, **wenn du Verträge 1.1.0 bzw. Rechnungen 1.1.0 installierst oder aktualisierst** – Ablago zeigt vorher, was wohin geht, und du bestätigst mit „Gesamte Verwaltung“. Reihenfolge: erst **Verträge**, dann **Rechnungen** (je allein), dann das Update von Vermietung. Danach: Den *Stand* („läuft“, „gekündigt“) findest du in der Notiz – trag am Vertrag Kündigungsfrist und „Danach“ ein, dann rechnet Verträge den Status. Die alten Ansichten *Laufende Mietverträge* und *Mieterhöhung möglich* fragen noch den Stand ab; pass sie an oder lösche sie.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Vermietung“ im Titel.
