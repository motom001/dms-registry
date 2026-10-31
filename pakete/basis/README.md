# Basis

Das Basis-Paket bringt die Mappentypen **Organisation**, **Niederlassung** und **Person**. Organisation ist für Firmen, Behörden, Ärzte und Praxen, Versicherungen, Banken, Vereine, Vermieter und alle anderen Stellen, mit denen ein Haushalt zu tun hat. Statt die Typen Feld für Feld in der Werkbank zu bauen, installierst du sie mit einem Klick unter **Werkbank → Pakete**.

## Inhalt

| Mappentyp | wofür | wichtige Felder |
| --- | --- | --- |
| Organisation | jede Stelle, mit der du zu tun hast | Name, Art, Kundennummer, Telefon, E-Mail, Anschrift |
| Niederlassung | Filiale, Zweigstelle, Praxis oder Außenstelle einer Organisation | Organisation, Name, Art, Nummer, Öffnungszeiten, Kontakt, Anschrift |
| Person | ein Mensch, mit dem du zu tun hast – **kein Benutzer des DMS** | Anrede, Titel, Vor- und Nachname, Beziehung, Geburtstag, Organisation, Niederlassung, Funktion, Kontakt, Anschrift |

### Organisation

| Register | Felder |
| --- | --- |
| Stammdaten | **Name** (Pflicht, eindeutig), Kürzel, **Art** (Mehrfachauswahl: Lieferant, Kunde, Bank, Versicherung, Behörde, Arbeitgeber, Arzt/Praxis, Handwerker, Vermieter, Verein, Versorger, Sonstige), **Kundennummer**, Beschreibung |
| Kontakt | Telefon, Fax, E-Mail (wird auf die Form geprüft), Internetseite |
| Anschrift | Straße, Hausnummer, PLZ, Ort, Land (Vorgabe: Deutschland) |
| Niederlassungen | alle Niederlassungen dieser Organisation (ab 1.1.0) |
| Ansprechpartner | alle Personen, die hier arbeiten bzw. Ansprechpartner sind (ab 1.1.0) |

Dazu *Dokumente* und *Historie*. Die **Kundennummer** ist *deine* Nummer bei der Organisation – Kunden-, Mitglieds-, Versicherten- oder Patientennummer. Sie steht so auf Briefen und Rechnungen und hilft beim Zuordnen.

### Niederlassung

Eine Bank mit mehreren Filialen, eine Arztpraxis mit zwei Praxen, eine Behörde mit Außenstellen: Die Organisation gibt es **einmal**, ihre Niederlassungen hängen an ihr (Verweis *Organisation*, Pflicht). Der Titel zeigt beides, z. B. „Sparkasse Musterstadt – Filiale Marktplatz“. Art: Filiale, Zweigstelle, Geschäftsstelle, Praxis, Außenstelle, Werk/Lager, Büro, Sonstige. Register *Allgemein*, *Kontakt*, *Anschrift*, *Ansprechpartner*, *Verknüpfungen*, *Dokumente*, *Historie*. Andere Pakete (z. B. Haushalt) verweisen weiter auf die Organisation.

### Person

Eine **Person** ist ein Kontakt – Ansprechpartnerin bei der Bank, Hausarzt, Vermieter, Oma. Sie ist **kein Benutzer** des DMS und kann sich nicht anmelden (Benutzer verwaltest du unter *Werkbank → Benutzer*). Register *Stammdaten* (mit **Beziehung**: Familie, Freund/in, Ansprechpartner, Arzt/Ärztin, Handwerker, Mieter/in, Vermieter/in, Nachbar/in, Sonstige), *Arbeit* (Organisation, Niederlassung, Funktion, Abteilung), *Kontakt*, *Anschrift*, *Verknüpfungen*, *Dokumente*, *Historie*. Wer an Geburtstage erinnert werden möchte, schaltet am Feld *Geburtstag* unter *Werkbank → Mappentypen* eine jährliche Erinnerung ein.

**Sichten:** *Organisationen* mit *Versicherungen*, *Banken*, *Behörden*, *Ärzte und Praxen* und *Niederlassungen*; *Personen* mit *Familie und Freunde* und *Ansprechpartner*.

**Beispiele (optional):** „Stadtwerke Musterstadt“, „Praxis Dr. Beispiel“, die „Sparkasse Musterstadt“ mit zwei Filialen, die Kundenberaterin Sabine Beraterin (Filiale Marktplatz), Hausarzt Dr. Bernd Beispiel und Oma Muster – erfundene Daten, untereinander verknüpft.

## Voraussetzungen

- DMS ab Version 0.79 (Version 1.0.0 lief ab 0.63)
- keine weiteren Pakete

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Sichten und auf Wunsch Beispiele an.

## Nach der Installation

1. Unter **Ablage → Organisationen** neue Organisationen anlegen; ihre Filialen legst du als **Niederlassung** an.
2. Unter **Ablage → Personen** die Menschen, mit denen du zu tun hast – mit Organisation und Niederlassung, wo sie arbeiten.
3. **Update von 1.0.0:** ergänzt nur – Niederlassung und Person kommen dazu, die Organisation bekommt die Register *Niederlassungen* und *Ansprechpartner*; vorhandene Organisationen bleiben, wie sie sind.
4. Bei bestehenden Typen (z. B. „Vertragspartner“) ändert das Paket nichts. Wer umsteigen will, verweist in seinen Typen künftig auf „Organisation“.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Basis“ im Titel.
