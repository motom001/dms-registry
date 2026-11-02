/* WASI ohne Ausnahmen kennt kein setjmp/longjmp. libtiff nutzt es nur, um nach einem Fehler in libjpeg
 * zurückzuspringen (tif_jpeg.c). Hier: setjmp kehrt einmal mit 0 zurück, longjmp beendet den Aufruf (Trap).
 * Ein kaputtes JPEG in einem TIFF bricht so den Aufruf ab; der Paket-Läufer meldet es als Fehler. */
#ifndef BILDFORMATE_SETJMP_H
#define BILDFORMATE_SETJMP_H
#include <stdlib.h>
typedef int jmp_buf[1];
#define setjmp(b) ((void)(b), 0)
static inline __attribute__((noreturn)) void longjmp(jmp_buf b, int v) { (void)b; (void)v; abort(); }
#endif
