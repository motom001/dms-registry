# Gesundheit

Das Paket **Gesundheit** ordnet Gesundheitsunterlagen nach ihrem **Verlauf**: Aus einer Diagnose folgen Befunde, Therapien, Krankschreibungen und Rechnungen. Dazu kommen Medikamentenplan, Impfpass, U-Heft und einzelne Impfungen – für Familien wie die von Lena und für alle, die Unterlagen der Eltern mit im Blick haben.

## Inhalt

```
Person ── Behandlungsfall (z. B. „Bandscheibenvorfall L5“)
            ├─ Arztbriefe & Befunde
            ├─ Therapien
            ├─ Arbeitsunfähigkeit
            └─ Rechnungen (Paket Rechnungen und Bestellungen, Betrifft = Behandlungsfall)
```

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Behandlungsfall | Erkrankung oder Anlass, vom Verdacht bis zum Abschluss | Person, Bezeichnung, ICD-Code, Fachgebiet, behandelnde Praxis, festgestellt am, Status (in Abklärung, in Behandlung, chronisch, abgeschlossen) | – |
| Arztbrief & Befund | Arztbericht, Befund, Labor, Röntgen/MRT/CT, OP-Bericht, Entlassungsbrief | Art, Datum, Person, Praxis/Klinik, Behandlungsfall, **wichtig** | – |
| Therapie | Medikament, Physiotherapie, Operation, Reha, Psychotherapie, Hilfsmittel | Behandlungsfall, Art, Bezeichnung, verordnet von, von/bis, Einheiten, Status | **Verordnung gültig bis** (7 Tage vorher) |
| Arbeitsunfähigkeit | AU-Bescheinigung (seit der eAU die Ausfertigung für dich) | Person, von, bis, Erst-/Folgebescheinigung, Arbeitsunfall, Ärztin/Arzt, Behandlungsfall, Arbeitsverhältnis (Paket Haushalt) | – |
| Medikamentenplan | der aktuelle Plan einer Person | Person, Stand vom, ausgestellt von, **ersetzt** den vorigen Plan | – |
| Gesundheitspass | Impfpass, U-Heft, Mutterpass, Allergie-, Röntgen-, Implantat-, Brillenpass, Blutspende-, Organspende-, Notfallausweis, Zahn-Bonusheft | Person, Art, ausgestellt am, letzter Eintrag am, Verbleib Original | **Nächster Termin** (14 Tage vorher) |
| Impfung | eine einzelne Impfung | Person, gegen, Datum, Impfstoff, eingetragen in (Impfpass) | **Nächste Auffrischung** (30 Tage vorher) |

**Register:** jeder Typ hat *Allgemein*, *Dokumente*, *Verknüpfungen* und *Historie*. Beim Behandlungsfall heißen die Verknüpfungen **Verlauf** – dort steht alles, was auf ihn zeigt.

**Kein eigener Typ:** Kranken-, Pflege- und Zusatzversicherung sind **Verträge** (Paket Verträge, Versicherungsarten „Krankenversicherung“, „Pflegeversicherung“, „Kranken-Zusatz“); die Mitgliedsbescheinigung ist ein Dokument am Vertrag. Arztrechnungen sind **Rechnungen** mit *Betrifft* = Behandlungsfall und gern einem Steuerjahr.

**Ansichten:** *Gesundheit* mit allem, darunter je Typ eine Ansicht und **Wichtige Befunde** (Arztbriefe und Befunde mit Haken *wichtig*). Die Fristen kommen später unter *Fristen*.

**Automatisierungen** (nach der Installation aus): Verordnung läuft ab, nächster Termin laut Pass, Impfung auffrischen.

**Beispiele (optional):** für die erfundene Familie Muster (Personen aus Basis) Jonas' U-Heft, Lenas Impfpass mit einer Tetanus-Impfung und Toms Behandlungsfall „Rückenschmerzen nach dem Umzug“ mit einem wichtigen Befund aus der Hausarztpraxis und Krankengymnastik.

**Bisher woanders:** Bis Haushalt 4.x gab es dort den Typ „Gesundheit“. Einen Umzug gibt es nicht.

## Wer was sehen darf

Gesundheitsdaten sind besonders schutzwürdig. **Nach der Installation sieht jede Person mit eigenem Zugang alle Gesundheits-Mappen** – das Paket bringt (noch) keine Regeln mit. Richte deshalb gleich Berechtigungen ein, etwa so:

1. Unter **Werkbank → Benutzer** eine Rolle **Eltern** anlegen und Lena und Tom geben.
2. Am Mappentyp **Behandlungsfall** eine Regel anlegen: **Nur Eltern** – wenn *Benutzer hat nicht Rolle Eltern* → **✗ C R U D P**.
3. Mit **Regel in andere Mappentypen kopieren** dieselbe Regel an alle Typen dieses Pakets geben und speichern.
4. Im **Testlauf** mit dem Benutzer von Jonas prüfen: Er darf keine Gesundheits-Mappe lesen.

Feiner geht es mit einer Regel je Person, z. B. „Mappen, deren Person Markus ist, sieht nur Markus“. Mehr im Administratorhandbuch unter „Berechtigungen“.

**KI-Dienste:** Mappentypen aus Paketen sind für KI-Dienste gesperrt, bis die Verwaltung sie ausdrücklich zulässt. Wir empfehlen, die Gesundheits-Typen **nicht** für KI-Dienste zuzulassen.

## Voraussetzungen

- Ablago ab Version 0.248
- Paket **Basis** ab 1.10.0 – kommt bei der Installation aus dem Katalog mit. Mit **Rechnungen und Bestellungen** ab 1.2.2 kann *Betrifft* einer Rechnung ein Behandlungsfall sein; mit **Haushalt** zeigt die Arbeitsunfähigkeit auf das Arbeitsverhältnis.

## Rechte und Netz

Dieses Paket enthält keinen Code und geht nicht ins Netz. Es legt nur Mappentypen, Ansichten, Automatisierungen und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. **Berechtigungen einrichten** (siehe oben).
2. Praxen und Kliniken als **Organisation** anlegen, Ärztinnen und Ärzte bei Bedarf als **Person**.
3. Für eine Erkrankung einen Behandlungsfall anlegen und Arztbriefe, Befunde und Therapien darauf zeigen lassen.
4. Unter Werkbank → Automatisierungen die Erinnerungen einschalten, die du brauchst.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit dem Paketnamen im Titel.
