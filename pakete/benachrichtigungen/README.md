# Benachrichtigungen

Das Paket **Benachrichtigungen** bringt vorgefertigte [Automatisierungen](https://help.ablago.app/admin/aktuell/automatisierungen/) mit, die Ablago bisher fest eingebaut hatte. Du kannst sie unter **Werkbank → Ablage aufbauen → Automatisierungen** ansehen, anpassen und ein- oder ausschalten.

## Inhalt

| Automatisierung | Wenn | Dann |
| --- | --- | --- |
| Tägliche Zusammenfassung | Zeitplan für jeden Benutzer, Uhrzeit aus dem Profil (sonst werktags 7:00) | E-Mail mit den offenen Aufgaben; abbestellt, abwesend oder nichts offen → nichts |
| Favoriten-Änderungen melden | Favorit geändert | gebündelte Benachrichtigung „Geändert“ an alle, die die Mappe als Favorit haben; in der Automatisierung lässt sich auf Rollen einschränken und die Vorgabe für neue Benutzer wählen |
| Post für dich | Post angelegt oder „An“ bzw. Stand geändert – solange jemand unter „An“ steht und die Post neu ist | Aufgabe „Post für dich – bitte zuordnen“ an die Person unter „An“ (bei Abwesenheit an die Vertretung). Sie erledigt sich, sobald die Post zugeordnet oder erledigt ist oder an jemand anderen geht; je Post und Person nur eine. |
| Vertretung eingetragen | Abwesenheit gesetzt | Aufgabe an den Vertreter: „Hallo …, … hat dich vom … bis … als Vertreter hinterlegt.“ Sie erledigt sich, wenn die Abwesenheit endet oder sich die Vertretung ändert. |
| Vertretung zurückgezogen | Vertretung zurückgezogen (Abwesenheit beendet, anderer oder kein Vertreter mehr) | Benachrichtigung an den bisherigen Vertreter |
| Sammelmeldung Anmeldeschutz | Zeitplan täglich 0:00 | Mail an die Administratoren über die Sperren seit der letzten Meldung (nur wenn es welche gab) |
| Kontosperre sofort melden | Benutzerkonto gesperrt | Mail an die Administratoren, je Konto höchstens einmal am Tag |

Im Einrichtungsassistenten ist das Paket vorausgewählt. Beim Installieren fragt Ablago, welche Automatisierungen gleich eingeschaltet werden sollen – vorausgewählt sind alle; die beiden Meldungen des Anmeldeschutzes wählst du ab, wenn du keine Mails über Angriffsversuche willst. Hat dein Ablago diese Abläufe beim Update schon als eigene Automatisierungen übernommen, ersetzen die mitgelieferten sie, solange du sie nicht geändert hast – an oder aus bleibt dabei erhalten.

**„Post für dich“** legte Ablago bis 0.256 selbst an. Ab 0.257 macht das nur noch diese Automatisierung: Ohne das Paket bekommt bei neuer Post niemand mehr die Aufgabe. Offene Aufgaben „Post für dich“ von vorher bleiben und erledigen sich wie bisher.

Dazu bringt das Paket **Automatisierungsvorlagen** fürs Menü **Mappe ▾** mit (unter **Werkbank → Ablage aufbauen → Automatisierungsvorlagen**):

| Vorlage | Wann | Fragt | Dann |
| --- | --- | --- | --- |
| Aufgabe vergeben | sofort | Empfänger, Text | Aufgabe an die gewählte Person – ersetzt die Vorlage von Ablago mit denselben Werten |
| Erinnern | am gewählten Datum | Datum, Empfänger, Text | Erinnerung an die gewählte Person – ersetzt die Vorlage von Ablago mit denselben Werten |
| Wiedervorlage | in 6 Monaten | – | Aufgabe „Wiedervorlage: {titel}“ an dich |

Entfernst du das Paket, gelten wieder „Aufgabe vergeben“ und „Erinnern“ von Ablago; geplante Erinnerungen laufen weiter.

## Voraussetzungen

- Ablago ab Version 0.257

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Automatisierungen an; sie laufen mit dem Systemkonto „Automatisierung“. Die Automatisierungsvorlagen legen nur Aufgaben an und laufen mit den Rechten der Person, die sie an einer Mappe anwendet.

---

# Notifications (English)

The **Notifications** package brings ready-made automations that Ablago used to have built in: the **daily summary** of open tasks (schedule per user, time from the profile), **favourite changes** (optionally only for some roles), **Post for you** (a task “Post for you – please assign” for the person under “To” on new post, to their stand-in when they are away; it completes itself once the post is assigned, done or goes to someone else – Ablago did this itself up to 0.256), **Substitute entered** and **Substitution withdrawn**, and the **login protection** mails (daily summary of blocks, immediate mail when an account is locked). It is preselected in the setup wizard; while installing, Ablago asks which automations to switch on (all preselected). It also brings the automation templates **Assign task**, **Remind** (both replacing Ablago’s with the same values) and **Follow-up** (a task for you in six months) for the **Folder** menu – tasks only. Requires Ablago 0.257 or later; without the package, nobody gets “Post for you” from 0.257 on. No code, no network access.
