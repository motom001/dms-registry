/* Zusatzpaket für die Texterkennung: Das Modul selbst tut nichts. Es gibt nur seine Sprachdaten (code/daten/)
 * frei – das Paket Texterkennung liest sie als „texterkennung.tur/tur.traineddata“ (DMS ab 0.133.0). */
#include <stdint.h>
#include <stdlib.h>

static char *eingang;

__attribute__((export_name("dms_puffer"))) char *dms_puffer(int32_t n) {
  free(eingang);
  eingang = malloc((size_t)n + 1);
  return eingang;
}

__attribute__((export_name("dms_ereignis"))) int32_t dms_ereignis(char *json, int32_t n) {
  (void)json; (void)n;
  return 0;
}
