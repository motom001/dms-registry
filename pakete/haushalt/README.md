# Haushalt

Das Paket **Haushalt** bringt die typischen Unterlagen eines Haushalts fertig mit: Konten, Verträge, Versicherungen, Steuerjahre, Arbeitsverhältnisse, Vorsorge, Ausweise und Urkunden, Gesundheit, Anschaffungen und Bildung. Statt die Werkbank selbst einzurichten, installierst du es mit einem Klick unter **Werkbank → Pakete** und kannst sofort ablegen. Das Paket **Basis** (Organisation) kommt dabei automatisch mit.

![Die zehn Mappentypen des Pakets mit ihren Feldern, Fristen und Beispielen](https://raw.githubusercontent.com/motom001/dms-registry/main/pakete/haushalt/bilder/ueberblick.png)

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Konto | Girokonto, Sparkonto, Depot, Kreditkarte, Kredit, Bausparvertrag | Bank, Art, Inhaber, IBAN, Online-Zugang (Passwort), eröffnet/gekündigt am | – |
| Vertrag | Strom, Gas, Internet, Mobilfunk, Streaming, Miete, Mitgliedschaft … | Vertragspartner, Art, Vertragsnummer, Beginn, Mindestlaufzeit, Kündigungsfrist, Betrag, Zahlweise | **Kündigen bis** (30 Tage vorher) |
| Versicherung | Haftpflicht, Hausrat, Kfz, Berufsunfähigkeit … | Versicherer, Art, Versicherungsnummer, Versichert, Beitrag, Zahlweise | **Hauptfälligkeit** (jährlich, 6 Wochen vorher), **Kündigen bis** (30 Tage vorher) |
| Steuerjahr | Einkommensteuer eines Jahres | Jahr (eindeutig), abgegeben am, Bescheid vom, Erstattung/Nachzahlung, Steuerberater | **Einspruch bis** (7 Tage vorher) |
| Arbeitsverhältnis | Anstellung, Minijob, Ausbildung | Arbeitgeber, Person, Tätigkeit, Beginn, Ende, Steuerjahre | – |
| Vorsorge | Rente, Riester, Rürup, Bausparen … | Art, Anbieter, Vertragsnummer, Person, Beginn | – |
| Ausweis & Urkunde | Personalausweis, Reisepass, Führerschein, Urkunden, Zeugnisse | Art, Person, Nummer, ausgestellt am | **Gültig bis** (90 Tage vorher) |
| Gesundheit | Arztbriefe, Befunde, Impfungen, Rezepte, Rechnungen | Person, Art, Datum, Praxis, Betrag, Steuerjahr | – |
| Anschaffung | Geräte und Möbel mit Kassenbon | Gegenstand, Händler, Kaufdatum, Preis, Seriennummer, Steuerjahr | **Garantie bis** (30 Tage vorher) |
| Bildung | Schule, Ausbildung, Studium, Kurse | Person, Art, Einrichtung, von, bis, Abschluss, Steuerjahr | – |

**Register:** jeder Typ hat *Allgemein* (die Felder), *Dokumente*, *Verknüpfungen* und *Historie*. Das **Steuerjahr** hat zusätzlich *Belege*: Dort erscheinen alle Anschaffungen, Gesundheitsunterlagen, Bildungsnachweise und Arbeitsverhältnisse, bei denen du dieses Steuerjahr eingetragen hast.

**Verweise:**

- Bank, Vertragspartner, Versicherer, Arbeitgeber, Anbieter, Praxis, Händler, Einrichtung und Steuerberater sind **Organisationen** aus dem Paket Basis. Eine Organisation legst du einmal an und wählst sie danach überall aus.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** des DMS (z. B. „Arbeitszimmer › Schrank › roter Ordner“). So findest du das Papier, wenn du das Original brauchst. Das Feld heißt in allen Typen gleich (`verbleib_original`), deshalb funktionieren gemeinsame Ansichten wie „Originale nach Ort“.
- **Person** ist vorerst ein Textfeld („Erika Muster“). Ein eigener Mappentyp für Personen kommt später mit dem Paket Basis.

**Fristen:** An den Datumsfeldern mit Frist erinnert das DMS rechtzeitig unter **Zu erledigen** und in der Ansicht **Anstehend** – bei der Hauptfälligkeit einer Versicherung jedes Jahr wieder.

**Ansichten:** *Haushalt* mit allen Unterlagen und darunter

- je eine Ansicht pro Mappentyp (*Konten*, *Verträge*, *Versicherungen* … *Bildung*); unter *Versicherungen* die *Sachversicherungen* (Haftpflicht, Hausrat, Wohngebäude, Kfz, Rechtsschutz) und die *Personenversicherungen* (Berufsunfähigkeit, Leben, Kranken-Zusatz, Reise, Unfall),
- *Kündigung in den nächsten 3 Monaten* – Verträge und Versicherungen, bei denen „Kündigen bis“ in den nächsten drei Monaten liegt,
- *Läuft bald ab* – Ausweise, die in den nächsten sechs Monaten ablaufen oder schon abgelaufen sind,
- *Garantie läuft ab* – Anschaffungen, deren Garantie in den nächsten drei Monaten endet.

**Beispiele (optional):** 15 Mappen der erfundenen Familie Muster (Erika, Max und Lena) – je Typ ein bis zwei, dazu die Kfz-Versicherung fürs Paket Fahrzeuge. Sie hängen zusammen: Das Girokonto zeigt auf die Sparkasse, der Stromvertrag auf die Stadtwerke, die Impfung auf die Praxis Dr. Beispiel (alle aus dem Paket Basis), Max’ Arbeitsverhältnis auf das Steuerjahr 2025. Ablageorte setzt du selbst.

## Voraussetzungen

- DMS ab Version 0.79 (Verweis auf den Ablageort des DMS, Verweise zwischen Beispielen)
- Paket **Basis** ab 1.0.0 – wird bei der Installation aus dem Katalog mitinstalliert

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten und auf Wunsch Beispiel-Mappen an.

## Wer was sehen darf

Nicht alles gehört vor alle Augen: Gesundheitsunterlagen und Konten (mit den Zugangsdaten zum Online-Banking) sollen meist nur die Eltern sehen. Das Paket schreibt dafür nichts vor – du richtest es nach der Installation selbst ein. Berechtigungen pflegst du am **Mappentyp** (Werkbank → Mappentypen → *Gesundheit* bzw. *Konto*, Abschnitt **Berechtigungen**). Ein Beispiel:

1. Unter **Werkbank → Benutzer** eine Rolle **Eltern** anlegen und Erika und Max geben.
2. Am Mappentyp **Gesundheit** eine Regel anlegen: **Nur Eltern** – wenn *Benutzer hat nicht Rolle Eltern* → **✗ C R U D P**.
3. Dieselbe Regel mit **Regel in andere Mappentypen kopieren** auch an den Mappentyp **Konto** geben und **Mappentyp speichern**.
4. Im **Testlauf** darunter mit Lenas Benutzer prüfen: Sie darf keine Gesundheits- oder Kontomappe lesen.

Wer nur die Passwörter schützen will, entzieht statt **R** nur **P** (Passwörter sehen). Mehr dazu im Administratorhandbuch unter „Berechtigungen“.

## Nach der Installation

1. Die eigenen Banken, Versicherer, Ärzte und Firmen als **Organisation** anlegen (oder aus der Post heraus).
2. Unter **Ablage → Ablageorte** die Orte anlegen, an denen Papier liegt.
3. Verträge, Versicherungen und Ausweise ablegen; die Fristen erinnern von selbst.
4. Die Beispiel-Mappen löschen, sobald du sie nicht mehr brauchst.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Haushalt“ im Titel.
