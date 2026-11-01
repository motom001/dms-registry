/* Code-128-Leser für Graustufenbilder – Beschreibung in barcode.h. */
#include "barcode.h"

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* Strich-/Lückenbreiten (in Modulen) der Werte 0–105; 106 = Stopp (mit Abschlussstrich). ISO/IEC 15417. */
static const char *const MUSTER[107] = {
  "212222", "222122", "222221", "121223", "121322", "131222", "122213", "122312", "132212", "221213",
  "221312", "231212", "112232", "122132", "122231", "113222", "123122", "123221", "223211", "221132",
  "221231", "213212", "223112", "312131", "311222", "321122", "321221", "312212", "322112", "322211",
  "212123", "212321", "232121", "111323", "131123", "131321", "112313", "132113", "132311", "211313",
  "231113", "231311", "112133", "112331", "132131", "113123", "113321", "133121", "313121", "211331",
  "231131", "213113", "213311", "213131", "311123", "311321", "331121", "312113", "312311", "332111",
  "314111", "221411", "431111", "111224", "111422", "121124", "121421", "141122", "141221", "112214",
  "112412", "122114", "122411", "142112", "142211", "241211", "221114", "413111", "241112", "134111",
  "111242", "121142", "121241", "114212", "124112", "124211", "411212", "421112", "421211", "212141",
  "214121", "412121", "111143", "111341", "131141", "114113", "114311", "411113", "411311", "113141",
  "114131", "311141", "411131", "211412", "211214", "211232", "2331112",
};
enum { START_A = 103, START_C = 105, STOPP = 106, WERTE_MAX = 90 };

#define BLOCK 32        /* Bildpunkte je Block für die örtliche Schwelle */
#define KONTRAST 40.0f  /* kleinster Unterschied hell/dunkel, sonst gilt die Stelle als hell */
#define RUHEZONE 4.0f   /* Module hell vor dem Start und nach dem Stopp (Norm: 10; Scans sind ungenau) */

static int muster[107][6];
static int tw[107][4]; /* Abstände gleichartiger Kanten (Strich+Lücke, Lücke+Strich …) – unempfindlich gegen verlaufende Tinte */
static int bereit = 0;

static void vorbereiten(void) {
  if (bereit) return;
  for (int v = 0; v < 107; v++) {
    for (int i = 0; i < 6; i++) muster[v][i] = MUSTER[v][i] - '0';
    for (int i = 0; i < 4; i++) tw[v][i] = muster[v][i] + muster[v][i + 1];
  }
  bereit = 1;
}

/* Ein Zeichen aus sechs Breiten (Strich zuerst); -1, wenn es keins ist. Stopp (106) über seine ersten sechs Elemente. */
static int erkenne(const float *w) {
  float summe = 0;
  for (int i = 0; i < 6; i++) summe += w[i];
  if (summe <= 0) return -1;
  float m[6];
  for (int i = 0; i < 6; i++) m[i] = w[i] * 11.0f / summe;
  int t[4];
  for (int i = 0; i < 4; i++) t[i] = (int)lroundf(m[i] + m[i + 1]);
  int beste = -1;
  float besteAbw = 1e9f;
  for (int v = 0; v < 107; v++) {
    if (tw[v][0] != t[0] || tw[v][1] != t[1] || tw[v][2] != t[2] || tw[v][3] != t[3]) continue;
    float abw = 0;
    for (int i = 0; i < 6; i++) abw += fabsf(m[i] - (float)muster[v][i]);
    if (abw < besteAbw) { besteAbw = abw; beste = v; }
  }
  if (beste >= 0 && besteAbw <= 3.0f) return beste;
  /* Zweiter Versuch über die Breiten selbst (z. B. wenn eine Kante verrauscht ist). */
  beste = -1;
  besteAbw = 1e9f;
  for (int v = 0; v < 107; v++) {
    float abw = 0, einzeln = 0;
    for (int i = 0; i < 6; i++) {
      float a = fabsf(m[i] - (float)muster[v][i]);
      abw += a;
      if (a > einzeln) einzeln = a;
    }
    if (einzeln <= 0.7f && abw <= 2.2f && abw < besteAbw) { besteAbw = abw; beste = v; }
  }
  return beste;
}

/* Werte (Start, Daten ohne Prüfzeichen) → Text. 0, wenn er nicht passt. */
static int alsText(const int *v, int n, char *aus) {
  int satz = v[0] - START_A; /* 0 = A, 1 = B, 2 = C */
  int umschalten = 0;
  size_t len = 0;
  for (int i = 1; i < n; i++) {
    int x = v[i];
    int s = satz;
    if (umschalten) { s = satz == 0 ? 1 : 0; umschalten = 0; }
    if (s == 2) {
      if (x < 100) {
        if (len + 2 >= BC_TEXT_MAX) return 0;
        aus[len++] = (char)('0' + x / 10);
        aus[len++] = (char)('0' + x % 10);
      } else if (x == 100) satz = 1;
      else if (x == 101) satz = 0;
      else if (x != 102) return 0; /* FNC1 überspringen */
      continue;
    }
    if (x < 96) {
      int c = s == 0 ? (x < 64 ? x + 32 : x - 64) : x + 32;
      if (len + 1 >= BC_TEXT_MAX) return 0;
      aus[len++] = (char)(c < 32 || c > 126 ? '?' : c);
      continue;
    }
    switch (x) {
      case 98: umschalten = 1; break;
      case 99: satz = 2; break;
      case 100: if (s == 0) satz = 1; break;  /* in B: FNC4 */
      case 101: if (s == 1) satz = 0; break;  /* in A: FNC4 */
      case 96: case 97: case 102: break;      /* FNC3, FNC2, FNC1 */
      default: return 0;
    }
  }
  aus[len] = 0;
  return len > 0;
}

static int merke(bc_fund *funde, int anzahl, int max, const char *text) {
  for (int i = 0; i < anzahl; i++)
    if (!strcmp(funde[i].text, text)) { funde[i].treffer++; return anzahl; }
  if (anzahl >= max) return anzahl;
  strcpy(funde[anzahl].text, text);
  funde[anzahl].treffer = 1;
  return anzahl + 1;
}

/* Läufe (Breiten, dunkel ja/nein) nach Code 128 durchsuchen. */
static int lies(const float *w, const unsigned char *dunkel, int r, bc_fund *funde, int anzahl, int max) {
  int werte[WERTE_MAX + 2];
  for (int k = 1; k + 6 < r; k++) {
    if (!dunkel[k]) continue;
    float summe = 0;
    for (int i = 0; i < 6; i++) summe += w[k + i];
    if (w[k - 1] < RUHEZONE * summe / 11.0f) continue;
    int v = erkenne(w + k);
    if (v < START_A || v > START_C) continue;
    int nw = 0, ok = 0, j = k + 6;
    float mittel = summe;
    werte[nw++] = v;
    while (j + 5 < r) {
      float s2 = 0;
      for (int i = 0; i < 6; i++) s2 += w[j + i];
      if (fabsf(s2 - mittel) > 0.25f * mittel) break;
      int x = erkenne(w + j);
      if (x < 0 || (x >= START_A && x <= START_C)) break;
      if (x == STOPP) {
        float u = s2 / 11.0f;
        if (j + 6 < r && dunkel[j + 6] && w[j + 6] > 1.0f * u && w[j + 6] < 3.5f * u && (j + 7 >= r || w[j + 7] >= RUHEZONE * u)) ok = 1;
        break;
      }
      if (nw >= WERTE_MAX) break;
      werte[nw++] = x;
      mittel = 0.8f * mittel + 0.2f * s2;
      j += 6;
    }
    if (!ok || nw < 3) continue; /* Start, mindestens ein Zeichen, Prüfzeichen */
    int pruef = werte[0];
    for (int i = 1; i < nw - 1; i++) pruef += werte[i] * i;
    if (pruef % 103 != werte[nw - 1]) continue;
    char text[BC_TEXT_MAX];
    if (!alsText(werte, nw - 1, text)) continue;
    anzahl = merke(funde, anzahl, max, text);
    k = j + 6;
  }
  return anzahl;
}

int bc_linie(const float *v, int n, bc_fund *funde, int anzahl, int max) {
  vorbereiten();
  if (n < 40) return anzahl;
  int bloecke = (n + BLOCK - 1) / BLOCK;
  float *lo = malloc(sizeof(float) * (size_t)bloecke), *hi = malloc(sizeof(float) * (size_t)bloecke);
  float *schwelle = malloc(sizeof(float) * (size_t)n);
  float *w = malloc(sizeof(float) * (size_t)(n + 1));
  unsigned char *dunkel = malloc((size_t)(n + 1));
  float *w2 = malloc(sizeof(float) * (size_t)(n + 1));
  unsigned char *dunkel2 = malloc((size_t)(n + 1));
  if (!lo || !hi || !schwelle || !w || !dunkel || !w2 || !dunkel2) goto ende;

  /* Örtliche Schwelle: Mitte zwischen hellstem und dunkelstem Wert in drei Blöcken. */
  for (int b = 0; b < bloecke; b++) {
    float a = 255, z = 0;
    for (int i = b * BLOCK; i < n && i < (b + 1) * BLOCK; i++) { if (v[i] < a) a = v[i]; if (v[i] > z) z = v[i]; }
    lo[b] = a; hi[b] = z;
  }
  for (int i = 0; i < n; i++) {
    int b = i / BLOCK;
    float a = lo[b], z = hi[b];
    if (b > 0) { if (lo[b - 1] < a) a = lo[b - 1]; if (hi[b - 1] > z) z = hi[b - 1]; }
    if (b + 1 < bloecke) { if (lo[b + 1] < a) a = lo[b + 1]; if (hi[b + 1] > z) z = hi[b + 1]; }
    schwelle[i] = z - a >= KONTRAST ? (a + z) / 2 : -1.0f;
  }

  /* Kanten auf Bruchteile eines Bildpunkts (lineare Interpolation an der Schwelle) → Läufe. */
  int r = 0, d = v[0] < schwelle[0];
  float letzte = 0;
  for (int i = 1; i < n; i++) {
    int di = v[i] < schwelle[i];
    if (di == d) continue;
    float s = schwelle[i] >= 0 && schwelle[i - 1] >= 0 ? (schwelle[i] + schwelle[i - 1]) / 2 : (schwelle[i] >= 0 ? schwelle[i] : schwelle[i - 1]);
    float a = v[i - 1] - s, b = v[i] - s, anteil = a != b ? a / (a - b) : 0.5f;
    if (anteil < 0) anteil = 0;
    if (anteil > 1) anteil = 1;
    float pos = (float)(i - 1) + anteil;
    w[r] = pos - letzte; dunkel[r] = (unsigned char)d; r++;
    letzte = pos; d = di;
  }
  w[r] = (float)n - letzte; dunkel[r] = (unsigned char)d; r++;

  anzahl = lies(w, dunkel, r, funde, anzahl, max);
  for (int i = 0; i < r; i++) { w2[i] = w[r - 1 - i]; dunkel2[i] = dunkel[r - 1 - i]; } /* Seite auf dem Kopf */
  anzahl = lies(w2, dunkel2, r, funde, anzahl, max);
ende:
  free(lo); free(hi); free(schwelle); free(w); free(dunkel); free(w2); free(dunkel2);
  return anzahl;
}

int bc_suche(const uint8_t *bild, int breite, int hoehe, int zeilenlaenge, int schritt, bc_fund *funde, int max) {
  if (schritt < 1) schritt = 1;
  int n = breite > hoehe ? breite : hoehe;
  float *linie = malloc(sizeof(float) * (size_t)n);
  if (!linie) return 0;
  int anzahl = 0;
  /* Zeilen (je drei gemittelt gegen Rauschen) */
  for (int y = schritt / 2; y < hoehe; y += schritt) {
    const uint8_t *a = bild + (size_t)(y > 0 ? y - 1 : y) * (size_t)zeilenlaenge;
    const uint8_t *b = bild + (size_t)y * (size_t)zeilenlaenge;
    const uint8_t *c = bild + (size_t)(y + 1 < hoehe ? y + 1 : y) * (size_t)zeilenlaenge;
    for (int x = 0; x < breite; x++) linie[x] = (a[x] + b[x] + c[x]) / 3.0f;
    anzahl = bc_linie(linie, breite, funde, anzahl, max);
  }
  /* Spalten (quer liegende Seite) */
  for (int x = schritt / 2; x < breite; x += schritt) {
    int x0 = x > 0 ? x - 1 : x, x2 = x + 1 < breite ? x + 1 : x;
    for (int y = 0; y < hoehe; y++) {
      const uint8_t *z = bild + (size_t)y * (size_t)zeilenlaenge;
      linie[y] = (z[x0] + z[x] + z[x2]) / 3.0f;
    }
    anzahl = bc_linie(linie, hoehe, funde, anzahl, max);
  }
  free(linie);
  return anzahl;
}

double bc_dunkelanteil(const uint8_t *bild, int breite, int hoehe, int zeilenlaenge) {
  int x0 = breite / 20, x1 = breite - breite / 20, y0 = hoehe / 20, y1 = hoehe - hoehe / 20;
  long dunkel = 0, alle = 0;
  for (int y = y0; y < y1; y += 2) {
    const uint8_t *z = bild + (size_t)y * (size_t)zeilenlaenge;
    for (int x = x0; x < x1; x += 2) { alle++; if (z[x] < 128) dunkel++; }
  }
  return alle ? (double)dunkel / (double)alle : 0;
}

int bc_code128b(const char *text, int *breiten, int max) {
  vorbereiten();
  int werte[WERTE_MAX + 3], n = 0;
  werte[n++] = START_A + 1;
  int pruef = START_A + 1;
  for (int i = 0; text[i]; i++) {
    int c = (unsigned char)text[i];
    if (c < 32 || c > 127 || n >= WERTE_MAX) return 0;
    werte[n] = c - 32;
    pruef += werte[n] * n;
    n++;
  }
  werte[n++] = pruef % 103;
  werte[n++] = STOPP;
  int k = 0;
  for (int i = 0; i < n; i++) {
    const char *m = MUSTER[werte[i]];
    for (int j = 0; m[j]; j++) { if (k >= max) return 0; breiten[k++] = m[j] - '0'; }
  }
  return k;
}
