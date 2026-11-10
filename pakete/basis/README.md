# Basis

Das Basis-Paket bringt die Mappentypen **Organisation**, **Niederlassung**, **Person** und **Ablageort**. Organisation ist für Firmen, Behörden, Ärzte und Praxen, Versicherungen, Banken, Vereine, Vermieter und alle anderen Stellen, mit denen ein Haushalt zu tun hat. Statt die Typen Feld für Feld in der Werkbank zu bauen, installierst du sie mit einem Klick unter **Werkbank → Pakete**.

## Inhalt

| Mappentyp | wofür | wichtige Felder |
| --- | --- | --- |
| Organisation | jede Stelle, mit der du zu tun hast | Name, Art, Kundennummer, Telefon, E-Mail, Anschrift |
| Niederlassung | Filiale, Zweigstelle, Praxis oder Außenstelle einer Organisation | Organisation, Name, Art, Nummer, Öffnungszeiten, Kontakt, Anschrift |
| Person | ein Mensch, mit dem du zu tun hast – **kein Benutzer von Ablago** | Anrede, Titel, Vor- und Nachname, Beziehung, Geburtstag, Organisation, Niederlassung, Funktion, Kontakt, Anschrift |
| Ablageort | wo das Papier liegt – Ordner, Kiste, Schrank, Schließfach oder „vernichtet“ (ab 1.6.0) | Name, Liegt in, Beschreibung |

### Organisation

| Register | Felder |
| --- | --- |
| Stammdaten | **Name** (Pflicht, eindeutig), Kürzel, **Art** (Mehrfachauswahl: Lieferant, Kunde, Bank, Versicherung, Behörde, Arbeitgeber, Arzt/Praxis, Handwerker, Vermieter, Verein, Versorger, Sonstige), **Eigene Organisation** (ab 1.7.0), **Kundennummer**, Beschreibung; Abschnitt **Datenschutz** nur bei einer eigenen Organisation: Verantwortlicher, Datenschutzbeauftragter |
| Kontakt | Telefon, Fax, E-Mail (wird auf die Form geprüft), Internetseite |
| Anschrift | Straße, Hausnummer, PLZ, Ort, Land (Vorgabe: Deutschland) |
| Niederlassungen | alle Niederlassungen dieser Organisation (ab 1.1.0) |
| Ansprechpartner | alle Personen, die hier arbeiten bzw. Ansprechpartner sind (ab 1.1.0) |

Dazu *Dokumente* und *Historie*. Die **Kundennummer** ist *deine* Nummer bei der Organisation – Kunden-, Mitglieds-, Versicherten- oder Patientennummer. Sie steht so auf Briefen und Rechnungen und hilft beim Zuordnen.

**Eigene Organisation** (ab 1.7.0): Kennzeichne deine eigene Firma oder dein Gewerbe so. Ablago nimmt Name, Anschrift und Kontakt von dort für Datenschutz-Auskünfte und den Briefkopf von Vorlagen und liest die eigene Organisation nie als Absender eingehender Post. Den Haken setzt nur, wer Ablago verwaltet; mehrere eigene Organisationen sind möglich. Im Abschnitt **Datenschutz** stehen dann Verantwortlicher und – falls es einen gibt – Datenschutzbeauftragter (keine Rechtsberatung). AGB und Preislisten legst du unter *Dokumente* mit ihrem Stand im Namen ab, z. B. „AGB Stand 2026-01“.

### Niederlassung

Eine Bank mit mehreren Filialen, eine Arztpraxis mit zwei Praxen, eine Behörde mit Außenstellen: Die Organisation gibt es **einmal**, ihre Niederlassungen hängen an ihr (Verweis *Organisation*, Pflicht). Der Titel zeigt beides, z. B. „Sparkasse Musterstadt – Filiale Marktplatz“. Art: Filiale, Zweigstelle, Geschäftsstelle, Praxis, Außenstelle, Werk/Lager, Büro, Sonstige. Register *Allgemein*, *Kontakt*, *Anschrift*, *Ansprechpartner*, *Verknüpfungen*, *Dokumente*, *Historie*. Andere Pakete (z. B. Haushalt) verweisen weiter auf die Organisation.

### Person

Eine **Person** ist ein Kontakt – Ansprechpartnerin bei der Bank, Hausarzt, Vermieter, Oma. Sie ist **kein Benutzer** von Ablago und kann sich nicht anmelden (Benutzer verwaltest du unter *Werkbank → Benutzer*). Register *Stammdaten* (mit **Beziehung**: Familie, Freund/in, Ansprechpartner, Arzt/Ärztin, Handwerker, Mieter/in, Vermieter/in, Nachbar/in, Sonstige), *Arbeit* (Organisation, Niederlassung, Funktion, Abteilung – bei *Niederlassung* erscheinen nur die Niederlassungen der gewählten Organisation, ab 1.6.1), *Kontakt*, *Anschrift*, *Verknüpfungen*, *Dokumente*, *Historie*. Wer an Geburtstage erinnert werden möchte, schaltet am Feld *Geburtstag* unter *Werkbank → Mappentypen* eine jährliche Erinnerung ein.

### Ablageort

Ein **Ablageort** hält fest, wo das Papier zu einem eingescannten Dokument liegt – oder dass es vernichtet ist. Ablageorte liegen ineinander: Der Titel zeigt den ganzen Pfad, z. B. „zu Hause › Arbeitszimmer Schrank › roter Ordner“. Zieht der Schrank um, änderst du nur *Liegt in* am Schrank; Ablago zieht die Titel darunter nach. Register *Allgemein* (Name, Liegt in, Beschreibung), *Enthält* (die Orte darin), *Liegt hier* (alle Mappen, die auf diesen Ort verweisen) und *Fotos*.

Andere Pakete (Haushalt, Haus, Vermietung, Fahrzeuge) verweisen im Feld *Verbleib Originaldokumente* auf ihn – mit `basis:ablageort`. Früher brachte Ablago den Ablageort selbst mit; gibt es ihn in deiner Ablage schon, **übernimmt** Basis ihn beim Installieren bzw. beim Update auf 1.6.0 mit allen Orten und Verweisen. Es entsteht kein zweiter.

**Sichten:** *Organisationen* mit *Versicherungen*, *Banken*, *Behörden*, *Ärzte und Praxen* und *Niederlassungen*; *Personen* mit *Familie und Freunde* und *Ansprechpartner*; *Ablageorte*.

**Gleichbedeutende Wörter für die Suche:** *Rechnung, Beleg* · *Quittung, Kassenbon, Kassenzettel* · *Vertrag, Vereinbarung* · *Kündigung, Beendigung* · *Police, Versicherungsschein, Versicherungspolice* · *Mahnung, Zahlungserinnerung* · *Gutschrift, Erstattung, Rückerstattung* · *Lastschrift, Abbuchung* · *Anschrift, Adresse*. Wer eines sucht, findet auch die anderen. Das sind nur allgemeine Wörter, die in jeder Ablage vorkommen; fachliche Wörter bringen die Fachpakete mit (z. B. Kfz/Auto in Fahrzeuge). Sie stehen in Ablago unter Werkbank → Suche; eigene Gruppen kannst du dort ergänzen.

**Beispiele (optional):** „Stadtwerke Musterstadt“, „Praxis Dr. Beispiel“, die „Sparkasse Musterstadt“ mit zwei Filialen, die Kundenberaterin Sabine Beraterin (Filiale Marktplatz), Hausarzt Dr. Bernd Beispiel und Oma Muster – erfundene Daten, untereinander verknüpft.

## Voraussetzungen

- Ablago ab Version 0.230 (vorläufig; eigene Organisation und Datenschutz, Etappe 15). 1.6 lief ab 0.212 (Ablageort aus Basis), 1.5 ab 0.127, 1.0.0 ab 0.63.
- keine weiteren Pakete

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Sichten, gleichbedeutende Wörter für die Suche und auf Wunsch Beispiele an – bzw. übernimmt einen vorhandenen Ablageort.

## Nach der Installation

1. Unter **Ablage → Organisationen** neue Organisationen anlegen; ihre Filialen legst du als **Niederlassung** an.
2. Unter **Ablage → Personen** die Menschen, mit denen du zu tun hast – mit Organisation und Niederlassung, wo sie arbeiten.
3. Unter **Ablage → Ablageorte** legst du die Orte für dein Papier an – oben „zu Hause“, darin der Schrank, darin der Ordner.
4. **Update von 1.0.0:** ergänzt nur – Niederlassung und Person kommen dazu, die Organisation bekommt die Register *Niederlassungen* und *Ansprechpartner*; vorhandene Organisationen bleiben, wie sie sind.
5. **Update auf 1.6.0:** Ein vorhandener Ablageort aus Ablago wird übernommen, nicht neu angelegt.
6. Bei bestehenden Typen (z. B. „Vertragspartner“) ändert das Paket nichts. Wer umsteigen will, verweist in seinen Typen künftig auf „Organisation“.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Basis“ im Titel.
