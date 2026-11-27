# Vollmachten

Das Paket **Vollmachten** hält alle Vollmachten eines Haushalts an einem Ort fest: wer wen bevollmächtigt hat, gegenüber wem, wie lange und wo das Original liegt. Das reicht von der Vorsorgevollmacht über die Kontovollmacht bis zur Postvollmacht.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Vollmacht | jede Vollmacht im Haushalt | Art, Vollmachtgeber, Bevollmächtigt (mehrere), Gegenüber (Organisation), Umfang, ausgestellt am, gültig bis, über den Tod hinaus, Form, im Vorsorgeregister, widerrufen am, Verbleib Original | **Gültig bis** (30 Tage vorher) |

**Arten:** Vorsorgevollmacht, Generalvollmacht, Kontovollmacht, Vollmacht gegenüber Kranken- oder Pflegekasse, Schweigepflichtentbindung, Vollmacht für Steuerberatung, Vollmacht gegenüber einer Behörde (z. B. Zulassungsstelle, Bürgeramt), Stimmrechtsvollmacht (Eigentümerversammlung), Vollmacht für Kita oder Schule (Abholen), Einverständnis für eine Reise mit Kind, Anwaltsvollmacht, Postvollmacht und Sonstige.

**Ansichten:** *Vollmachten* mit allen, darunter **Gültige Vollmachten** (ohne „Widerrufen am“).

**Automatisierung** (nach der Installation aus): Vollmacht läuft ab.

**Beispiele (optional):** für die erfundene Familie Muster (Personen aus Basis) Toms Vorsorgevollmacht für Lena und Lenas Kontovollmacht bei der Sparkasse Musterstadt für Tom.

**Woanders:** Patientenverfügung, Betreuungsverfügung und Testament stehen im Paket **Verfügungen**. Dort kann eine Verfügung auf die passende Vollmacht zeigen.

## Wer was sehen darf

Vollmachten verraten viel über Familie, Gesundheit und Geld. **Nach der Installation sieht jede Person mit eigenem Zugang alle Vollmachten.** Wenn das nicht passt, leg unter **Werkbank → Benutzer** eine Rolle an (z. B. „Eltern“) und am Mappentyp **Vollmacht** eine Regel, die anderen das Lesen verbietet. Mehr im Administratorhandbuch unter „Berechtigungen“.

## Voraussetzungen

- Ablago ab Version 0.323
- Paket **Basis** ab 1.12.0 – kommt bei der Installation aus dem Katalog mit.

## Rechte und Netz

Dieses Paket enthält keinen Code und geht nicht ins Netz. Es legt nur einen Mappentyp, Ansichten, eine Automatisierung und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. Bevollmächtigte als **Person** anlegen, Banken, Kassen und Ämter als **Organisation**.
2. Für jede Vollmacht eine Mappe anlegen und den Scan anhängen.
3. Bei Vorsorgevollmachten eintragen, wo das Original liegt – im Ernstfall wird es gebraucht.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit dem Paketnamen im Titel.
