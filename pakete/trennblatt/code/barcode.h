/*
 * Code-128-Leser für Graustufenbilder (8 Bit), ohne Abhängigkeiten.
 *
 * Gedacht für gescannte Seiten: Das Bild wird zeilen- und spaltenweise abgetastet (je drei benachbarte
 * Zeilen gemittelt), jede Abtastlinie mit einer örtlichen Schwelle in Striche und Lücken zerlegt (Kanten
 * auf Bruchteile eines Bildpunkts genau) und in beide Richtungen nach Code 128 (Zeichensätze A, B, C)
 * gelesen. Leicht schiefe Scans gehen, solange eine Abtastlinie alle Striche kreuzt; die Prüfziffer
 * verhindert Fehllesungen.
 */
#ifndef TRENNBLATT_BARCODE_H
#define TRENNBLATT_BARCODE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define BC_TEXT_MAX 96
#define BC_FUNDE_MAX 16

typedef struct {
  char text[BC_TEXT_MAX]; /* gelesener Inhalt (druckbares ASCII) */
  int treffer;            /* auf wie vielen Abtastlinien gelesen */
} bc_fund;

/*
 * Sucht Code-128-Barcodes im Bild. bild: Bildpunkte zeilenweise, 0 = schwarz, 255 = weiß;
 * zeilenlaenge: Abstand zweier Zeilen in Bytes; schritt: Abstand der Abtastlinien in Bildpunkten (≥ 1).
 * Gibt die Zahl verschiedener Funde zurück (höchstens max).
 */
int bc_suche(const uint8_t *bild, int breite, int hoehe, int zeilenlaenge, int schritt, bc_fund *funde, int max);

/* Liest eine Abtastlinie (Helligkeiten) in beide Richtungen; ergänzt funde, gibt die neue Anzahl zurück. */
int bc_linie(const float *werte, int n, bc_fund *funde, int anzahl, int max);

/* Anteil dunkler Bildpunkte im Inneren der Seite (ohne 5 % Rand) – für „leere Rückseite“. */
double bc_dunkelanteil(const uint8_t *bild, int breite, int hoehe, int zeilenlaenge);

/* Code 128 B als Folge von Strich- und Lückenbreiten in Modulen (für Tests); gibt die Anzahl zurück. */
int bc_code128b(const char *text, int *breiten, int max);

#ifdef __cplusplus
}
#endif

#endif
