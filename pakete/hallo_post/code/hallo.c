/*
 * Hallo Post – kleinstes Beispiel für ein Paket mit Code (DMS-Paket-ABI 1).
 *
 * Zählt jede neue Post im Speicher des Pakets und nennt die Zahl, wenn ein Administrator in
 * Werkbank → Pakete → Hallo Post → Einstellungen auf „Wie viel Post kam bisher?“ klickt.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DMS(name) __attribute__((import_module("dms"), import_name(#name)))
DMS(antwort_laenge) int32_t dms_antwort_laenge(void);
DMS(antwort_lesen) int32_t dms_antwort_lesen(char *ziel, int32_t max);
DMS(speicher_lesen) int32_t dms_speicher_lesen(const char *schluessel, int32_t len);
DMS(speicher_schreiben) int32_t dms_speicher_schreiben(const char *schluessel, int32_t len, const char *wert, int32_t wlen);
DMS(log) int32_t dms_log(int32_t stufe, const char *text, int32_t len);
DMS(ergebnis) int32_t dms_ergebnis(const char *text, int32_t len);

static char *eingang;

/* Das DMS fragt nach Platz für die Eingabe (JSON) und schreibt sie dorthin. */
__attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = malloc((size_t)n + 1);
  if (eingang) eingang[n] = 0;
  return eingang;
}

/* Bisherige Zahl aus dem Speicher des Pakets (Text je Schlüssel, bleibt zwischen Aufrufen). */
static int zahl(void) {
  if (dms_speicher_lesen("zahl", 4) < 0) return 0;
  char t[16] = {0};
  int32_t n = dms_antwort_laenge();
  dms_antwort_lesen(t, n < 15 ? n : 15);
  return atoi(t);
}

static void melde(const char *t) { dms_ergebnis(t, (int32_t)strlen(t)); }

/* Ein Ereignis: { "art": "post.angelegt", "daten": { "mappe": "…", "kanal": "…" }, … } */
__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t len) {
  (void)len;
  if (!strstr(json, "\"art\":\"post.angelegt\"")) return 0; /* andere Ereignisse: nichts zu tun */
  int neu = zahl() + 1;
  char t[64];
  int n = snprintf(t, sizeof t, "%d", neu);
  if (dms_speicher_schreiben("zahl", 4, t, n) != 0) return 1; /* Fehler: das DMS versucht es später erneut */
  n = snprintf(t, sizeof t, "Neue Post Nr. %d", neu);
  dms_log(1, t, n);
  melde("gezählt");
  return 0;
}

/* Eine Aktion aus der Werkbank: { "aktion": "zaehlen", … } */
__attribute__((export_name("dms_aktion"))) int32_t dms_aktion(char *json, int32_t len) {
  (void)json; (void)len;
  char t[64];
  int z = zahl();
  snprintf(t, sizeof t, z == 1 ? "Bisher kam 1 neue Post." : "Bisher kamen %d neue Posts.", z);
  melde(t);
  return 0;
}
