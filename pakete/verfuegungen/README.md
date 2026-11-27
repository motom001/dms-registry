# Verfügungen

Das Paket **Verfügungen** hält fest, was jemand für den Fall verfügt hat, dass er nicht mehr selbst entscheiden kann oder stirbt: Patientenverfügung, Betreuungsverfügung, Testament und Erbvertrag. Dazu gehört immer, wo das Original liegt und wer davon weiß.

## Inhalt

| Mappentyp | wofür | wichtige Felder | Frist |
| --- | --- | --- | --- |
| Verfügung | eine Verfügung einer oder zweier Personen | Art, Für (Person, mehrere), erstellt am, Form, hinterlegt, im Register, zuletzt bestätigt am, aufgehoben oder ersetzt am, Verbleib Original, kennt den Ort, zugehörige Vollmacht | **Erneut prüfen am** (14 Tage vorher) |

**Arten:** Patientenverfügung, Betreuungsverfügung, Sorgerechtsverfügung (wer sich um die Kinder kümmern soll), Bestattungsverfügung, Testament, gemeinschaftliches Testament und Erbvertrag.

**Erbvertrag:** Er ist zwar ein Vertrag, rechtlich aber eine Verfügung von Todes wegen (§ 1941 BGB). Deshalb steht er hier und nicht im Paket Verträge.

**Register:** Ins Zentrale Testamentsregister kommen nur Testamente und Erbverträge in amtlicher Verwahrung (Amtsgericht oder Notar). Ins Zentrale Vorsorgeregister kommen Vorsorgevollmacht und Betreuungsverfügung, eine Patientenverfügung nur zusammen mit einer der beiden.

**Bestätigen:** *Zuletzt bestätigt am* und *Erneut prüfen am* erscheinen nur bei Patienten-, Betreuungs- und Sorgerechtsverfügung. Eine Patientenverfügung solltest du etwa alle zwei Jahre mit Datum und Unterschrift bestätigen.

**Ansichten:** *Verfügungen* mit allen, darunter **Gesundheit und Betreuung** und **Für den Todesfall**.

**Automatisierung** (nach der Installation aus): Verfügung erneut prüfen.

**Beispiele (optional):** für die erfundene Familie Muster (Personen aus Basis) Toms Patientenverfügung, deren Ort Lena kennt, und das gemeinschaftliche Testament von Lena und Tom, hinterlegt beim Amtsgericht.

**Woanders:** Vollmachten, auch die Vorsorgevollmacht, stehen im Paket **Vollmachten**. Ist es installiert, zeigt *Zugehörige Vollmacht* darauf. Der Organspendeausweis ist ein **Gesundheitspass** im Paket Gesundheit. Was nach dem Tod kommt – Testamentseröffnung, Erbschein, Ausschlagung, Nachlassverzeichnis – deckt dieses Paket bewusst nicht ab.

## Wer was sehen darf

Verfügungen gehören zu den persönlichsten Unterlagen – ein Testament soll oft niemand sonst lesen. **Nach der Installation sieht jede Person mit eigenem Zugang alle Verfügungen** – das Paket bringt keine Regeln mit. Richte deshalb gleich Berechtigungen ein:

1. Unter **Werkbank → Benutzer** eine Rolle anlegen, z. B. **Eltern**.
2. Am Mappentyp **Verfügung** eine Regel anlegen: wenn *Benutzer hat nicht Rolle Eltern* → **✗ C R U D P**.
3. Feiner geht es mit einer Regel je Person, z. B. „Mappen, bei denen *Für* Markus ist, sieht nur Markus“.
4. Im **Testlauf** mit einem anderen Benutzer prüfen.

Mehr im Administratorhandbuch unter „Berechtigungen“.

**Keine Rechtsberatung:** Das Paket hilft beim Ablegen und Wiederfinden. Ob ein Testament oder eine Patientenverfügung wirksam ist, kann es nicht beurteilen. Dafür sind Notariat, Anwältin, Ärztin oder Betreuungsbehörde da.

**KI-Dienste:** Mappentypen aus Paketen sind für KI-Dienste gesperrt, bis die Verwaltung sie ausdrücklich zulässt. Wir empfehlen, die Verfügung **nicht** für KI-Dienste zuzulassen.

## Voraussetzungen

- Ablago ab Version 0.323
- Paket **Basis** ab 1.12.0 – kommt bei der Installation aus dem Katalog mit. Mit dem Paket **Vollmachten** kann eine Verfügung auf die zugehörige Vollmacht zeigen.

## Rechte und Netz

Dieses Paket enthält keinen Code und geht nicht ins Netz. Es legt nur einen Mappentyp, Ansichten, eine Automatisierung und auf Wunsch Beispiel-Mappen an.

## Nach der Installation

1. Den Ort des Originals als **Ablageort** anlegen, etwa „Ordner Familie, Wohnzimmerschrank“.
2. Für jede Verfügung eine Mappe anlegen, den Scan anhängen und eintragen, wer den Ort kennt.
3. Unter Werkbank → Automatisierungen „Verfügung erneut prüfen“ einschalten.

## Pflege

Fehler und Wünsche bitte als [Issue in dms-registry](https://github.com/motom001/dms-registry/issues) mit dem Paketnamen im Titel.
