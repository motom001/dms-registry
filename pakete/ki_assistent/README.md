# KI-Assistent

Das Paket **KI-Assistent** beantwortet Fragen an deine Ablage: Auf der Startseite des DMS erscheint das Feld **„Frag deine Ablage“**. Du fragst in eigenen Worten – „Wann läuft die Kfz-Versicherung aus?“ – und bekommst eine Antwort mit Links zu den passenden Mappen.

Das Paket **rechnet nicht selbst**. Es ist ein Adapter zu einem **KI-Dienst, den du betreibst oder bewusst wählst** – zum Beispiel [Ollama](https://ollama.com) auf deinem Heimserver. Es spricht die verbreitete **OpenAI-kompatible Schnittstelle** (Chat Completions); damit gehen auch LocalAI, der Server von llama.cpp und – wenn du das willst – Anbieter im Internet.

## Was geht wann wohin

1. Du stellst im DMS eine Frage. Der Browser schickt sie mit dem bisherigen Chat an **dein DMS**.
2. **Das DMS selbst** sucht passende Stellen – im Volltext deiner Dokumente, in Titeln und Feldern der Mappen und, mit dem Paket [KI lokal – Ähnlichkeit](../ki_aehnlich/), nach Ähnlichkeit. Es sucht **nur in Mappen, die du lesen darfst**; Passwortfelder und Benutzer sind nie dabei.
3. Es schneidet **wenige Ausschnitte** heraus – höchstens so viele, wie der Administrator unter *Werkbank → Pakete → KI-Assistent → Frag deine Ablage* einstellt (Standard: 8 Ausschnitte, zusammen 6 000 Zeichen). **Nie der ganze Bestand.**
4. Das DMS gibt Frage, bisherigen Chat und Ausschnitte an dieses Paket im **Paket-Läufer**. Das Paket schickt sie an den KI-Dienst unter der **Dienst-Adresse** – an keine andere Adresse; das erzwingt der Läufer.
5. Der Dienst antwortet Stück für Stück; das Paket gibt die Stücke weiter, und die Antwort entsteht beim Schreiben.
6. Das DMS zeigt die Antwort **nur als Text** und darunter die **Quellen**. Unter jeder Antwort steht aufklappbar **„An die KI geschickt: n Ausschnitte aus m Mappen“** mit genau den Stellen, die beim Dienst angekommen sind.

Das Paket liest **nichts selbst** aus deiner Ablage, speichert nichts und schreibt nichts vom Inhalt ins Protokoll. Das DMS speichert weder Fragen noch Antworten; der Chat bleibt im Browser, bis du die Seite neu lädst.

> **Betrieb und Hosting des KI-Dienstes liegen außerhalb des DMS.** Läuft der Dienst bei dir im eigenen Netz, verlassen die Ausschnitte das Haus nicht. Bindest du einen Dienst bei einem **anderen Anbieter** an, ist das eine **Vertrauensbeziehung zu diesem Dienstleister** – wie beim Hosten des DMS selbst: Wo stehen die Rechner (Standort)? Gibt es einen Vertrag zur Auftragsverarbeitung? Speichert der Anbieter die Anfragen, und nutzt er sie zum Training? Das entscheidest du bewusst, indem du das Paket installierst, die Adresse einträgst und den Hinweis bestätigst. Voreingestellt ist nie eine Adresse im Internet.

## Rechte und Netzwerkzugriff

Bei der Installation zeigt das DMS diese Rechte und lässt sie dich bestätigen:

- **Fragen an die Ablage beantworten („Frag deine Ablage“) – nur aus Ausschnitten, die das DMS mitgibt (dms:antworten).** Keine Rechte an Mappen und keine an Dokumenten: Das Paket bekommt nur, was das DMS je Frage heraussucht.
- **Zugriff auf Netzwerk/Internet nur zu: der Adresse aus der Einstellung „Dienst-Adresse“ (trägst du ein und bestätigst sie).** Das Paket bringt keine feste Adresse mit.
- Es reagiert auf **keine Ereignisse** – es läuft nur, wenn jemand fragt oder du „Verbindung testen“ drückst.

## Einrichten

### 1. Einen KI-Dienst bereitstellen

**Ollama aus dem App-Store deines Heimservers** – am einfachsten:

- **Umbrel:** App Store → *Ollama* installieren. Adresse für das DMS meist `http://<umbrel>:11434/v1`.
- **CasaOS / ZimaOS:** App Store → *Ollama* installieren. Adresse `http://<rechner>:11434/v1`.

Danach ein Modell holen, z. B. im Terminal des Ollama-Containers: `ollama pull qwen2.5:3b`.

**Docker Compose neben dem DMS** – dann erreicht das DMS Ollama im selben Netz unter `http://ollama:11434/v1`:

```yaml
services:
  ollama:
    image: ollama/ollama
    volumes:
      - ./ollama:/root/.ollama
    restart: unless-stopped
    # Mit NVIDIA-Grafikkarte zusätzlich:
    # deploy: { resources: { reservations: { devices: [{ driver: nvidia, count: all, capabilities: [gpu] }] } } }
```

Ins Compose-Projekt des DMS eintragen (oder beide Projekte in ein gemeinsames Netzwerk hängen), dann `docker compose exec ollama ollama pull qwen2.5:3b`. Einen Port nach außen braucht Ollama dafür nicht.

**Ein anderer Rechner mit Grafikkarte** im Heimnetz ist oft deutlich schneller als ein NAS: Ollama dort installieren, mit `OLLAMA_HOST=0.0.0.0` starten und im DMS `http://<ip-des-rechners>:11434/v1` eintragen. Die Verbindung im Heimnetz ist dann unverschlüsselt (`http://`) – das ist bei einem eigenen Netz üblich; über das Internet nimm immer `https://`.

### 2. Paket installieren und einstellen

1. *Werkbank → Pakete → KI-Assistent → Installieren* und die Rechte bestätigen.
2. Reiter **Einstellungen**:
   - **Dienst-Adresse**, z. B. `http://ollama:11434/v1` – im leeren Feld steht das nur als Beispiel.
   - **Modell**, z. B. `qwen2.5:3b`.
   - **Schlüssel (API-Key)** nur, wenn der Dienst eine Anmeldung verlangt (Ollama nicht). Das DMS speichert ihn verschlüsselt.
   - **Antwort höchstens (Tokens)**, Standard 800 – kleiner ist schneller.
3. **Speichern** – das DMS fragt „Daten an diese Adresse schicken?“. Mit **Adresse bestätigen und speichern** gilt die Adresse; erst dann darf das Paket dorthin.
4. **Verbindung testen**: Das Paket fragt den Dienst nach seinen Modellen und stellt eine kurze Probefrage. Die Meldung sagt, ob der Dienst erreichbar ist, ob das Modell da ist (sonst: welche es gibt) und wie lange eine Antwort dauerte.

Unter *Werkbank → Pakete → KI-Assistent* stellst du außerdem die **Höchstmenge je Frage** ein.

## Welches Modell?

Kleine Modelle mit 1–4 Milliarden Parametern (quantisiert, z. B. Q4) laufen auch ohne Grafikkarte; gute Kandidaten für deutsche Fragen sind `qwen2.5:3b`, `llama3.2:3b` und `gemma2:2b`. Größere Modelle (7–8 Milliarden) antworten besser, brauchen aber eine Grafikkarte oder viel Geduld.

## Messung

Gemessen im **Paket-Läufer des DMS** (DMS 0.124.0, Standardgrenzen) auf **amd64 mit 2 Kernen**, mit der Attrappe eines Dienstes (`tests/attrappe.mjs`), die ihre Antwort in Stücken alle 20 ms schickt:

| | |
| --- | --- |
| Eigenanteil des Pakets je Frage (Worker starten, Nachrichten bauen, erstes Stück weitergeben) | ≈ 100–120 ms |
| Ganze Frage mit Suche der Ausschnitte, 9 Stücke | 310–360 ms |
| Verbindung testen (Modellliste) | 4–50 ms |

Die Zeit bestimmt also fast nur der KI-Dienst. **Messungen mit echten Modellen auf typischer Hardware (Intel N100, Raspberry Pi 5, NAS, Rechner mit Grafikkarte) stehen noch aus** und kommen hier dazu – mit Zeit bis zum ersten Wort und Wörtern je Sekunde. Die Zeitgrenze des Läufers (2 Minuten je Aufruf) gilt auch für eine Antwort; auf einem langsamen NAS hilft eine kleinere **Antwort höchstens (Tokens)**.

## Voraussetzungen

- DMS **0.124.0** oder neuer (Schnittstelle `dms:antworten`, Dienst-Adresse als Einstellung, Antwort Stück für Stück).
- Ein KI-Dienst mit OpenAI-kompatibler Schnittstelle (`/v1/models`, `/v1/chat/completions`).
- Dokumente mit Volltext – ohne Text findet das DMS keine Ausschnitte. Mit [KI lokal – Ähnlichkeit](../ki_aehnlich/) findet es auch Stellen ohne gleiche Wörter.

## Für Entwickler

| Datei | Inhalt |
| --- | --- |
| [`code/assistent.cpp`](code/assistent.cpp) | das Modul (DMS-Paket-ABI 1): Aktionen `dms:antworten` (Chat Completions mit `"stream": true` über `netz_strom`/`netz_weiter`, Stücke mit `teil`) und `verbindung_testen` |
| [`code/json.h`](code/json.h) | kleiner JSON-Leser (wie bei KI lokal – Ähnlichkeit) |
| [`code/bauen.sh`](code/bauen.sh) | Bau mit wasi-sdk – ohne fremde Bibliotheken und ohne Daten |
| [`tests/modul_test.mjs`](tests/modul_test.mjs) | Ablauf mit einer Nachbildung des DMS und eines Dienstes: Stücke, Nachrichten, Fehler, Verbindung testen |
| [`tests/attrappe.mjs`](tests/attrappe.mjs) | Attrappe eines OpenAI-kompatiblen Dienstes zum Ausprobieren ohne Modell |

```sh
pakete/ki_assistent/tests/pruefen.sh          # bauen und prüfen, ohne Netz
node pakete/ki_assistent/tests/attrappe.mjs   # Attrappe auf Port 11434 – im DMS als Dienst-Adresse eintragen
```

Das Paket gibt dem Dienst den Hinweis des DMS unverändert als Systemnachricht, die Ausschnitte als eigene, als Daten gekennzeichnete Nachricht und die Frage getrennt davon. Die Schnittstelle beschreibt das Entwicklerhandbuch des DMS unter [Pakete mit Code → Fragen beantworten](https://motom001.github.io/dms/entwickler/aktuell/pakete-code/#fragen-beantworten).

**Adapter für weitere Anbieter sind ausdrücklich willkommen** – als eigenes Paket mit dem Recht `dms:antworten` und einer Dienst-Adresse als Einstellung (siehe [REGELN](../../REGELN.md)). Felder aus Dokumenten vorschlagen („Aus Dokument ausfüllen“, DMS #511) kann dieses Paket noch nicht; das kommt in einer späteren Version.

## Lizenz

Apache-2.0 (siehe `LICENSE`).
