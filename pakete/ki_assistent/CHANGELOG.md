# Änderungen

## 1.1.1

- Kein „Nachdenken“ vor der Antwort: Jede Anfrage an den KI-Dienst (Frag deine Ablage, Aus Dokument ausfüllen, Probefrage von „Verbindung testen“) schickt `"reasoning_effort": "none"` mit – Ollama schaltet damit das Nachdenken von Modellen wie `qwen3` ab, die sonst auf einem NAS lange keine sichtbare Antwort geben. Lehnt ein Dienst das Feld ab (HTTP 400), wiederholt das Paket die Anfrage einmal ohne (DMS #564).
- Beispielmodell jetzt `ministral-3:3b` (Apache-2.0) statt `qwen2.5:3b` (Qwen Research License, keine offene Lizenz) – in der Beschreibung, der Hilfe zum Feld *Modell* und den Einrichtungsschritten. Alternativen und Lizenzen in der Beschreibung unter „Welches Modell?“.
- Beschreibung verweist auf die Seite [KI lokal betreiben](https://motom001.github.io/dms/admin/aktuell/ki-lokal/) im Administratorhandbuch des DMS (Ollama per Docker Compose, auch auf einem NAS ohne Grafikkarte).
- Die Attrappe kennt das Modell `streng:1b`, das `reasoning_effort` ablehnt.

## 1.1.0

- Neu: **Aus Dokument ausfüllen** über den KI-Dienst (dms-registry #64, DMS #511). Das Paket beantragt dafür zusätzlich das Recht **„Felder aus Dokumenten vorschlagen“ (`dms:erkennen`)** – das DMS zeigt es beim Update und lässt es bestätigen. Es bekommt nur den Text des Dokuments und die Beschreibung der Felder als JSON Schema.
- Strukturierte Ausgabe: Anfrage mit `response_format` vom Typ `json_schema` (Ollama ab 0.5, llama.cpp-Server, LocalAI, vLLM); kennt der Dienst das nicht, ein zweiter Versuch mit „nur JSON“. Der Text geht abgegrenzt als Daten an den Dienst, getrennt von der Aufgabe.
- Das Paket prüft die Antwort, bevor es sie weitergibt: unbekannte Felder und Werte, die nicht zum Schema passen, fallen weg. Ist nichts Brauchbares dabei, antwortet der Dienst nicht oder nicht rechtzeitig, meldet das Paket einen Fehler – das DMS nimmt dann die eingebaute Erkennung.
- Neue Einstellungen im Abschnitt *Aus Dokument ausfüllen*: **Für „Aus Dokument ausfüllen“ nutzen** (Standard an) und **Zeitgrenze** (Standard 50 Sekunden).
- Braucht DMS ab 0.125.0. „Frag deine Ablage“ bleibt unverändert.

## 1.0.0

- Erste Fassung: beantwortet Fragen an die Ablage („Frag deine Ablage“, DMS 0.124.0) über einen Dienst mit OpenAI-kompatibler Schnittstelle (Chat Completions, Antwort Stück für Stück), Netz nur zur bestätigten Dienst-Adresse, „Verbindung testen“ mit Modellliste und Antwortzeit.
