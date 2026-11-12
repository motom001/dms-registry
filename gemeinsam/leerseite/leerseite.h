/*
 * Leere Seite erkennen (dms #997) – gemeinsam für die Pakete „Leerseiten“ und „Trennblatt“, ohne Bibliotheken.
 * Eingabe ist ein Graustufenbild (8 Bit, 0 = schwarz, 255 = weiß), wie es Ablago als PGM liefert.
 *
 * Ablauf:
 *  1. Auf etwa 100 dpi verkleinern (Mittelwert je Block) – das glättet Rauschen und hält den Aufwand klein.
 *  2. Papierton schätzen: der helle Wert, den die meisten Bildpunkte im Inneren haben (75. Perzentil).
 *  3. „Tinte“ ist, was deutlich dunkler ist als das Papier. Wie deutlich, hängt von der Stufe ab: „vorsichtig“ zählt
 *     schon durchscheinende Schrift von der Rückseite, „normal“ und „streng“ erst kräftigere Striche.
 *  4. Zusammenhängende Flecken suchen und weglassen, was kein Inhalt ist: Staub (sehr kleine Flecken), Lochung (runde
 *     Flecken von 4–9 mm nahe am Rand) und Schatten am Rand (Flecken, die den Bildrand berühren und schmal am Rand
 *     liegen). Einen schmalen Streifen am Bildrand schaut die Erkennung gar nicht an.
 *  5. Leer ist die Seite, wenn der Rest klein bleibt: Fläche, größter Fleck und Zahl der Flecken unter den Grenzen der
 *     Stufe. Im Zweifel ist eine Seite nicht leer.
 *
 * Nur Kopf-Datei (static), damit jedes Paket sie ohne eigene Übersetzungseinheit einbindet (`-I gemeinsam/leerseite`).
 * Lizenz: Apache-2.0 wie das Repository.
 */
#ifndef LEERSEITE_H
#define LEERSEITE_H

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Empfindlichkeit: vorsichtig (Vorgabe) markiert nur, was wirklich leer ist; streng auch fast leere Seiten. */
typedef enum { LS_VORSICHTIG = 0, LS_NORMAL = 1, LS_STRENG = 2 } ls_stufe;

/* Was die Erkennung gefunden hat (für Protokoll und Tests). */
typedef struct {
  double tinte_mm2;   /* Fläche der Flecken, die als Inhalt zählen */
  double groesste_mm; /* längste Seite des größten Flecks */
  int flecken;        /* Zahl der Flecken, die als Inhalt zählen */
  int loecher;        /* erkannte Lochung */
  int rand;           /* Schatten und Ränder, die nicht zählen */
  int staub;          /* sehr kleine Flecken, die nicht zählen */
  int papier;         /* geschätzter Papierton 0..255 */
} ls_befund;

typedef struct { int kontrast; double staub_mm2; double flaeche_mm2; double fleck_mm; int flecken; } ls_grenzen;

static const ls_grenzen LS_GRENZEN[3] = {
  /* vorsichtig: schon schwache Spuren zählen (durchscheinende Schrift, Bleistift) */
  { 18, 0.15, 0.8, 2.0, 3 },
  /* normal: durchscheinende Schrift und Rauschen zählen nicht */
  { 45, 0.4, 4.0, 5.0, 10 },
  /* streng: auch einzelne Striche und kleine Flecken zählen nicht */
  { 45, 1.5, 40.0, 20.0, 40 },
};

/* Stufe aus dem Text der Einstellung (vorsichtig, normal, streng); Unbekanntes ist vorsichtig. */
static inline ls_stufe ls_stufe_von(const char *s) {
  if (s && !strcmp(s, "normal")) return LS_NORMAL;
  if (s && !strcmp(s, "streng")) return LS_STRENG;
  return LS_VORSICHTIG;
}

/*
 * Ist die Seite leer? 1 = leer, 0 = Inhalt, -1 = kein Speicher oder ungültiges Bild.
 * px: Bildpunkte (Zeilen mit Abstand stride), w × h, dpi: Auflösung des Bilds (0 = unbekannt, dann wie A4 geschätzt).
 */
static inline int ls_pruefe(const uint8_t *px, int w, int h, int stride, int dpi, ls_stufe stufe, ls_befund *b) {
  ls_befund leer_b;
  if (!b) b = &leer_b;
  memset(b, 0, sizeof *b);
  if (!px || w < 8 || h < 8 || stride < w) return -1;
  if ((int)stufe < 0 || (int)stufe > 2) stufe = LS_VORSICHTIG;
  const ls_grenzen g = LS_GRENZEN[stufe];
  /* Unbekannte Auflösung (z. B. ein Foto): so tun, als sei die lange Seite 297 mm. */
  if (dpi <= 0) dpi = (int)((w > h ? w : h) / 11.69 + 0.5);
  if (dpi < 20) dpi = 20;
  int f = (dpi + 50) / 100;
  if (f < 1) f = 1;
  const int bw = w / f, bh = h / f;
  if (bw < 8 || bh < 8) return -1;
  const double mm = 25.4 * f / dpi;  /* Kantenlänge eines Bildpunkts nach dem Verkleinern */
  const double mm2 = mm * mm;

  uint8_t *klein = (uint8_t *)malloc((size_t)bw * bh);
  if (!klein) return -1;
  for (int y = 0; y < bh; y++)
    for (int x = 0; x < bw; x++) {
      unsigned s = 0;
      for (int dy = 0; dy < f; dy++) {
        const uint8_t *z = px + (size_t)(y * f + dy) * stride + (size_t)x * f;
        for (int dx = 0; dx < f; dx++) s += z[dx];
      }
      klein[(size_t)y * bw + x] = (uint8_t)(s / (unsigned)(f * f));
    }

  /* Streifen am Bildrand, den die Erkennung nicht ansieht: 1,5 % je Seite (mindestens 1 Bildpunkt). */
  const int rx = bw * 15 / 1000 + 1, ry = bh * 15 / 1000 + 1;
  unsigned hist[256] = { 0 };
  for (int y = ry; y < bh - ry; y++)
    for (int x = rx; x < bw - rx; x++) hist[klein[(size_t)y * bw + x]]++;
  unsigned gesamt = 0;
  for (int i = 0; i < 256; i++) gesamt += hist[i];
  /* Papierton: 75. Perzentil von dunkel nach hell – auch bei viel Inhalt ist das noch Papier. */
  unsigned bis = gesamt / 4, n = 0;
  int papier = 255;
  for (int i = 255; i >= 0; i--) { n += hist[i]; if (n >= bis) { papier = i; break; } }
  b->papier = papier;
  const int schwelle = papier - g.kontrast;

  /* Tinte markieren: 1 = Tinte, 2 = schon besucht. */
  uint8_t *maske = (uint8_t *)calloc((size_t)bw * bh, 1);
  int32_t *stapel = (int32_t *)malloc(sizeof(int32_t) * (size_t)bw * bh);
  if (!maske || !stapel) { free(klein); free(maske); free(stapel); return -1; }
  for (int y = ry; y < bh - ry; y++)
    for (int x = rx; x < bw - rx; x++)
      if (klein[(size_t)y * bw + x] < schwelle) maske[(size_t)y * bw + x] = 1;

  const double band_loch = 30.0 / mm;  /* Lochung: Mitte höchstens 30 mm vom Rand */
  const int band_x = bw * 6 / 100 + 1, band_y = bh * 6 / 100 + 1;  /* Schatten: schmal am Rand */
  for (int y0 = ry; y0 < bh - ry; y0++)
    for (int x0 = rx; x0 < bw - rx; x0++) {
      if (maske[(size_t)y0 * bw + x0] != 1) continue;
      /* Fleck füllen (8 Nachbarn), Fläche und Rahmen merken. */
      int oben = 0, minx = x0, maxx = x0, miny = y0, maxy = y0;
      long flaeche = 0;
      stapel[oben++] = y0 * bw + x0;
      maske[(size_t)y0 * bw + x0] = 2;
      while (oben) {
        const int p = stapel[--oben], x = p % bw, y = p / bw;
        flaeche++;
        if (x < minx) minx = x;
        if (x > maxx) maxx = x;
        if (y < miny) miny = y;
        if (y > maxy) maxy = y;
        for (int dy = -1; dy <= 1; dy++)
          for (int dx = -1; dx <= 1; dx++) {
            const int nx = x + dx, ny = y + dy;
            if (nx < rx || ny < ry || nx >= bw - rx || ny >= bh - ry) continue;
            uint8_t *m = &maske[(size_t)ny * bw + nx];
            if (*m == 1) { *m = 2; stapel[oben++] = ny * bw + nx; }
          }
      }
      const double a = flaeche * mm2;
      const int fw = maxx - minx + 1, fh = maxy - miny + 1;
      const double wmm = fw * mm, hmm = fh * mm;
      if (a < g.staub_mm2) { b->staub++; continue; }
      /* Schatten am Rand: berührt den angesehenen Bereich am Rand und bleibt dort schmal. */
      const int amrand_x = minx <= rx || maxx >= bw - rx - 1, amrand_y = miny <= ry || maxy >= bh - ry - 1;
      if ((amrand_x && fw <= band_x) || (amrand_y && fh <= band_y)) { b->rand++; continue; }
      /* Lochung: rund (Rahmen fast quadratisch, gut gefüllt), 4–9 mm, nahe an einem Rand. */
      const double cx = (minx + maxx) / 2.0, cy = (miny + maxy) / 2.0;
      const int nahe = cx < band_loch || cy < band_loch || bw - cx < band_loch || bh - cy < band_loch;
      const double fuellung = (double)flaeche / ((double)fw * fh);
      if (nahe && wmm >= 3.5 && wmm <= 9.0 && hmm >= 3.5 && hmm <= 9.0 && (wmm > hmm ? wmm - hmm : hmm - wmm) < 2.5 && fuellung > 0.55) { b->loecher++; continue; }
      b->flecken++;
      b->tinte_mm2 += a;
      const double laenge = wmm > hmm ? wmm : hmm;
      if (laenge > b->groesste_mm) b->groesste_mm = laenge;
    }
  free(klein); free(maske); free(stapel);
  return b->tinte_mm2 < g.flaeche_mm2 && b->groesste_mm < g.fleck_mm && b->flecken < g.flecken ? 1 : 0;
}

#endif
