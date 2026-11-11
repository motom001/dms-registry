# Verträge

Ein Mappentyp für **alle Verträge** – Strom, Internet, Handy, Streaming, Mitgliedschaft, Miete, Versicherung und im Betrieb dieselben mit mehr Angaben. Du trägst ein, **was es ist, bei wem und wie lange es läuft**; das Paket rechnet aus, **bis wann du kündigen musst**, wann der Vertrag endet und was er im Monat kostet, und erinnert die zuständige Person rechtzeitig.

> Berechnet aus deinen Angaben, **ohne Gewähr und ohne Rechtsberatung**. Maßgeblich ist, was im Vertrag steht.

## Inhalt

| Mappentyp | wofür | wichtige Felder |
| --- | --- | --- |
| Vertrag | jeder Vertrag mit Laufzeit oder Kündigungsfrist | Bezeichnung, Anbieter, Vertragsart, Zuständig, **Kündigen bis**, **Status** |
| Vertragsart | Art eines Vertrags mit üblichen Fristen und Vorlagen | Name, Für (privat/beruflich/beides), übliche Mindestlaufzeit, Verlängerung, Kündigungsfrist, Kündigung zum |

### Vertrag

| Teil | Felder |
| --- | --- |
| oben | Bezeichnung (Pflicht), **Anbieter** (`von`), **Vertragsart**, **Zuständig**, *Kündigen bis*, *Status* |
| Vertragsparteien | **Kunde** (`an`, leer heißt: wir), Vertragsnummer (Anbieter) |
| Laufzeit und Kündigung | Beginn, Mindestlaufzeit, Danach (verlängert sich um … / läuft unbefristet weiter / endet), Verlängert sich um, Vertragsende, Kündigungsfrist, Kündigung zum (Laufzeitende, Monats-, Quartals-, Jahresende, jederzeit), Gekündigt am, Kündigung bestätigt am, *Frühestens zu Ende am*, *Nächste Verlängerung*, *Endet am*, *Laufzeit in Monaten* |
| Kosten | Betrag, Zahlweise, *Pro Monat* |
| Weiteres | Gehört zu (übergeordneter Vertrag, z. B. Familientarif), Verbleib Original, Bemerkungen |
| Abschluss | nur, wenn Anbieter oder Kunde eine **eigene Organisation** ist (Basis): von uns / von der Gegenseite unterschrieben am, interne Nummer, Ansprechpartner |
| Miete | nur bei Vertragsart Miete: Mietart, Kaltmiete, Vorauszahlung, Sonstiges, nächste Mieterhöhung, Kaution, Kautionskonto, Kaution zurück am |
| Versicherung | nur bei Vertragsart Versicherung: Versicherung (Haftpflicht, Hausrat …), versicherte Personen, Selbstbeteiligung, Hauptfälligkeit |

*Kursiv* = berechnet: Diese Felder schreibt nur das Paket, in Ablago sind sie nur lesbar. Register: *Vertrag*, *Dokumente*, *Verknüpfungen* (z. B. Rechnungen zum Vertrag aus dem Paket Rechnungen), *Historie*.

## So rechnet das Paket

- **Erste Laufzeit:** Beginn plus Mindestlaufzeit, einen Tag weniger (24 Monate ab 15.03.2026 enden am 14.03.2028). Fristen wie im BGB: ein Monat ab dem 15.01. endet am 15.02.
- **Verlängert sich um …:** weitere Laufzeiten gleicher Länge. Gekündigt wird zum Ende einer Laufzeit; *Kündigen bis* ist der letzte Tag, an dem die Kündigung ankommen muss.
- **Läuft unbefristet weiter** (viele Verbraucherverträge seit März 2022): Vor dem Ende der ersten Laufzeit gibt es ein *Kündigen bis*; danach ist der Vertrag jederzeit mit der Frist kündbar, ggf. zum Monats-, Quartals- oder Jahresende. Dann gibt es kein *Kündigen bis* mehr (sonst käme jeden Monat eine Erinnerung), der Status sagt, wann er frühestens endet.
- **Endet:** Der Vertrag endet von selbst zum Vertragsende.
- **Gekündigt am** gefüllt: *Endet am* ist das Ende nach der Kündigung, der Status „gekündigt zum …“ (mit „Bestätigung fehlt noch“, bis *Kündigung bestätigt am* gefüllt ist), danach „beendet am …“.
- **Pro Monat:** Betrag geteilt durch 1, 3, 6 oder 12 nach der Zahlweise; bei „einmalig“ leer.
- Gerechnet wird bei jeder Änderung eines Vertrags und jeden Morgen über die mitgelieferte Automatisierung **„Verträge täglich prüfen“** (gleich eingeschaltet; Uhrzeit und Tage stellst du unter Automatisierungen ein). Das Paket schreibt nur die berechneten Felder und nur, wenn sich etwas ändert. Hat inzwischen jemand dasselbe Feld geändert, lässt es den Wert stehen.

Beispiele für den Status: „läuft – kündigen bis 14.02.2028, Ende dann 14.03.2028“ · „läuft – jederzeit kündbar mit 3 Monaten zum Monatsende, frühestens zum 28.02.2027“ · „läuft – endet am 31.12.2026 von selbst“ · „gekündigt zum 20.06.2028“ · „beendet am 20.06.2028“.

## Vertragsarten

Mitgeliefert (als Vorgaben, sie bleiben nach der Installation und du kannst sie ändern): Strom, Gas, Wasser, Internet, Mobilfunk, Streaming, Zeitschrift, Mitgliedschaft, Miete, Versicherung, Sonstiges. Wählst du am Vertrag eine Vertragsart, schlägt Ablago ihre üblichen Fristen in leere Felder vor. Eigene Vertragsarten legst du einfach dazu; in ihr Register *Vorlagen* kommen später Vorlagen wie ein Kündigungsschreiben (dms-registry #160).

## Erinnerung

Die mitgelieferte Automatisierung **„Vertrag rechtzeitig kündigen“** ist nach der Installation aus. Eingeschaltet bekommt *Zuständig* (sonst, wer den Vertrag angelegt hat) 30 Tage vor *Kündigen bis* eine Aufgabe – bei Abwesenheit die Vertretung. Die Aufgabe erledigt sich selbst, wenn *Kündigen bis* sich ändert oder leer wird, z. B. weil du *Gekündigt am* eingetragen hast.

## Einstellungen

| Einstellung | Vorgabe | Bedeutung |
| --- | --- | --- |
| Status und Fristen ausrechnen | an | Aus: Die berechneten Felder bleiben, wie sie sind. |

## Voraussetzungen

- Ablago ab 0.238.0: Zeitraum, Anzeige-Bedingungen, mehrere Ziele, berechnete Felder, „Paket nach Zeitplan ausführen“, Vorbelegen, Vorgaben und eigene Organisation (Etappe 15).
- Paket Basis ab 1.7.0.

## Rechte und Netzwerkzugriff

- **Mappen lesen:** Vertrag, Vertragsart · **Mappen anlegen und ändern:** Vertrag – das Paket schreibt nur die berechneten Felder.
- Keine Dokumente, **kein Zugriff auf Netzwerk und Internet**.
- Reagiert auf: `mappe.angelegt`, `mappe.geaendert` (Verträge), `zeitplan.ausgefuehrt` (Automatisierung „Verträge täglich prüfen“), `paket.einstellungen_geaendert`.

## Entwickeln

| Datei | Inhalt |
| --- | --- |
| [`code/berechnung.h`](code/berechnung.h) | die Berechnung (Datum, Fristen, Laufzeiten, Status) – ohne Ablago testbar |
| [`code/vertraege.cpp`](code/vertraege.cpp) | Ereignisse, Lesen und Schreiben über die API |
| [`tests/berechnung_test.cpp`](tests/berechnung_test.cpp) | typische Verträge (Handy, Versicherung, Miete, befristet, Streaming); läuft nativ in `code/bauen.sh` |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | das gebaute Modul gegen eine Nachbildung von Ablago |

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Verträge“ im Titel.
