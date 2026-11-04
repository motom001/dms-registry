/*
 * Sicherungsziel WebDAV (DMS-Paket-ABI 1, DMS #585): bringt jede Sicherung des DMS auf einen WebDAV-Speicher –
 * Nextcloud, viele NAS, viele Hoster – und prüft dort, dass sie heil angekommen ist.
 *
 * Ereignis sicherung.fertig { name, datei, groesse, sha256, beginn, format, schlank, verschluesselung }
 *   1. „läuft“ melden, Ordner anlegen (MKCOL, wo nötig)
 *   2. die verschlüsselte Sicherung in Stücken lesen (GET /sicherungen/{name}/datei) und in Teilen hochladen:
 *        Nextcloud           Chunking v2 (/remote.php/dav/uploads/…, Teile ab 5 MB, zum Schluss MOVE .file)
 *        WebDAV allgemein    PUT des ersten Teils, danach PUT mit Content-Range, zum Schluss MOVE <datei>.teil → <datei>
 *        Dateiablage         Nextcloud „Nur Hochladen“ (File drop): ein PUT am Stück – kann nicht lesen, nicht löschen
 *      Kleine Sicherungen (bis zur Teilgröße) gehen überall in einem PUT.
 *   3. die schlanken Metadaten als <name>.json daneben legen (Wiederherstellung ohne vollständige .json)
 *   4. prüfen: Größe (PROPFIND), dann zurücklesen – vollständig mit SHA-256 (bis zur eingestellten Größe oder wenn die
 *      letzte vollständige Prüfung älter als 30 Tage ist), sonst 8 Stichproben gegen die lokale Datei. Dateiablage:
 *      nur „hochgeladen“ – ehrlich, denn zurücklesen geht dort nicht.
 *   5. auf Wunsch (Vorgabe aus) ältere Sicherungen am Ziel löschen
 *   6. Stand melden: als „extern“ in der Antwort auf jeden Aufruf (DMS #636) – das Paket schreibt im DMS nichts
 *
 * Lange Arbeit verteilt das Paket auf mehrere Aufrufe: Nach etwa 50 s antwortet es mit {"weiter": {…}} (Stelle,
 * Stand der Prüfsumme); der Paket-Läufer ruft es gleich wieder auf. Bricht das Netz ab, setzt die Wiederholung an der
 * letzten gespeicherten Stelle an. Nie liegt die ganze Sicherung im Speicher (außer bei der Dateiablage, bis 128 MB).
 *
 * Das Paket sieht nur die verschlüsselte Datei – nie den Schlüssel, nie Inhalte. Netz nur zur bestätigten Adresse
 * (erzwingt der Paket-Läufer); Zugangsdaten kommen aus den verschlüsselten Einstellungen und stehen nirgends im Protokoll.
 */
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cctype>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>
#include "json.h"

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
DMS(api) int32_t dms_api(const char *json, int32_t len);
DMS(netz) int32_t dms_netz(const char *json, int32_t len, const char *body, int32_t blen);
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(speicher_lesen) int32_t dms_speicher_lesen(const char *schluessel, int32_t len);
DMS(speicher_schreiben) int32_t dms_speicher_schreiben(const char *schluessel, int32_t len, const char *wert, int32_t wlen);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);

static const uint64_t MB = 1024ull * 1024ull;
/** So viel liest das DMS höchstens auf einmal (GET /sicherungen/{name}/datei). */
static const uint64_t STUECK = 8 * MB;
/** Dateiablage: am Stück höchstens so groß (die Datei liegt dafür ganz im Speicher des Aufrufs). */
static const uint64_t AM_STUECK_MAX = 128 * MB;
/** Nach so viel Zeit je Aufruf eine Fortsetzung (der Läufer erlaubt Standard 120 s). */
static const double BUDGET_MS = 50000;
static const int STICHPROBEN = 8;
static const uint64_t STICHPROBE = 1 * MB;
static const int VOLL_TAGE = 30;

static void log(int stufe, const std::string &t) { dms_log(stufe, t.data(), (int32_t)t.size()); }
static void ergebnis(const std::string &t) { dms_ergebnis(t.data(), (int32_t)t.size()); }
static std::string antwort() {
  std::string t((size_t)dms_antwort_laenge(), '\0');
  if (!t.empty()) dms_antwort_lesen(&t[0], (int32_t)t.size());
  return t;
}
static double jetztMs() { timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec * 1000.0 + t.tv_nsec / 1e6; }
static std::string zahl(uint64_t n) { char b[32]; snprintf(b, sizeof b, "%llu", (unsigned long long)n); return b; }
static std::string kurz(const std::string &t, size_t n) { return t.size() <= n ? t : t.substr(0, n) + " …"; }
static std::string mbText(uint64_t b) { char x[32]; snprintf(x, sizeof x, "%.1f MB", b / (double)MB); std::string s = x; for (auto &c : s) if (c == '.') c = ','; return s; }

static std::string speicherLesen(const std::string &k) {
  int n = dms_speicher_lesen(k.data(), (int32_t)k.size());
  return n < 0 ? "" : antwort();
}
static void speicherSchreiben(const std::string &k, const std::string &w) { dms_speicher_schreiben(k.data(), (int32_t)k.size(), w.data(), (int32_t)w.size()); }

/* ---------- SHA-256 (Stand lässt sich zwischen Aufrufen speichern) ---------- */

struct Sha256 {
  uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  uint64_t laenge = 0;
  uint8_t puffer[64];
  size_t n = 0;
  static uint32_t r(uint32_t x, int k) { return (x >> k) | (x << (32 - k)); }
  void block(const uint8_t *p) {
    static const uint32_t K[64] = {
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
      0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
      0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
      0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};
    uint32_t w[64];
    for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[4 * i] << 24 | (uint32_t)p[4 * i + 1] << 16 | (uint32_t)p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++) w[i] = w[i - 16] + (r(w[i - 15], 7) ^ r(w[i - 15], 18) ^ (w[i - 15] >> 3)) + w[i - 7] + (r(w[i - 2], 17) ^ r(w[i - 2], 19) ^ (w[i - 2] >> 10));
    uint32_t a = h[0], b = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
    for (int i = 0; i < 64; i++) {
      uint32_t t1 = hh + (r(e, 6) ^ r(e, 11) ^ r(e, 25)) + ((e & f) ^ (~e & g)) + K[i] + w[i];
      uint32_t t2 = (r(a, 2) ^ r(a, 13) ^ r(a, 22)) + ((a & b) ^ (a & c) ^ (b & c));
      hh = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
    }
    h[0] += a; h[1] += b; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
  }
  void update(const uint8_t *p, size_t l) {
    laenge += l;
    while (l) {
      if (!n && l >= 64) { block(p); p += 64; l -= 64; continue; }
      size_t k = std::min(l, 64 - n);
      memcpy(puffer + n, p, k); n += k; p += k; l -= k;
      if (n == 64) { block(puffer); n = 0; }
    }
  }
  std::string hex() {
    Sha256 x = *this;
    uint64_t bits = x.laenge * 8;
    uint8_t eins = 0x80, null = 0;
    x.update(&eins, 1);
    while (x.n != 56) x.update(&null, 1);
    uint8_t l[8];
    for (int i = 0; i < 8; i++) l[i] = (uint8_t)(bits >> (56 - 8 * i));
    x.update(l, 8);
    std::string s; char b[9];
    for (int i = 0; i < 8; i++) { snprintf(b, sizeof b, "%08x", x.h[i]); s += b; }
    return s;
  }
  /** Stand als Text: 8 Wörter, Länge, Rest des Puffers (hex). */
  std::string stand() const {
    std::string s; char b[24];
    for (int i = 0; i < 8; i++) { snprintf(b, sizeof b, "%08x", h[i]); s += b; }
    snprintf(b, sizeof b, ":%llu:", (unsigned long long)laenge); s += b;
    for (size_t i = 0; i < n; i++) { snprintf(b, sizeof b, "%02x", puffer[i]); s += b; }
    return s;
  }
  bool ausStand(const std::string &s) {
    if (s.size() < 66) return false;
    for (int i = 0; i < 8; i++) h[i] = (uint32_t)strtoul(s.substr(8 * i, 8).c_str(), nullptr, 16);
    size_t a = s.find(':', 64), b = s.find(':', a + 1);
    if (a != 64 || b == std::string::npos) return false;
    laenge = strtoull(s.substr(a + 1, b - a - 1).c_str(), nullptr, 10);
    std::string rest = s.substr(b + 1);
    n = rest.size() / 2;
    if (n >= 64 || n != laenge % 64) return false;
    for (size_t i = 0; i < n; i++) puffer[i] = (uint8_t)strtoul(rest.substr(2 * i, 2).c_str(), nullptr, 16);
    return true;
  }
};

/* ---------- Kleinigkeiten für HTTP ---------- */

static std::string base64(const std::string &s) {
  static const char *z = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  std::string r;
  size_t i = 0;
  for (; i + 2 < s.size(); i += 3) {
    uint32_t v = (uint8_t)s[i] << 16 | (uint8_t)s[i + 1] << 8 | (uint8_t)s[i + 2];
    r += z[v >> 18]; r += z[(v >> 12) & 63]; r += z[(v >> 6) & 63]; r += z[v & 63];
  }
  if (i + 1 == s.size()) { uint32_t v = (uint8_t)s[i] << 16; r += z[v >> 18]; r += z[(v >> 12) & 63]; r += "=="; }
  else if (i + 2 == s.size()) { uint32_t v = (uint8_t)s[i] << 16 | (uint8_t)s[i + 1] << 8; r += z[v >> 18]; r += z[(v >> 12) & 63]; r += z[(v >> 6) & 63]; r += '='; }
  return r;
}
/** Ein Pfadteil prozentkodiert (wie encodeURIComponent). */
static std::string kodiere(const std::string &s) {
  std::string r; char b[4];
  for (unsigned char c : s) {
    if (isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') r += (char)c;
    else { snprintf(b, sizeof b, "%%%02X", c); r += b; }
  }
  return r;
}
/** Ordnerpfad „a/b c“ → „/a/b%20c“ (leer bleibt leer). */
static std::string pfadKodiert(const std::string &p) {
  std::string r, teil;
  for (size_t i = 0; i <= p.size(); i++) {
    if (i == p.size() || p[i] == '/') { if (!teil.empty() && teil != "." && teil != "..") r += "/" + kodiere(teil); teil.clear(); }
    else teil += p[i];
  }
  return r;
}

/* ---------- Einstellungen ---------- */

enum Art { NEXTCLOUD, DATEIABLAGE, WEBDAV };
struct Ziel {
  Art art = NEXTCLOUD;
  std::string adresse, benutzer, passwort, ordner, freigabe;
  uint64_t teil = 8 * MB, vollBis = 2048 * MB;
  bool loeschen = false;
  int behalten = 14;
  std::string fehler;

  std::string ordnerUrl() const {
    if (art == NEXTCLOUD) return adresse + "/remote.php/dav/files/" + kodiere(benutzer) + pfadKodiert(ordner);
    if (art == DATEIABLAGE) return adresse + "/public.php/webdav";
    return adresse + pfadKodiert(ordner);
  }
  std::string dateiUrl(const std::string &d) const { return ordnerUrl() + "/" + kodiere(d); }
  std::string uploadsUrl(const std::string &name) const { return adresse + "/remote.php/dav/uploads/" + kodiere(benutzer) + "/dms-" + kodiere(name); }
  /** Ziel in Worten für das DMS (ohne Zugangsdaten). */
  std::string text() const {
    if (art == DATEIABLAGE) return "Nextcloud-Dateiablage " + adresse;
    return std::string(art == NEXTCLOUD ? "Nextcloud " : "WebDAV ") + ordnerUrl();
  }
  std::string anmeldung() const {
    if (art == DATEIABLAGE) return freigabe.empty() ? "" : "Basic " + base64(freigabe + ":" + passwort);
    if (benutzer.empty() && passwort.empty()) return "";
    return "Basic " + base64(benutzer + ":" + passwort);
  }
};

static Ziel zielAus(const Json &e) {
  Ziel z;
  const Json &s = e["einstellungen"];
  std::string art = s["art"].text("Nextcloud");
  z.art = art.find("Dateiablage") != std::string::npos ? DATEIABLAGE : art.find("WebDAV") != std::string::npos ? WEBDAV : NEXTCLOUD;
  z.adresse = s["adresse"].text();
  while (!z.adresse.empty() && z.adresse.back() == '/') z.adresse.pop_back();
  z.benutzer = s["benutzer"].text();
  z.passwort = s["passwort"].text();
  z.ordner = s["ordner"].text(z.art == WEBDAV ? "" : "DMS-Sicherung");
  // Freigabe: der Link (…/s/<token>) oder nur das Token.
  z.freigabe = s["freigabe"].text();
  size_t p = z.freigabe.find("/s/");
  if (p != std::string::npos) z.freigabe = z.freigabe.substr(p + 3);
  while (!z.freigabe.empty() && (z.freigabe.back() == '/' || z.freigabe.back() == ' ')) z.freigabe.pop_back();
  int t = (int)s["teil_mb"].zahl(8);
  z.teil = (uint64_t)(t < 5 ? 5 : t > 8 ? 8 : t) * MB;
  double v = s["voll_mb"].zahl(2048);
  z.vollBis = (uint64_t)(v < 0 ? 0 : v) * MB;
  z.loeschen = s["extern_loeschen"].wahr(false);
  int b = (int)s["extern_behalten"].zahl(14);
  z.behalten = b < 1 ? 1 : b;
  if (z.adresse.empty()) z.fehler = "Es ist keine Adresse eingetragen (Werkbank → Pakete → Sicherungsziel WebDAV → Einstellungen).";
  else if (z.art == NEXTCLOUD && z.benutzer.empty()) z.fehler = "Für Nextcloud fehlt der Benutzer (Einstellungen des Pakets).";
  else if (z.art == DATEIABLAGE && z.freigabe.empty()) z.fehler = "Für die Dateiablage fehlt der Freigabe-Link (Einstellungen des Pakets).";
  return z;
}

/* ---------- Netz ---------- */

struct Antwort { int status; std::string text; };

static Antwort netz(const Ziel &z, const char *methode, const std::string &url, const std::vector<std::pair<std::string, std::string>> &kopf, const char *body = nullptr, size_t blen = 0) {
  std::string k = "{";
  std::string a = z.anmeldung();
  bool erst = true;
  auto dazu = [&](const std::string &n, const std::string &w) { k += (erst ? "" : ",") + jsonText(n) + ":" + jsonText(w); erst = false; };
  if (!a.empty()) dazu("authorization", a);
  if (z.art == DATEIABLAGE) dazu("x-requested-with", "XMLHttpRequest");
  for (auto &x : kopf) dazu(x.first, x.second);
  std::string q = "{\"methode\":" + jsonText(methode) + ",\"url\":" + jsonText(url) + ",\"kopf\":" + k + "}}";
  int s = dms_netz(q.data(), (int32_t)q.size(), body, (int32_t)blen);
  return { s, antwort() };
}

/** Grund in Worten; endgueltig: Eine Wiederholung hilft nicht (bis jemand etwas ändert). */
struct Problem { std::string grund; bool endgueltig = false; };
static Problem problem(const Ziel &z, const std::string &was, const Antwort &a) {
  char s[16]; snprintf(s, sizeof s, "%d", a.status);
  if (a.status == -2) return { "Die Adresse " + z.adresse + " ist nicht freigegeben – bitte die Einstellungen speichern und die Adresse bestätigen.", true };
  if (a.status < 0) return { "Das Ziel ist nicht erreichbar (" + kurz(a.text, 160) + ") – neuer Versuch folgt.", false };
  if (a.status == 401) return { "Anmeldung abgelehnt – Benutzer oder Passwort falsch (" + was + ", HTTP 401).", true };
  if (a.status == 403) return { "Kein Schreibrecht am Ziel (" + was + ", HTTP 403).", true };
  if (a.status == 404 || a.status == 409) return { std::string("Den Ordner gibt es am Ziel nicht (") + was + ", HTTP " + s + ") – Adresse und Ordner prüfen.", true };
  if (a.status == 507) return { "Der Speicher am Ziel ist voll (" + was + ", HTTP 507).", true };
  if (a.status == 413) return { std::string("Das Ziel lehnt die Größe ab (") + was + ", HTTP 413) – eine kleinere Teilgröße einstellen.", true };
  if (a.status == 423) return { "Die Datei am Ziel ist gesperrt (" + was + ", HTTP 423) – neuer Versuch folgt.", false };
  return { std::string("Das Ziel antwortet mit HTTP ") + s + " (" + was + ")" + (a.status >= 500 ? " – neuer Versuch folgt." : "."), a.status < 500 && a.status != 429 && a.status != 408 };
}
static bool ok(int s) { return s >= 200 && s < 300; }

/** Größe einer Datei am Ziel (PROPFIND, Depth 0); -1 = unbekannt. */
static int64_t groesseAmZiel(const Ziel &z, const std::string &url, Antwort &a) {
  static const char *koerper = "<?xml version=\"1.0\"?><d:propfind xmlns:d=\"DAV:\"><d:prop><d:getcontentlength/></d:prop></d:propfind>";
  a = netz(z, "PROPFIND", url, {{"depth", "0"}, {"content-type", "application/xml"}}, koerper, strlen(koerper));
  if (a.status != 207) return -1;
  size_t p = a.text.find("getcontentlength");
  if (p == std::string::npos) return -1;
  p = a.text.find('>', p);
  if (p == std::string::npos) return -1;
  return strtoll(a.text.c_str() + p + 1, nullptr, 10);
}

/* ---------- DMS ---------- */

/** Ein Stück der lokalen, verschlüsselten Sicherung. */
static bool lokal(const std::string &name, uint64_t ab, uint64_t n, std::string &aus, std::string &fehler) {
  std::string q = "{\"methode\":\"GET\",\"pfad\":" + jsonText("/sicherungen/" + name + "/datei?versatz=" + zahl(ab) + "&laenge=" + zahl(n)) + "}";
  int s = dms_api(q.data(), (int32_t)q.size());
  aus = antwort();
  if (s != 200) { char b[16]; snprintf(b, sizeof b, "%d", s); fehler = std::string("Das DMS liefert die Sicherung nicht (HTTP ") + b + "): " + kurz(aus, 200); return false; }
  return true;
}

/**
 * Stand der Kopie für Ablago (DMS #636): Das Paket schreibt im DMS nichts – der zuletzt gemerkte Stand geht als
 * „extern“ mit der Antwort auf den Aufruf zurück (auch neben „weiter“); Ablago trägt ihn ein.
 */
static std::string stand;
static void melde(const std::string &status, const Ziel &z, const std::string &extra = "") {
  stand = "{\"status\":" + jsonText(status) + ",\"ziel\":" + jsonText(z.text()) + extra + "}";
}
/** Antwort mit dem Stand; mehr: weitere Felder davor (z. B. "weiter":{…}). */
static void antworte(const std::string &mehr = "") {
  ergebnis("{" + mehr + (mehr.empty() || stand.empty() ? "" : ",") + (stand.empty() ? "" : "\"extern\":" + stand) + "}");
}
/** Rückgabewert bei einem Fehler: 2 = endgültig (hier muss jemand handeln), 1 = vorübergehend. Ablago wiederholt beides. */
static int fehlerCode = 1;

/* ---------- Ablauf ---------- */

enum Phase { START = 0, HOCHLADEN = 1, ABSCHLUSS = 2, PRUEFEN = 3, AUFRAEUMEN = 4 };
struct Stand {
  Phase phase = START;
  uint64_t versatz = 0;   // hochgeladen bzw. (beim Prüfen) zurückgelesen bis hier
  int teil = 1;           // nächster Teil (Nextcloud)
  bool voll = false;      // vollständig zurücklesen statt Stichproben
  std::string sha;        // Stand der Prüfsumme beim Zurücklesen
};
static std::string weiterText(const Stand &s, uint64_t groesse) {
  char f[64];
  snprintf(f, sizeof f, "%s %llu von %llu MB", s.phase == PRUEFEN ? "geprüft" : "hochgeladen", (unsigned long long)(s.versatz / MB), (unsigned long long)(groesse / MB));
  return "\"weiter\":{\"phase\":" + zahl(s.phase) + ",\"versatz\":" + zahl(s.versatz) + ",\"teil\":" + zahl((uint64_t)s.teil) + ",\"voll\":" + (s.voll ? "true" : "false") +
    ",\"sha\":" + jsonText(s.sha) + ",\"fortschritt\":" + jsonText(f) + "}";
}

/** Tage seit 1970 aus JJJJ-MM-TT (für „letzte vollständige Prüfung“). */
static long tage(const std::string &iso) {
  if (iso.size() < 10) return 0;
  int j = atoi(iso.substr(0, 4).c_str()), m = atoi(iso.substr(5, 2).c_str()), d = atoi(iso.substr(8, 2).c_str());
  j -= m <= 2;
  long era = (j >= 0 ? j : j - 399) / 400;
  long yoe = j - era * 400, doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1, doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097 + doe - 719468;
}

struct Lauf {
  const Ziel &z;
  std::string name, datei, sha256, beginn;
  uint64_t groesse;
  Stand s;
  double start;
  bool zeitUm() const { return jetztMs() - start > BUDGET_MS; }
};

/**
 * Fehler: Der Grund ist das Ergebnis, der Rückgabewert sagt endgültig (2, „fehlgeschlagen“) oder vorübergehend (1,
 * „läuft“ mit Grund) – Ablago trägt das ein und wiederholt. Gibt intern 1 zurück („abbrechen“).
 */
static int scheitere(Lauf &l, const Problem &p, bool neuHochladen = false) {
  if (neuHochladen) speicherSchreiben("neu:" + l.name, "1");
  fehlerCode = p.endgueltig ? 2 : 1;
  log(p.endgueltig ? 3 : 2, l.name + ": " + p.grund);
  ergebnis(p.grund);
  return 1;
}

/** Ordner am Ziel anlegen (Teil für Teil); vorhanden ist auch gut. */
static bool ordnerAnlegen(Lauf &l, Problem &p) {
  if (l.z.art == DATEIABLAGE) return true;
  std::string basis = l.z.art == NEXTCLOUD ? l.z.adresse + "/remote.php/dav/files/" + kodiere(l.z.benutzer) : l.z.adresse;
  std::string ziel = l.z.ordnerUrl();
  // Erst schauen, ob der Ordner schon da ist.
  Antwort a = netz(l.z, "PROPFIND", ziel, {{"depth", "0"}});
  if (a.status == 207) return true;
  if (a.status != 404) { p = problem(l.z, "Ordner prüfen", a); return false; }
  std::string pfad = l.z.ordner, teil, bis = basis;
  for (size_t i = 0; i <= pfad.size(); i++) {
    if (i == pfad.size() || pfad[i] == '/') {
      if (!teil.empty() && teil != "." && teil != "..") {
        bis += "/" + kodiere(teil);
        Antwort m = netz(l.z, "MKCOL", bis, {});
        if (!ok(m.status) && m.status != 405) { p = problem(l.z, "Ordner anlegen", m); return false; }
      }
      teil.clear();
    } else teil += pfad[i];
  }
  return true;
}

static int hochladen(Lauf &l) {
  const Ziel &z = l.z;
  bool amStueck = l.groesse <= z.teil || z.art == DATEIABLAGE;
  std::string stueck, fehler;
  if (amStueck) {
    if (l.groesse > AM_STUECK_MAX) {
      return scheitere(l, { "Die Sicherung ist " + mbText(l.groesse) + " groß – eine Dateiablage nimmt nur Dateien bis " + mbText(AM_STUECK_MAX) + " am Stück an. Nimm einen Nextcloud-Benutzer (Hochladen in Teilen) statt der Dateiablage.", true });
    }
    std::string alles;
    alles.reserve((size_t)l.groesse);
    for (uint64_t ab = 0; ab < l.groesse; ab += STUECK) {
      if (!lokal(l.name, ab, std::min(STUECK, l.groesse - ab), stueck, fehler)) return scheitere(l, { fehler, false });
      alles += stueck;
    }
    if (alles.size() != l.groesse) return scheitere(l, { "Das DMS lieferte " + zahl(alles.size()) + " statt " + zahl(l.groesse) + " Bytes.", false });
    Antwort a = netz(z, "PUT", z.dateiUrl(l.datei), {{"content-type", "application/octet-stream"}, {"oc-checksum", "SHA256:" + l.sha256}}, alles.data(), alles.size());
    if (!ok(a.status)) return scheitere(l, problem(z, "Hochladen", a));
    l.s.versatz = l.groesse;
    l.s.phase = ABSCHLUSS;
    return 0;
  }
  // In Teilen.
  while (l.s.versatz < l.groesse) {
    uint64_t n = std::min(z.teil, l.groesse - l.s.versatz);
    if (!lokal(l.name, l.s.versatz, n, stueck, fehler)) return scheitere(l, { fehler, false });
    if (stueck.size() != n) return scheitere(l, { "Das DMS lieferte ein unvollständiges Stück.", false });
    Antwort a;
    if (z.art == NEXTCLOUD) {
      char nr[16]; snprintf(nr, sizeof nr, "/%05d", l.s.teil);
      a = netz(z, "PUT", l.z.uploadsUrl(l.name) + nr, {{"content-type", "application/octet-stream"}, {"destination", z.dateiUrl(l.datei)}, {"oc-total-length", zahl(l.groesse)}}, stueck.data(), stueck.size());
    } else if (l.s.versatz == 0) {
      a = netz(z, "PUT", z.dateiUrl(l.datei + ".teil"), {{"content-type", "application/octet-stream"}}, stueck.data(), stueck.size());
    } else {
      std::string bereich = "bytes " + zahl(l.s.versatz) + "-" + zahl(l.s.versatz + n - 1) + "/" + zahl(l.groesse);
      a = netz(z, "PUT", z.dateiUrl(l.datei + ".teil"), {{"content-type", "application/octet-stream"}, {"content-range", bereich}}, stueck.data(), stueck.size());
      if (a.status == 400 || a.status == 405 || a.status == 416 || a.status == 501) {
        return scheitere(l, { "Dieser WebDAV-Server nimmt keine Teile an (Content-Range, HTTP " + zahl((uint64_t)a.status) + "). Sicherungen bis zur Teilgröße gehen am Stück; für größere nimm Nextcloud oder einen Server, der Teile annimmt (z. B. Apache mit mod_dav).", true }, true);
      }
    }
    if (!ok(a.status)) return scheitere(l, problem(z, "Hochladen, Teil " + zahl((uint64_t)l.s.teil), a));
    l.s.versatz += n; l.s.teil++;
    if (l.s.versatz < l.groesse && l.zeitUm()) return 2;
  }
  l.s.phase = ABSCHLUSS;
  return 0;
}

static int abschliessen(Lauf &l) {
  const Ziel &z = l.z;
  bool amStueck = l.groesse <= z.teil || z.art == DATEIABLAGE;
  if (!amStueck) {
    Antwort a;
    if (z.art == NEXTCLOUD) a = netz(z, "MOVE", z.uploadsUrl(l.name) + "/.file", {{"destination", z.dateiUrl(l.datei)}, {"overwrite", "T"}, {"oc-total-length", zahl(l.groesse)}, {"oc-checksum", "SHA256:" + l.sha256}});
    else a = netz(z, "MOVE", z.dateiUrl(l.datei + ".teil"), {{"destination", z.dateiUrl(l.datei)}, {"overwrite", "T"}});
    if (a.status == 404 || a.status == 409 || a.status == 400) return scheitere(l, { "Die hochgeladenen Teile fehlen am Ziel (HTTP " + zahl((uint64_t)a.status) + ") – das Paket lädt die Sicherung beim nächsten Versuch neu hoch.", false }, true);
    if (!ok(a.status)) return scheitere(l, problem(z, "Zusammensetzen", a));
  }
  // Schlanke Metadaten daneben: damit lässt sich die Kopie wiederherstellen.
  std::string q = "{\"methode\":\"GET\",\"pfad\":" + jsonText("/sicherungen/" + l.name) + "}";
  if (dms_api(q.data(), (int32_t)q.size()) != 200) return scheitere(l, { "Das DMS liefert die Metadaten nicht: " + kurz(antwort(), 200), false });
  std::string metaText = antwort();
  Json m = JsonLeser::lies(metaText.data(), metaText.size());
  m.o.erase("name");
  std::string json = jsonSchreib(m) + "\n";
  Antwort a = netz(z, "PUT", z.dateiUrl(l.name + ".json"), {{"content-type", "application/json"}}, json.data(), json.size());
  if (!ok(a.status)) return scheitere(l, problem(z, "Metadaten hochladen", a));
  l.s.phase = PRUEFEN; l.s.versatz = 0;
  // Vollständig zurücklesen: bis zur eingestellten Größe immer, sonst wenn die letzte vollständige Prüfung zu alt ist.
  std::string zuletzt = speicherLesen("voll_am");
  l.s.voll = l.groesse <= z.vollBis || zuletzt.empty() || tage(l.beginn) - tage(zuletzt) >= VOLL_TAGE;
  l.s.sha.clear();
  return 0;
}

/** Bereich vom Ziel lesen (Range); false bei Fehler (Problem gesetzt). */
static bool zurueck(Lauf &l, uint64_t ab, uint64_t n, std::string &aus, Problem &p) {
  Antwort a = netz(l.z, "GET", l.z.dateiUrl(l.datei), {{"range", "bytes=" + zahl(ab) + "-" + zahl(ab + n - 1)}});
  if (a.status == 200 && ab == 0 && a.text.size() == l.groesse && n >= l.groesse) { aus = a.text; return true; }
  if (a.status != 206) {
    // 200 (ganze Datei) oder -3 (Antwort zu groß): Der Server übergeht Range.
    p = a.status == 200 || a.status == -3 ? Problem{ "Das Ziel liefert keine Teile einer Datei (Range) – zurücklesen geht nicht.", true } : problem(l.z, "Zurücklesen", a);
    return false;
  }
  aus = a.text;
  if (aus.size() != n) { p = { "Das Ziel lieferte beim Zurücklesen " + zahl(aus.size()) + " statt " + zahl(n) + " Bytes.", false }; return false; }
  return true;
}

static int pruefen(Lauf &l) {
  const Ziel &z = l.z;
  if (z.art == DATEIABLAGE) {
    // Eine Dateiablage kann nicht lesen: ehrlich „hochgeladen“ – angenommen hat das Ziel die Datei (HTTP 2xx).
    melde("hochgeladen", z, ",\"pruefung\":\"keine\",\"bytes\":" + zahl(l.groesse) + ",\"gesamt\":" + zahl(l.groesse));
    l.s.phase = AUFRAEUMEN;
    return 0;
  }
  if (l.s.versatz == 0) {
    Antwort a;
    int64_t g = groesseAmZiel(z, z.dateiUrl(l.datei), a);
    if (g < 0) return scheitere(l, a.status == 207 ? Problem{ "Das Ziel nennt die Größe der Datei nicht.", false } : problem(z, "Größe prüfen", a));
    if ((uint64_t)g != l.groesse) return scheitere(l, { "Die Datei am Ziel ist " + zahl((uint64_t)g) + " statt " + zahl(l.groesse) + " Bytes groß – das Paket lädt sie beim nächsten Versuch neu hoch.", true }, true);
  }
  Problem p;
  std::string stueck;
  if (l.s.voll) {
    Sha256 h;
    if (!l.s.sha.empty() && !h.ausStand(l.s.sha)) l.s.versatz = 0;
    while (l.s.versatz < l.groesse) {
      uint64_t n = std::min(STUECK, l.groesse - l.s.versatz);
      if (!zurueck(l, l.s.versatz, n, stueck, p)) {
        if (p.endgueltig && p.grund.find("Range") != std::string::npos) {
          melde("hochgeladen", z, ",\"pruefung\":\"groesse\",\"bytes\":" + zahl(l.groesse) + ",\"gesamt\":" + zahl(l.groesse));
          log(2, l.name + ": " + p.grund + " Nur die Größe ist bestätigt.");
          l.s.phase = AUFRAEUMEN;
          return 0;
        }
        return scheitere(l, p);
      }
      h.update((const uint8_t *)stueck.data(), stueck.size());
      l.s.versatz += n;
      if (l.s.versatz < l.groesse && l.zeitUm()) { l.s.sha = h.stand(); return 2; }
    }
    if (h.hex() != l.sha256) return scheitere(l, { "Die Prüfsumme am Ziel weicht ab – die Kopie ist beschädigt oder wurde verändert. Das Paket lädt sie beim nächsten Versuch neu hoch.", true }, true);
    speicherSchreiben("voll_am", l.beginn.substr(0, 10));
    melde("geprueft", z, ",\"pruefung\":\"pruefsumme\",\"bytes\":" + zahl(l.groesse) + ",\"gesamt\":" + zahl(l.groesse));
  } else {
    // Stichproben: Stellen aus der Prüfsumme der Sicherung, je 1 MB vom Ziel und vom DMS.
    std::string hier, fehler;
    uint64_t raum = l.groesse > STICHPROBE ? l.groesse - STICHPROBE : 0;
    for (int i = 0; i < STICHPROBEN; i++) {
      uint64_t w = strtoull(l.sha256.substr((size_t)(i * 8) % 56, 8).c_str(), nullptr, 16);
      uint64_t ab = i == 0 ? 0 : i == STICHPROBEN - 1 ? raum : (raum ? (w * 2654435761ull) % raum : 0);
      uint64_t n = std::min(STICHPROBE, l.groesse - ab);
      if (!zurueck(l, ab, n, stueck, p)) return scheitere(l, p);
      if (!lokal(l.name, ab, n, hier, fehler)) return scheitere(l, { fehler, false });
      if (hier != stueck) return scheitere(l, { "Eine Stichprobe am Ziel weicht ab (ab Byte " + zahl(ab) + ") – die Kopie ist beschädigt oder wurde verändert. Das Paket lädt sie beim nächsten Versuch neu hoch.", true }, true);
    }
    melde("geprueft", z, ",\"pruefung\":\"stichprobe\",\"bytes\":" + zahl(l.groesse) + ",\"gesamt\":" + zahl(l.groesse));
  }
  l.s.phase = AUFRAEUMEN;
  return 0;
}

/** Ältere Sicherungen am Ziel löschen – nur, wenn ausdrücklich eingeschaltet. Fehler hier stören nicht. */
static void aufraeumen(Lauf &l) {
  const Ziel &z = l.z;
  if (!z.loeschen || z.art == DATEIABLAGE) return;
  Antwort a = netz(z, "PROPFIND", z.ordnerUrl(), {{"depth", "1"}});
  if (a.status != 207) { log(2, "Aufräumen am Ziel: Liste nicht lesbar (HTTP " + zahl((uint64_t)(a.status < 0 ? 0 : a.status)) + ")."); return; }
  std::vector<std::string> namen;
  const std::string endung = ".dms-sicherung";
  for (size_t p = 0; (p = a.text.find("href>", p)) != std::string::npos; ) {
    p += 5;
    size_t e = a.text.find('<', p);
    if (e == std::string::npos) break;
    std::string h = a.text.substr(p, e - p);
    size_t s = h.find_last_of('/');
    std::string n = s == std::string::npos ? h : h.substr(s + 1);
    if (n.size() > endung.size() && n.compare(n.size() - endung.size(), endung.size(), endung) == 0) namen.push_back(n.substr(0, n.size() - endung.size()));
  }
  // Namen beginnen mit Datum und Uhrzeit: absteigend sortiert = neueste zuerst.
  std::sort(namen.begin(), namen.end(), [](const std::string &x, const std::string &y) { return x > y; });
  int weg = 0;
  for (size_t i = (size_t)z.behalten; i < namen.size(); i++) {
    if (namen[i] == l.name) continue;
    Antwort d = netz(z, "DELETE", z.dateiUrl(namen[i] + endung), {});
    if (!ok(d.status) && d.status != 404) { log(2, "Aufräumen am Ziel: " + namen[i] + " nicht gelöscht (HTTP " + zahl((uint64_t)(d.status < 0 ? 0 : d.status)) + ")."); continue; }
    netz(z, "DELETE", z.dateiUrl(namen[i] + ".json"), {});
    weg++;
  }
  if (weg) log(1, "Aufräumen am Ziel: " + zahl((uint64_t)weg) + " ältere Sicherungen gelöscht.");
}

static int sicherungFertig(const Json &e) {
  const Json &d = e["daten"];
  Ziel z = zielAus(e);
  std::string name = d["name"].text();
  if (name.empty()) { ergebnis("Ereignis ohne Namen der Sicherung."); return 0; }
  Lauf l{ z, name, d["datei"].text(), d["sha256"].text(), d["beginn"].text(), (uint64_t)d["groesse"].zahl(0), Stand{}, jetztMs() };
  if (!z.fehler.empty()) { ergebnis(z.fehler); return 2; }
  if (l.datei.empty() || l.sha256.size() != 64 || !l.groesse) { ergebnis("Die Angaben zur Sicherung sind unvollständig."); return 0; }
  const Json &w = d["weiter"];
  // Nach einer abweichenden Prüfsumme oder fehlenden Teilen: von vorn (statt an der gespeicherten Stelle).
  bool neu = speicherLesen("neu:" + name) == "1";
  if (neu) speicherSchreiben("neu:" + name, "");
  if (w.art == Json::OBJEKT && !neu) {
    l.s.phase = (Phase)(int)w["phase"].zahl(0);
    l.s.versatz = (uint64_t)w["versatz"].zahl(0);
    l.s.teil = (int)w["teil"].zahl(1);
    l.s.voll = w["voll"].wahr(false);
    l.s.sha = w["sha"].text();
  }
  if (l.s.phase == START) {
    melde("laeuft", z, ",\"bytes\":0,\"gesamt\":" + zahl(l.groesse));
    // Von vorn nach einem Fehler beim Zusammensetzen oder Prüfen: alte Teile weg.
    if (neu && z.art == NEXTCLOUD) netz(z, "DELETE", z.uploadsUrl(name), {});
    Problem p;
    if (!ordnerAnlegen(l, p)) { scheitere(l, p); return fehlerCode; }
    if (z.art == NEXTCLOUD && l.groesse > z.teil) {
      Antwort a = netz(z, "MKCOL", z.uploadsUrl(name), {{"destination", z.dateiUrl(l.datei)}});
      if (!ok(a.status) && a.status != 405) { scheitere(l, problem(z, "Hochladen vorbereiten", a)); return fehlerCode; }
    }
    l.s.phase = HOCHLADEN; l.s.versatz = 0; l.s.teil = 1;
  } else melde("laeuft", z, ",\"bytes\":" + zahl(l.s.phase >= PRUEFEN ? l.groesse : l.s.versatz) + ",\"gesamt\":" + zahl(l.groesse));
  for (;;) {
    int r = 0;
    switch (l.s.phase) {
      case START: case HOCHLADEN: r = hochladen(l); break;
      case ABSCHLUSS: r = abschliessen(l); break;
      case PRUEFEN: r = pruefen(l); break;
      case AUFRAEUMEN: aufraeumen(l); log(1, "Sicherung " + name + " außer Haus: " + z.text()); antworte(); return 0;
    }
    if (r == 1) return fehlerCode;
    if (r == 2 || (l.zeitUm() && l.s.phase != AUFRAEUMEN)) {
      // Fortsetzung: noch unterwegs – mit dem Fortschritt bis hier.
      melde("laeuft", z, ",\"bytes\":" + zahl(l.s.phase >= PRUEFEN ? l.groesse : l.s.versatz) + ",\"gesamt\":" + zahl(l.groesse));
      antworte(weiterText(l.s, l.groesse));
      return 0;
    }
  }
}

/* ---------- Aktion „Verbindung testen“ ---------- */

static int verbindungTesten(const Json &e) {
  Ziel z = zielAus(e);
  if (!z.fehler.empty()) { ergebnis(z.fehler); return 1; }
  if (z.art == DATEIABLAGE) {
    // Eine Dateiablage lässt sich nicht lesen; die Freigabe-Seite zeigt, ob es sie gibt.
    Ziel ohne = z; ohne.passwort.clear(); ohne.freigabe.clear();
    Antwort a = netz(ohne, "GET", z.adresse + "/s/" + kodiere(z.freigabe), {});
    if (ok(a.status)) { ergebnis("Die Dateiablage " + z.adresse + "/s/… ist erreichbar. Ob das Passwort stimmt, zeigt erst das Hochladen. Zurücklesen kann eine Dateiablage nicht – die Werkbank zeigt deshalb „hochgeladen“ statt „geprüft“."); return 0; }
    ergebnis(problem(z, "Freigabe abrufen", a).grund);
    return 1;
  }
  Antwort a;
  double t0 = jetztMs();
  a = netz(z, "PROPFIND", z.ordnerUrl(), {{"depth", "0"}});
  char ms[32]; snprintf(ms, sizeof ms, "%.0f ms", jetztMs() - t0);
  if (a.status == 207) { ergebnis("Verbindung in Ordnung (" + std::string(ms) + "): " + z.text() + " – Anmeldung angenommen, der Ordner ist da."); return 0; }
  if (a.status == 404) { ergebnis("Anmeldung angenommen, den Ordner gibt es noch nicht – das Paket legt ihn bei der ersten Sicherung an: " + z.text()); return 0; }
  ergebnis(problem(z, "Verbindung testen", a).grund);
  return 1;
}

/* ---------- Exporte ---------- */

static char *eingang = nullptr;

extern "C" __attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = (char *)malloc((size_t)n + 1);
  if (eingang) eingang[n] = 0;
  return eingang;
}

extern "C" __attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t len) {
  Json e = JsonLeser::lies(json, (size_t)len);
  if (e["art"].text() == "sicherung.fertig") return sicherungFertig(e);
  return 0;
}

extern "C" __attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) {
  Json e = JsonLeser::lies(json, (size_t)len);
  std::string a = e["aktion"].text();
  if (a == "verbindung_testen") return verbindungTesten(e);
  log(2, "Unbekannte Aktion: " + kurz(a, 60));
  ergebnis("Unbekannte Aktion.");
  return 1;
}
