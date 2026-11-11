# Haushalt

Das Paket **Haushalt** bringt die typischen Unterlagen eines Haushalts fertig mit: Konten, Steuerjahre, Arbeitsverhältnisse, Vorsorge, Ausweise und Urkunden, Gesundheit, Anschaffungen und Bildung – Verträge und Versicherungen aus dem Paket **Verträge**, Rechnungen und Kassenbons aus dem Paket **Rechnungen**. Statt die Werkbank selbst einzurichten, installierst du es mit einem Klick unter **Werkbank → Pakete** und kannst sofort ablegen. Die Pakete **Basis** (Organisation, Person, Ablageort), **Verträge** und **Rechnungen** kommen dabei automatisch mit.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Konto | Girokonto, Sparkonto, Depot, Kreditkarte, Kredit, Bausparvertrag | Bank, Art, Inhaber (Personen), IBAN, Online-Zugang (Passwort), eröffnet/gekündigt am | – |
| Steuerjahr | Einkommensteuer eines Jahres | Jahr (eindeutig), abgegeben am, Bescheid vom, Erstattung/Nachzahlung, Steuerberater | **Einspruch bis** (7 Tage vorher) |
| Arbeitsverhältnis | Anstellung, Minijob, Ausbildung | Arbeitgeber, Person, Tätigkeit, Beginn, Ende, Steuerjahre | – |
| Vorsorge | Rente, Riester, Rürup, Bausparen … | Art, Anbieter, Vertragsnummer, Person, Beginn | – |
| Ausweis & Urkunde | Personalausweis, Reisepass, Führerschein, Urkunden, Zeugnisse | Art, Person, Nummer, ausgestellt am | **Gültig bis** (90 Tage vorher) |
| Gesundheit | Arztbriefe, Befunde, Impfungen, Rezepte, Rechnungen | Person, Art, Datum, Praxis, Betrag, Steuerjahr | – |
| Anschaffung | Geräte und Möbel | Gegenstand, Händler, Kaufdatum, Preis, Seriennummer, Steuerjahr; Register *Rechnungen* (Kassenbon und Rechnung aus dem Paket Rechnungen) | **Garantie bis** (30 Tage vorher) |
| Bildung | Schule, Ausbildung, Studium, Kurse | Person, Art, Einrichtung, von, bis, Abschluss, Steuerjahr | – |

**Register:** jeder Typ hat *Allgemein* (die Felder), *Dokumente*, *Verknüpfungen* und *Historie*. Das **Steuerjahr** hat zusätzlich *Belege*: Dort erscheinen alle Anschaffungen, Gesundheitsunterlagen, Bildungsnachweise, Arbeitsverhältnisse und Rechnungen, bei denen du dieses Steuerjahr eingetragen hast.

**Verträge und Versicherungen** legst du als **Vertrag** aus dem Paket Verträge an – eine Versicherung ist dort die Vertragsart *Versicherung*. Das Paket Verträge rechnet *Kündigen bis* selbst aus und erinnert rechtzeitig.

**Verweise:**

- Bank, Arbeitgeber, Anbieter, Praxis, Händler, Einrichtung und Steuerberater sind **Organisationen** aus dem Paket Basis. Eine Organisation legst du einmal an und wählst sie danach überall aus.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** aus dem Paket Basis (z. B. „Arbeitszimmer › Schrank › roter Ordner“). So findest du das Papier, wenn du das Original brauchst. Das Feld heißt in allen Typen gleich (`verbleib_original`), deshalb funktionieren gemeinsame Ansichten wie „Originale nach Ort“.
- **Inhaber** und **Person** sind **Personen** aus dem Paket Basis (Verweisart Bezug). An einer Person siehst du unter *Verknüpfungen* alles, was zu ihr gehört: Konten, Versicherungen (über *Versicherte Personen* im Vertrag), Arbeitsverhältnis, Ausweise, Arztbriefe, Zeugnisse – mit dem Paket Fahrzeuge auch ihre Fahrzeuge. 

**Fristen:** An den Datumsfeldern mit Frist erinnert Ablago rechtzeitig unter **Zu erledigen** und in der Ansicht **Anstehend** – bei der Hauptfälligkeit einer Versicherung jedes Jahr wieder.

**Ansichten:** *Haushalt* mit allen Unterlagen und darunter

- je eine Ansicht pro Mappentyp (*Konten*, *Steuerjahre* … *Bildung*), dazu *Verträge* und *Versicherungen* (Verträge mit ausgefüllter Versicherung) aus dem Paket Verträge; unter *Versicherungen* die *Sachversicherungen* (Haftpflicht, Hausrat, Wohngebäude, Kfz, Rechtsschutz) und die *Personenversicherungen* (Berufsunfähigkeit, Leben, Kranken-Zusatz, Reise, Unfall),
- *Kündigung in den nächsten 3 Monaten* – Verträge und Versicherungen, bei denen „Kündigen bis“ in den nächsten drei Monaten liegt,
- *Läuft bald ab* – Ausweise, die in den nächsten sechs Monaten ablaufen oder schon abgelaufen sind,
- *Garantie läuft ab* – Anschaffungen, deren Garantie in den nächsten drei Monaten endet.

**Beispiele (optional):** 13 Mappen der erfundenen Familie Muster – Lena, Tom und Sohn Jonas als **Personen**, je Typ ein bis zwei Mappen. Sie hängen zusammen: Das Girokonto gehört Lena und Tom und zeigt auf die Sparkasse, Jonas’ Impfung auf die Praxis Dr. Beispiel (aus dem Paket Basis), Toms Arbeitsverhältnis auf das Steuerjahr 2025. Ablageorte setzt du selbst.

## Voraussetzungen

- Ablago ab Version 0.243 (für die Pakete Verträge und Rechnungen)
- Pakete **Basis** ab 1.7.0, **Verträge** ab 1.1.0 und **Rechnungen** ab 1.1.0 – werden bei der Installation aus dem Katalog mitinstalliert

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten und auf Wunsch Beispiel-Mappen an.

## Wer was sehen darf

Nicht alles gehört vor alle Augen: Gesundheitsunterlagen und Konten (mit den Zugangsdaten zum Online-Banking) sollen meist nur die Eltern sehen. Das Paket schreibt dafür nichts vor – du richtest es nach der Installation selbst ein. Berechtigungen pflegst du am **Mappentyp** (Werkbank → Mappentypen → *Gesundheit* bzw. *Konto*, Abschnitt **Berechtigungen**). Ein Beispiel:

1. Unter **Werkbank → Benutzer** eine Rolle **Eltern** anlegen und Lena und Tom geben.
2. Am Mappentyp **Gesundheit** eine Regel anlegen: **Nur Eltern** – wenn *Benutzer hat nicht Rolle Eltern* → **✗ C R U D P**.
3. Dieselbe Regel mit **Regel in andere Mappentypen kopieren** auch an den Mappentyp **Konto** geben und **Mappentyp speichern**.
4. Im **Testlauf** darunter mit dem Benutzer von Jonas prüfen: Er darf keine Gesundheits- oder Kontomappe lesen.

Wer nur die Passwörter schützen will, entzieht statt **R** nur **P** (Passwörter sehen). Mehr dazu im Administratorhandbuch unter „Berechtigungen“.

## Nach der Installation

1. Die eigenen Banken, Versicherer, Ärzte und Firmen als **Organisation** anlegen (oder aus der Post heraus).
2. Unter **Ablage → Ablageorte** die Orte anlegen, an denen Papier liegt.
3. Verträge, Versicherungen und Ausweise ablegen; die Fristen erinnern von selbst (an „Kündigen bis“ das Paket Verträge).
4. Die Beispiel-Mappen löschen, sobald du sie nicht mehr brauchst.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

**Update auf 2.0.0 (Vertrag und Versicherung ziehen um):** Haushalt bringt ab 2.0.0 keine eigenen Typen *Vertrag* und *Versicherung* mehr mit. Deine Mappen ziehen in den Vertrag des Pakets Verträge, **wenn du Verträge 1.1.0 installierst oder aktualisierst** – Ablago zeigt vorher, was wohin geht, und du bestätigst mit „Gesamte Verwaltung“. Reihenfolge: erst **Verträge** (allein), dann **Rechnungen**, dann das Update von Haushalt. Einzelheiten im README von Verträge, Abschnitt „Umzug aus Haushalt und Vermietung“.

**Update von 1.0.x:** Inhaber, Versichert und Person waren bis 1.0.x Textfelder. Das Update legt die Verweise dazu, die Texte bleiben. Unter **Werkbank → Pakete → Haushalt → Text in Verweise umwandeln** siehst du je Feld in einer Vorschau, welche Person Ablago je Name vorschlägt oder neu anlegt („Lena und Tom Muster“ wird zu zwei Personen); „Familie“ oder „gemeinsam“ überspringst du. Erst dann wird umgewandelt, und es lässt sich rückgängig machen.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Haushalt“ im Titel.
