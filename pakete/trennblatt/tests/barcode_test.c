/*
 * Test des Code-128-Lesers (code/barcode.c), nativ übersetzt – läuft beim Bau (code/bauen.sh) und in tests/pruefen.sh.
 *
 *   cc -O2 -I code tests/barcode_test.c code/barcode.c -lm -o barcode_test
 *   ./barcode_test                 # künstliche Scans: schief, verrauscht, unscharf, gedreht, kleine Module
 *   ./barcode_test seite.pgm …     # gefundene Barcodes je Bild ausgeben (PGM P5, wie das DMS sie liefert)
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "barcode.h"

static unsigned zufall = 12345;
static double gleich(void) { zufall = zufall * 1103515245u + 12345u; return ((zufall >> 8) & 0xffffff) / (double)0x1000000; }
static double normal(void) { double a = gleich() + 1e-9, b = gleich(); return sqrt(-2 * log(a)) * cos(6.283185307 * b); }

typedef struct { int breite, hoehe; unsigned char *p; } Bild;

/* Barcode mittig ins Bild: modul in Bildpunkten, winkel in Grad, hoehe des Barcodes in Bildpunkten,
   tinte = Striche um so viele Module breiter (verlaufende Tinte), rauschen = Standardabweichung, unscharf = 3×3-Mittel. */
static Bild male(const char *text, double modul, double winkel, double hoehe, double tinte, double rauschen, int unscharf, int breite, int bhoehe) {
  int b[1200];
  int n = bc_code128b(text, b, 1200);
  double gesamt = 0;
  for (int i = 0; i < n; i++) gesamt += b[i];
  Bild bild = { breite, bhoehe, malloc((size_t)breite * (size_t)bhoehe) };
  double c = cos(winkel * M_PI / 180), s = sin(winkel * M_PI / 180);
  for (int y = 0; y < bhoehe; y++)
    for (int x = 0; x < breite; x++) {
      int schwarz = 0;
      for (int sy = 0; sy < 4; sy++)
        for (int sx = 0; sx < 4; sx++) {
          double px = x + (sx + 0.5) / 4 - breite / 2.0, py = y + (sy + 0.5) / 4 - bhoehe / 2.0;
          double u = (c * px + s * py) / modul + gesamt / 2, v = -s * px + c * py;
          if (fabs(v) > hoehe / 2 || u < -tinte || u > gesamt + tinte) continue;
          double pos = 0;
          for (int i = 0; i < n; i++) {
            if (i % 2 == 0 && u >= pos - tinte / 2 && u < pos + b[i] + tinte / 2) { schwarz++; break; }
            pos += b[i];
            if (pos - tinte > u) break;
          }
        }
      bild.p[(size_t)y * breite + x] = (unsigned char)(235 - schwarz * 215 / 16);
    }
  if (unscharf) {
    unsigned char *q = malloc((size_t)breite * (size_t)bhoehe);
    for (int y = 0; y < bhoehe; y++)
      for (int x = 0; x < breite; x++) {
        int sum = 0, k = 0;
        for (int dy = -1; dy <= 1; dy++)
          for (int dx = -1; dx <= 1; dx++) {
            int xx = x + dx, yy = y + dy;
            if (xx < 0 || yy < 0 || xx >= breite || yy >= bhoehe) continue;
            sum += bild.p[(size_t)yy * breite + xx]; k++;
          }
        q[(size_t)y * breite + x] = (unsigned char)(sum / k);
      }
    free(bild.p);
    bild.p = q;
  }
  for (size_t i = 0; i < (size_t)breite * bhoehe; i++) {
    double w = bild.p[i] + rauschen * normal();
    if (rauschen > 0 && gleich() < 0.003) w = gleich() < 0.5 ? 0 : 255; /* Staub */
    bild.p[i] = (unsigned char)(w < 0 ? 0 : w > 255 ? 255 : w);
  }
  return bild;
}

static int fehler = 0;

static void pruefe(const char *name, const char *text, double modul, double winkel, double hoehe, double tinte, double rauschen, int unscharf) {
  int breite = 1400, bhoehe = 900;
  Bild b = male(text, modul, winkel, hoehe, tinte, rauschen, unscharf, breite, bhoehe);
  bc_fund f[BC_FUNDE_MAX];
  int n = bc_suche(b.p, breite, bhoehe, breite, 5, f, BC_FUNDE_MAX);
  int gefunden = 0;
  for (int i = 0; i < n; i++) {
    if (!strcmp(f[i].text, text)) gefunden = f[i].treffer;
    else { printf("✗ %s: falsch gelesen „%s“\n", name, f[i].text); fehler++; }
  }
  if (!gefunden) { printf("✗ %s: „%s“ nicht gefunden\n", name, text); fehler++; }
  else printf("✓ %s: %d Linien\n", name, gefunden);
  free(b.p);
}

static void leer(const char *name, double rauschen) {
  int breite = 1200, bhoehe = 800;
  Bild b = { breite, bhoehe, malloc((size_t)breite * bhoehe) };
  /* „Text“: zufällige dunkle Kästchen in Zeilen, dazu Rauschen */
  for (int i = 0; i < breite * bhoehe; i++) b.p[i] = 235;
  for (int zeile = 60; zeile < bhoehe - 60; zeile += 36)
    for (int x = 80; x < breite - 80;) {
      int w = 3 + (int)(gleich() * 14), h = 14 + (int)(gleich() * 8);
      if (gleich() < 0.8)
        for (int y = zeile; y < zeile + h; y++)
          for (int xx = x; xx < x + w && xx < breite; xx++) b.p[(size_t)y * breite + xx] = 30;
      x += w + 2 + (int)(gleich() * 6);
    }
  for (int i = 0; i < breite * bhoehe; i++) { double w = b.p[i] + rauschen * normal(); b.p[i] = (unsigned char)(w < 0 ? 0 : w > 255 ? 255 : w); }
  bc_fund f[BC_FUNDE_MAX];
  int n = bc_suche(b.p, breite, bhoehe, breite, 3, f, BC_FUNDE_MAX);
  if (n) { printf("✗ %s: Barcode „%s“ in einer Seite ohne Barcode\n", name, f[0].text); fehler++; }
  else printf("✓ %s: kein Barcode\n", name);
  double anteil = bc_dunkelanteil(b.p, breite, bhoehe, breite);
  if (anteil < 0.05) { printf("✗ %s: Textseite gilt als leer (%.4f)\n", name, anteil); fehler++; }
  free(b.p);
}

static int ganzzahl(FILE *f) {
  int c, n = 0;
  while ((c = fgetc(f)) != EOF) {
    if (c == '#') { while ((c = fgetc(f)) != EOF && c != '\n') {} continue; }
    if (c >= '0' && c <= '9') break;
  }
  for (; c >= '0' && c <= '9'; c = fgetc(f)) n = n * 10 + (c - '0');
  return n;
}

static int datei(const char *pfad) {
  FILE *f = fopen(pfad, "rb");
  if (!f || fgetc(f) != 'P' || fgetc(f) != '5') { fprintf(stderr, "%s: kein PGM (P5)\n", pfad); return 1; }
  int breite = ganzzahl(f), hoehe = ganzzahl(f), max = ganzzahl(f);
  if (breite <= 0 || hoehe <= 0 || max != 255) { fprintf(stderr, "%s: nur 8 Bit\n", pfad); return 1; }
  unsigned char *p = malloc((size_t)breite * hoehe);
  if (fread(p, 1, (size_t)breite * hoehe, f) != (size_t)breite * hoehe) { fprintf(stderr, "%s: zu kurz\n", pfad); return 1; }
  fclose(f);
  bc_fund fu[BC_FUNDE_MAX];
  int n = bc_suche(p, breite, hoehe, breite, 5, fu, BC_FUNDE_MAX);
  printf("%s\t%.4f", pfad, bc_dunkelanteil(p, breite, hoehe, breite));
  for (int i = 0; i < n; i++) printf("\t%s", fu[i].text);
  printf("\n");
  free(p);
  return 0;
}

int main(int argc, char **argv) {
  if (argc > 1) {
    int r = 0;
    for (int i = 1; i < argc; i++) r |= datei(argv[i]);
    return r;
  }
  pruefe("sauber", "DMS-TRENNEN", 4, 0, 200, 0, 0, 0);
  pruefe("schief 3°", "DMS-TRENNEN", 4, 3, 200, 0, 8, 0);
  pruefe("schief -7°", "DMS-TRENNEN", 3, -7, 220, 0, 8, 1);
  pruefe("verrauscht", "DMS-TRENNEN", 3, 1.5, 200, 0, 30, 0);
  pruefe("verlaufene Tinte", "DMS-TRENNEN", 2.5, 2, 160, 0.35, 15, 0);
  pruefe("unscharf", "DMS-TRENNEN", 2.5, 2, 160, 0, 15, 1);
  pruefe("unscharf und Tinte", "DMS-TRENNEN", 3.5, 2, 160, 0.35, 15, 1);
  pruefe("auf dem Kopf", "DMS-TRENNEN", 3, 181, 200, 0, 10, 0);
  pruefe("quer", "DMS-TRENNEN", 3, 90.5, 200, 0, 10, 0);
  pruefe("Archivnummer 300 dpi (0,19 mm)", "DMS-ASN:A-000123", 2.25, 1, 130, 0, 10, 0);
  pruefe("Archivnummer kleinster Aufkleber (0,15 mm)", "DMS-ASN:A-000123", 1.75, 0.5, 130, 0, 6, 0);
  pruefe("Archivnummer schief", "DMS-ASN:2026-0042", 2.5, -4, 140, 0.2, 12, 1);
  pruefe("Kleinbuchstaben", "Hallo Welt 42", 3, 0, 150, 0, 5, 0);
  leer("Textseite", 10);
  leer("Textseite verrauscht", 35);
  if (fehler) { printf("%d Fehler\n", fehler); return 1; }
  printf("Alles gut.\n");
  return 0;
}
