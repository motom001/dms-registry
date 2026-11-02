// Paket Office und E-Mail (dms-registry #30, Stufe 1): Volltext für Word, Excel, PowerPoint, OpenDocument, RTF,
// Textdateien und E-Mails (.eml, .msg), die das DMS nicht selbst liest.
//
// Ablauf: Ereignis „Dokument hochgeladen“ (dokument.hochgeladen) → passt Dateityp oder Endung, die Datei über die API
// holen → Typ am Inhalt erkennen → Text herauslösen (nur XML bzw. Text lesen; Makros und eingebettete Objekte werden
// nie ausgeführt) → PUT /dokumente/{id}/volltext. Kein Netz, kein Dateisystem; das Original bleibt unverändert.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "erkennen.h"
#include "json.h"

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
extern "C" {
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(void *ziel, int32_t max);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);
}

namespace {

enum Stufe { DEBUG = 0, INFO = 1, WARNUNG = 2, FEHLER = 3 };

// Größere Dateien holt das Paket nicht (Speicher je Aufruf 256 MB; entpackte Teile kommen dazu).
constexpr double DATEI_MAX = 50.0 * 1024 * 1024;
// Die API nimmt höchstens 2 MB JSON je Anfrage: so viel Text (UTF-8) schreibt das Paket höchstens.
constexpr size_t TEXT_MAX = 1800u * 1000u;
constexpr size_t KOERPER_MAX = 2u * 1024u * 1024u - 4096u;

// Dateitypen (wie das DMS sie meldet) und Endungen, bei denen das Paket die Datei holt. Ob es wirklich eine solche
// Datei ist, entscheidet danach der Inhalt.
const char *TYPEN[] = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    "application/vnd.ms-word.document.macroenabled.12",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    "application/vnd.ms-excel.sheet.macroenabled.12",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
    "application/vnd.ms-powerpoint.presentation.macroenabled.12",
    "application/vnd.oasis.opendocument.text", "application/vnd.oasis.opendocument.spreadsheet",
    "application/vnd.oasis.opendocument.presentation",
    "message/rfc822", "application/vnd.ms-outlook", "application/rtf", "text/rtf", "text/plain",
};
const char *ENDUNGEN[] = {".docx", ".docm", ".dotx", ".xlsx", ".xlsm", ".xltx", ".pptx", ".pptm", ".ppsx", ".odt", ".ods", ".odp",
                          ".eml", ".msg", ".rtf", ".txt"};

void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }

std::vector<uint8_t> antwort() {
  std::vector<uint8_t> a((size_t)dms_antwort_laenge());
  if (!a.empty()) dms_antwort_lesen(a.data(), (int32_t)a.size());
  return a;
}
std::string antwortText() {
  std::vector<uint8_t> a = antwort();
  Json j = JsonLeser::lies((const char *)a.data(), a.size());
  std::string f = j["fehler"].text();
  return f.empty() ? std::string(a.begin(), a.end()) : f;
}

// Ids aus dem Ereignis kommen in einen Pfad: nur Buchstaben, Ziffern und Bindestrich.
bool sichereId(const std::string &s) {
  if (s.empty() || s.size() > 64) return false;
  for (char c : s) if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-')) return false;
  return true;
}

bool zustaendig(const std::string &mime, const std::string &name) {
  const std::string m = zeichen::klein(mime.substr(0, mime.find(';')));
  for (auto t : TYPEN) if (m == t) return true;
  const std::string n = zeichen::klein(name);
  for (auto e : ENDUNGEN) if (office::endetMit(n, e)) return true;
  return false;
}

std::string zahl(size_t n) {  // 12345 → „12.345“
  std::string s = std::to_string(n), r;
  for (size_t i = 0; i < s.size(); i++) { if (i && (s.size() - i) % 3 == 0) r += '.'; r += s[i]; }
  return r;
}

size_t zeichenzahl(const std::string &t) {
  size_t n = 0;
  for (unsigned char c : t) if ((c & 0xc0) != 0x80) n++;
  return n;
}

int verarbeite(const Json &e) {
  if (e["art"].text() != "dokument.hochgeladen") return 0;  // z. B. paket.einstellungen_geaendert
  const Json &d = e["daten"];
  const std::string dok = d["dokument"].text();
  if (!sichereId(dok)) { ergebnis("Ereignis ohne gültiges Dokument"); return 0; }
  if (!zustaendig(d["mime"].text(), d["name"].text())) return 0;  // PDF, Fotos … liest das DMS selbst
  if (d["groesse"].zahl(0) > DATEI_MAX) { ergebnis("Größer als 50 MB – kein Volltext"); return 0; }

  std::string q = "{\"methode\":\"GET\",\"pfad\":\"/dokumente/" + dok + "/inhalt\"}";
  int s = dms_api(q.data(), (int32_t)q.size());
  if (s == 404) { ergebnis("Das Dokument gibt es nicht mehr – nichts zu tun"); return 0; }
  if (s != 200) { log(FEHLER, "Datei holen: HTTP " + std::to_string(s) + " " + antwortText().substr(0, 200)); return 1; }

  zeichen::Sammler sammler(TEXT_MAX);
  erkennen::Gelesen g;
  {
    std::vector<uint8_t> datei = antwort();
    const std::string mime = zeichen::klein(d["mime"].text()), name = zeichen::klein(d["name"].text());
    g = erkennen::lies(datei.data(), datei.size(), sammler, 0, mime == "message/rfc822" || office::endetMit(name, ".eml"));
  }
  if (g.kern || g.art.empty()) { ergebnis("Kein Office-Dokument, keine E-Mail und kein Text (am Inhalt erkannt) – nichts zu tun"); return 0; }
  if (!g.fehler.empty()) {
    // Eine kaputte oder verschlüsselte Datei wird beim nächsten Versuch nicht besser: kein Fehlercode.
    const std::string m = g.art + " lässt sich nicht lesen: " + g.fehler;
    log(WARNUNG, "Dokument " + dok + ": " + m);
    ergebnis(m);
    return 0;
  }
  std::string text = sammler.fertig();
  bool gekuerzt = sammler.voll;
  std::string koerper = "{\"text\":" + jsonText(text) + "}";
  while (koerper.size() > KOERPER_MAX && text.size() > 1000) {  // viele Sonderzeichen: kürzer, bis es passt
    size_t n = text.size() * 9 / 10;
    while (n > 0 && ((uint8_t)text[n] & 0xc0) == 0x80) n--;
    text.resize(n);
    gekuerzt = true;
    koerper = "{\"text\":" + jsonText(text) + "}";
  }

  q = "{\"methode\":\"PUT\",\"pfad\":\"/dokumente/" + dok + "/volltext\",\"body\":" + koerper + "}";
  std::string().swap(koerper);
  s = dms_api(q.data(), (int32_t)q.size());
  std::string().swap(q);

  std::string meldung = g.art + ", " + zahl(zeichenzahl(text)) + " Zeichen";
  if (g.teile > 1 && (g.art == "PowerPoint" || g.art == "OpenDocument-Präsentation")) meldung += ", " + std::to_string(g.teile) + " Folien";
  if (g.teile > 1 && (g.art == "Excel" || g.art == "OpenDocument-Tabelle")) meldung += ", " + std::to_string(g.teile) + " Tabellenblätter";
  if (g.anhaenge) meldung += ", " + std::to_string(g.anhaenge) + (g.anhaenge == 1 ? " Anhang" : " Anhänge");
  if (gekuerzt) meldung += " (gekürzt)";
  if (g.makros) meldung += " – enthält Makros, nicht ausgeführt";
  if (g.verschluesselt) meldung += " – verschlüsselte Teile nicht lesbar";
  if (s == 200) { log(INFO, "Dokument " + dok + ": " + meldung); ergebnis(meldung); return 0; }
  const std::string grund = antwortText().substr(0, 300);
  // Dokument weg, keine Rechte, zu lang: eine Wiederholung ändert nichts.
  if (s == 404 || s == 403 || s == 413 || s == 422) {
    log(WARNUNG, "Dokument " + dok + ": Volltext nicht angenommen (HTTP " + std::to_string(s) + ") " + grund);
    ergebnis("Volltext nicht angenommen: " + grund);
    return 0;
  }
  log(FEHLER, "Volltext schreiben: HTTP " + std::to_string(s) + " " + grund);
  return 2;
}

char *eingang = nullptr;

}  // namespace

extern "C" {

__attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = static_cast<char *>(malloc((size_t)n + 1));
  if (eingang) eingang[n] = 0;
  return eingang;
}

__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t n) {
  return verarbeite(JsonLeser::lies(json, (size_t)n));
}

}
