# Haushalt

Das Paket **Haushalt** bringt die typischen Unterlagen eines Haushalts fertig mit: Arbeitsverhältnisse, Vorsorge, Anschaffungen und Bildung – Konten und Steuerjahre aus dem Paket **Finanzen**, Verträge und Versicherungen aus dem Paket **Verträge**, Rechnungen und Kassenbons aus dem Paket **Rechnungen und Bestellungen**. Statt die Werkbank selbst einzurichten, installierst du es mit einem Klick unter **Werkbank → Pakete** und kannst sofort ablegen. Die Pakete **Basis** (Organisation, Person, Ablageort), **Finanzen**, **Verträge** und **Rechnungen und Bestellungen** kommen dabei automatisch mit.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Arbeitsverhältnis | Anstellung, Minijob, Ausbildung | Arbeitgeber, Person, Tätigkeit, Beginn, Ende, Steuerjahre | – |
| Arbeitsmedizinische Vorsorge (ab 3.3.0) | Vorsorgebescheinigung nach ArbMedVV, eine Mappe je Anlass (Befunde gehören ins Paket **Gesundheit**) | Person, Arbeitsverhältnis, Datum, Ärztin/Arzt, Anlass, Art (Pflicht-, Angebots-, Wunschvorsorge) | **Nächste Vorsorge** (6 Wochen vorher; leer = keine weitere nötig) |
| Vorsorge | Rente, Riester, Rürup … (Bausparverträge sind Konten im Paket Finanzen) | Art, Anbieter, Vertragsnummer, Person, Beginn | – |
| Anschaffung | Geräte und Möbel | Gegenstand, Händler, Kaufdatum, Preis, Seriennummer, Steuerjahr; Register *Rechnungen* (Kassenbon und Rechnung aus dem Paket Rechnungen und Bestellungen) | **Garantie bis** (30 Tage vorher) |
| Bildung | Schule, Ausbildung, Studium, Kurse | Person, Art, Einrichtung, von, bis, Abschluss, Steuerjahr | – |

**Register:** jeder Typ hat *Allgemein* (die Felder), *Dokumente*, *Verknüpfungen* und *Historie*.

**Wohin mit Briefen ohne eigene Sache?** Ein Schreiben legst du als Dokument zu der Sache, um die es geht: Teilt der Arbeitgeber mit, dass das Gehalt künftig später kommt, gehört der Brief zum **Arbeitsverhältnis**. Weitere Beispiele: neue AGB der Bank → Konto, Preisänderung der Stadtwerke → Vertrag, neuer Beitragssatz der Krankenkasse → Versicherung. Gibt es keine Sache, leg ihn beim Absender (Organisation aus Basis) unter *Dokumente* ab. Einen eigenen Mappentyp für Hinweisschreiben gibt es bewusst nicht.

**Konten und Steuerjahre** kommen aus dem Paket **Finanzen**. Trägst du an einer Anschaffung, einem Bildungsnachweis oder einem Arbeitsverhältnis ein *Steuerjahr* ein, steht die Mappe dort unter *Belege*.

**Verträge und Versicherungen** legst du als **Vertrag** aus dem Paket Verträge an – eine Versicherung ist dort die Vertragsart *Versicherung*. Das Paket Verträge rechnet *Kündigen bis* selbst aus und erinnert rechtzeitig.

**Verweise:**

- Arbeitgeber, Anbieter, Praxis, Händler und Einrichtung sind **Organisationen** aus dem Paket Basis. Eine Organisation legst du einmal an und wählst sie danach überall aus.
- **Verbleib Originaldokumente** zeigt auf einen **Ablageort** aus dem Paket Basis (z. B. „Arbeitszimmer › Schrank › roter Ordner“). So findest du das Papier, wenn du das Original brauchst. Das Feld heißt in allen Typen gleich (`verbleib_original`), deshalb funktionieren gemeinsame Ansichten wie „Originale nach Ort“.
- **Person** ist eine **Person** aus dem Paket Basis (Verweisart Bezug). An einer Person siehst du unter *Verknüpfungen* alles, was zu ihr gehört: Konten (Paket Finanzen), Versicherungen (über *Versicherte Personen* im Vertrag), Arbeitsverhältnis, Arztbriefe, Zeugnisse – mit dem Paket Fahrzeuge auch ihre Fahrzeuge. 

**Fristen:** An den Datumsfeldern mit Frist erinnert Ablago rechtzeitig unter **Zu erledigen** und in der Ansicht **Anstehend** – bei der Hauptfälligkeit einer Versicherung jedes Jahr wieder.

**Ansichten:** *Haushalt* mit allen Unterlagen und darunter

- je eine Ansicht pro Mappentyp (*Arbeitsverhältnisse* … *Bildung*), jede mit Symbol,
- *Garantie läuft ab* – Anschaffungen, deren Garantie in den nächsten drei Monaten endet.

Verträge und Versicherungen (mit Sach- und Personenversicherungen) zeigt das Paket **Verträge** in seinen Ansichten.

**Beispiele (optional):** 10 Mappen der erfundenen Familie Muster – Lena, Tom und Sohn Jonas sind ab 4.0.0 **Personen** aus den Beispielen von Basis; je Typ ein bis zwei Mappen, dazu Konten, ein Kontoauszug, ein Freistellungsauftrag und das Steuerjahr 2025 aus dem Paket Finanzen. Sie hängen zusammen: Das Girokonto gehört Lena und Tom und zeigt auf die Sparkasse, Jonas’ Impfung auf die Hausarztpraxis (aus dem Paket Basis), Toms Arbeitsverhältnis auf das Steuerjahr 2025. Ablageorte setzt du selbst.

**Tipps:** Ein Tipp führt zu *Garantie bis* an der Anschaffung. Den Rundgang „Ausweis ablegen“ bringt ab 4.0.0 das Paket „Ämter & Papiere“ mit.

**Gesundheit** (bis 4.x hier ein Mappentyp) bringt ab 5.0.0 das eigene Paket **Gesundheit** mit – mit Behandlungsfall, Befunden, Therapien, Impfungen und Pässen.

**Ausweise und Urkunden** (bis 3.x hier als „Ausweis & Urkunde“) legst du ab 4.0.0 im Paket **„Ämter & Papiere“** an – dort getrennt in Ausweis (läuft ab, mit Erinnerung) und Urkunde (gilt für immer). Zeugnisse bleiben bei *Bildung*. Einen Umzug gibt es nicht; Ablago wird neu aufgesetzt.

## Voraussetzungen

- Ablago ab Version 0.293.2 (Rundgang und Tipps in mehreren Sprachen; für Verträge ab 0.243, für Rechnungen und Bestellungen ab 0.248)
- Pakete **Basis** ab 1.10.0, **Finanzen** ab 1.0.0, **Verträge** ab 1.1.0 und **Rechnungen und Bestellungen** ab 1.1.0 – werden bei der Installation aus dem Katalog mitinstalliert

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten und auf Wunsch Beispiel-Mappen an.

## Wer was sehen darf

Nicht alles gehört vor alle Augen: Konten (mit den Zugangsdaten zum Online-Banking) sollen meist nur die Eltern sehen – Gesundheitsunterlagen ebenso (Paket Gesundheit). Das Paket schreibt dafür nichts vor – du richtest es nach der Installation selbst ein. Berechtigungen pflegst du am **Mappentyp** (Werkbank → Mappentypen → *Gesundheit* bzw. *Konto* aus dem Paket Finanzen, Abschnitt **Berechtigungen**). Ein Beispiel:

1. Unter **Werkbank → Benutzer** eine Rolle **Eltern** anlegen und Lena und Tom geben.
2. Am Mappentyp **Konto** eine Regel anlegen: **Nur Eltern** – wenn *Benutzer hat nicht Rolle Eltern* → **✗ C R U D P**.
3. Dieselbe Regel mit **Regel in andere Mappentypen kopieren** auch an die Mappentypen des Pakets **Gesundheit** geben und **Mappentyp speichern**.
4. Im **Testlauf** darunter mit dem Benutzer von Jonas prüfen: Er darf keine Konto- oder Gesundheitsmappe lesen.

Wer nur die Passwörter schützen will, entzieht statt **R** nur **P** (Passwörter sehen). Mehr dazu im Administratorhandbuch unter „Berechtigungen“.

## Nach der Installation

1. Die eigenen Banken, Versicherer, Ärzte und Firmen als **Organisation** anlegen (oder aus der Post heraus).
2. Unter **Ablage → Ablageorte** die Orte anlegen, an denen Papier liegt.
3. Verträge und Versicherungen ablegen (Ausweise im Paket „Ämter & Papiere“); die Fristen erinnern von selbst (an „Kündigen bis“ das Paket Verträge).
4. Die Beispiel-Mappen löschen, sobald du sie nicht mehr brauchst.

Bestehende eigene Mappentypen ändert das Paket nicht. Ein Update ergänzt nur neue Felder, Register und Ansichten.

**Update auf 3.0.0 (Konto und Steuerjahr):** Ab 3.0.0 kommen Konto und Steuerjahr aus dem Paket **Finanzen**. Einen Umzug vorhandener Konten und Steuerjahre aus Haushalt 2.x gibt es nicht – Haushalt 3.0.0 ist für eine neu aufgebaute Ablage gedacht.
