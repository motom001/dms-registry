# Benachrichtigungen

Das Paket **Benachrichtigungen** bringt vorgefertigte [Automatisierungen](https://help.ablago.app/admin/aktuell/automatisierungen/) mit, die Ablago bisher fest eingebaut hatte. Du kannst sie unter **Werkbank → Ablage aufbauen → Automatisierungen** ansehen, anpassen und ein- oder ausschalten.

## Inhalt

| Automatisierung | Wenn | Dann |
| --- | --- | --- |
| Tägliche Zusammenfassung | Zeitplan für jeden Benutzer, Uhrzeit aus dem Profil (sonst werktags 7:00) | E-Mail mit den offenen Aufgaben; abbestellt, abwesend oder nichts offen → nichts |
| Favoriten-Änderungen melden | Favorit geändert | gebündelte Benachrichtigung „Geändert“ an alle, die die Mappe als Favorit haben |
| Vertretung eingetragen | Abwesenheit gesetzt | Aufgabe an den Vertreter: „Hallo …, … hat dich vom … bis … als Vertreter hinterlegt.“ Sie erledigt sich, wenn die Abwesenheit endet oder sich die Vertretung ändert. |
| Vertretung zurückgezogen | Vertretung zurückgezogen (Abwesenheit beendet, anderer oder kein Vertreter mehr) | Benachrichtigung an den bisherigen Vertreter |
| Sammelmeldung Anmeldeschutz | Zeitplan täglich 0:00 | Mail an die Administratoren über die Sperren seit der letzten Meldung (nur wenn es welche gab) |
| Kontosperre sofort melden | Benutzerkonto gesperrt | Mail an die Administratoren, je Konto höchstens einmal am Tag |

Im Einrichtungsassistenten ist das Paket vorausgewählt. Beim Installieren fragt Ablago, welche Automatisierungen gleich eingeschaltet werden sollen – vorausgewählt sind alle; die beiden Meldungen des Anmeldeschutzes wählst du ab, wenn du keine Mails über Angriffsversuche willst. Hat dein Ablago diese Abläufe beim Update schon als eigene Automatisierungen übernommen, ersetzen die mitgelieferten sie, solange du sie nicht geändert hast – an oder aus bleibt dabei erhalten.

## Voraussetzungen

- Ablago ab Version 0.188

## Rechte und Netz

Dieses Paket enthält keinen Code. Es legt nur Automatisierungen an; sie laufen mit dem Systemkonto „Automatisierung“.

---

# Notifications (English)

The **Notifications** package brings ready-made automations that Ablago used to have built in: the **daily summary** of open tasks (schedule per user, time from the profile), **favourite changes**, **Substitute entered** and **Substitution withdrawn**, and the **login protection** mails (daily summary of blocks, immediate mail when an account is locked). It is preselected in the setup wizard; while installing, Ablago asks which automations to switch on (all preselected). Requires Ablago 0.188 or later. No code, no network access.
