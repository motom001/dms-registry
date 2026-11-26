// Test auf dem Rechner: Modul ohne WebAssembly, Daten aus einem Ordner. Liest Texte (eine Zeile JSON-String je Text)
// von stdin und schreibt je Text eine Zeile: Wortteil-Nummern und Vektor als JSON.
//   clang++ -O2 -DABLAGO_NATIV -I../code ../code/e5.cpp nativ.cpp -o /tmp/e5nativ && /tmp/e5nativ <daten> < texte.jsonl
#include <chrono>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include "json.h"

std::vector<uint32_t> test_tokens(const std::string &t);
std::vector<float> test_vektor(const std::string &t);
static std::string ordner, antwort;
extern "C" int32_t dms_api(const char *, int32_t) { antwort.clear(); return 500; }
extern "C" int32_t dms_datei(const char *p, int32_t n) {
  std::ifstream f(ordner + "/" + std::string(p, (size_t)n), std::ios::binary);
  if (!f) return -1;
  std::stringstream s; s << f.rdbuf(); antwort = s.str(); return (int32_t)antwort.size();
}
extern "C" int32_t dms_antwort_laenge() { return (int32_t)antwort.size(); }
extern "C" int32_t dms_antwort_lesen(char *z, int32_t n) { size_t k = std::min((size_t)n, antwort.size()); memcpy(z, antwort.data(), k); return (int32_t)k; }
extern "C" int32_t dms_ergebnis(const char *t, int32_t n) { fprintf(stderr, "ergebnis: %.*s\n", n, t); return 0; }
extern "C" int32_t dms_log(int32_t, const char *t, int32_t n) { fprintf(stderr, "log: %.*s\n", n, t); return 0; }

int main(int argc, char **argv) {
  ordner = argc > 1 ? argv[1] : "daten";
  bool nurTokens = argc > 2 && std::string(argv[2]) == "tokens";
  std::string zeile;
  double ms = 0; int n = 0;
  while (std::getline(std::cin, zeile)) {
    Json j = JsonLeser::lies(zeile.data(), zeile.size());
    std::string t = j.text();
    auto ids = test_tokens(t);
    printf("{\"ids\":[");
    for (size_t i = 0; i < ids.size(); i++) printf(i ? ",%u" : "%u", ids[i]);
    printf("]");
    if (!nurTokens) {
      auto a = std::chrono::steady_clock::now();
      auto v = test_vektor(t);
      ms += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - a).count(); n++;
      printf(",\"vektor\":[");
      for (size_t i = 0; i < v.size(); i++) printf(i ? ",%.6g" : "%.6g", v[i]);
      printf("]");
    }
    printf("}\n");
  }
  if (n) fprintf(stderr, "%.1f ms je Text (%d Texte)\n", ms / n, n);
}
