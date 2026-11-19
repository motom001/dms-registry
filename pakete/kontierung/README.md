# Kontierung

Das Paket **Kontierung** bringt die Kontierungsobjekte eines Betriebs nach Ablago: **Kostenstellen**, **Kostenträger**, **Sachkonten**, **Steuerschlüssel** und **Organisationseinheiten**. Eine Rechnung lässt sich damit gleich einer Kostenstelle, einem Kostenträger und einem Sachkonto zuordnen. So findest du sie wieder, gibst sie frei und übergibst sie an die Buchhaltung. **Ablago bucht nicht** – Kontostände, Buchungen und Abschlüsse bleiben in der Buchhaltung.

Das Paket ist für die **berufliche Nutzung** gedacht: Ablago empfiehlt es nur, wenn die Ablage als „beruflich genutzt“ eingerichtet ist. Installieren kannst du es trotzdem immer.

## Inhalt

| Mappentyp | wofür | wichtige Felder |
| --- | --- | --- |
| Organisationseinheit | Abteilung oder Bereich, verschachtelt | Name, Kürzel, Gehört zu (übergeordnete Einheit), Leitung (Person) |
| Kostenstelle | wo Kosten entstehen, z. B. 4100 Fuhrpark | Nummer, Name, Verantwortliche Person, Übergeordnete Kostenstelle, Organisationseinheit |
| Kostenträger | wofür Kosten entstehen | Nummer, Name, Art (Produkt, Projekt, Auftrag, Sonstiges), Verantwortliche Person |
| Sachkonto | Konto aus dem Kontenrahmen, nur zur Auswahl | Nummer, Bezeichnung, Kontenrahmen (SKR03, SKR04, Eigener) |
| Steuerschlüssel | Umsatzsteuersatz für Rechnung und Positionen | Bezeichnung, Satz, Gültig ab, Gültig bis, Kennzeichen für die Buchhaltung |

**Hierarchien:** Organisationseinheit und Kostenstelle zeigen über *Gehört zu* bzw. *Übergeordnete Kostenstelle* auf ihre übergeordnete Mappe. Darunter stehen die Register *Untereinheiten* bzw. *Untergeordnete Kostenstellen*; an der Organisationseinheit dazu ihre *Kostenstellen*.

**Steuerschlüssel als Vorgaben:** Umsatzsteuer 19 % (gültig ab 1.1.2007), 7 % (ab 1.7.1983) und ohne Umsatzsteuer (0 %). Sie bleiben nach der Installation; ein Update überschreibt nichts, was du geändert hast. Das Kennzeichen eurer Buchhaltung trägst du selbst ein. Ändert sich ein Satz, trägst du beim alten *Gültig bis* ein und legst einen neuen an. Ohne Gewähr, keine Steuerberatung.

**Ansichten:** *Kontierung* mit allem, darunter je eine Ansicht für Kostenstellen, Kostenträger, Sachkonten, Steuerschlüssel und Organisationseinheiten.

## An der Rechnung

Das Paket [Rechnungen](../rechnungen/) (ab 1.3.0) zeigt bei „beruflich genutzt“ den Abschnitt **Kontierung** mit *Kostenstelle*, *Kostenträger*, *Sachkonto* und *Steuerschlüssel*. An jeder Position gibt es außerdem einen *Steuerschlüssel*. Wählst du einen Steuerschlüssel, übernimmt Ablago seinen Satz in den leeren *Umsatzsteuersatz*. Privat bleibt der Satz frei eintragbar. Unter *Verknüpfungen* einer Kostenstelle stehen alle Rechnungen, die auf sie zeigen.

## Voraussetzungen

- Ablago ab 0.236.0 (Vorgaben)
- Paket **Basis** ab 1.7.0 (Personen für Leitung und Verantwortliche) – kommt bei der Installation aus dem Katalog mit

## Rechte und Netzwerkzugriff

Dieses Paket enthält keinen Code. Es legt nur Mappentypen, Ansichten und die drei Steuerschlüssel an.

## Nach der Installation

1. Lege deine Kostenstellen an; übergeordnete Kostenstellen zuerst, dann die darunter.
2. Bei Bedarf Kostenträger, Sachkonten und Organisationseinheiten.
3. Ergänze an den Steuerschlüsseln das Kennzeichen eurer Buchhaltung, falls ihr eines nutzt.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit „Kontierung“ im Titel.
