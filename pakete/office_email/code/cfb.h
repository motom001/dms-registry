// Compound File Binary (OLE2) lesen – das Containerformat von Outlook-Nachrichten (.msg), alten Office-Dateien
// (.doc, .xls, .ppt) und verschlüsselten Office-Dateien. Nur Verzeichnis und Datenströme; nichts wird ausgeführt.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include "zeichen.h"

namespace cfb {

inline bool erkannt(const uint8_t *d, size_t n) {
  static const uint8_t k[8] = {0xd0, 0xcf, 0x11, 0xe0, 0xa1, 0xb1, 0x1a, 0xe1};
  return n >= 512 && !memcmp(d, k, 8);
}

struct Eintrag {
  std::string name;
  uint8_t typ = 0;  // 1 Speicher (Ordner), 2 Datenstrom, 5 Wurzel
  uint32_t links = 0xffffffff, rechts = 0xffffffff, kind = 0xffffffff, start = 0;
  uint64_t groesse = 0;
};

constexpr uint32_t ENDE = 0xfffffffe, FREI = 0xffffffff;
constexpr uint64_t STROM_MAX = 64u * 1024u * 1024u;

class Datei {
  const uint8_t *d = nullptr;
  size_t n = 0;
  uint32_t sektor = 512, miniSektor = 64, miniGrenze = 4096;
  std::vector<uint32_t> fat, miniFat;
  std::string miniStrom;

  static uint32_t le32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }
  const uint8_t *sektorDaten(uint32_t s) const {
    const uint64_t o = (uint64_t)(s + 1) * sektor;
    return o + sektor <= n ? d + o : nullptr;
  }
  // Kette in der FAT: Sektoren anhängen, bis ENDE (mit Schutz gegen Schleifen).
  bool kette(uint32_t s, uint64_t max, std::string &aus) const {
    aus.clear();
    for (size_t schritte = 0; s != ENDE; schritte++) {
      if (s >= fat.size() || schritte > fat.size()) return false;
      const uint8_t *p = sektorDaten(s);
      if (!p) return false;
      aus.append((const char *)p, sektor);
      if (aus.size() >= max) break;
      s = fat[s];
    }
    if (aus.size() > max) aus.resize(max);
    return true;
  }

 public:
  std::vector<Eintrag> eintraege;
  std::string fehler;

  bool oeffne(const uint8_t *daten, size_t laenge) {
    d = daten; n = laenge;
    if (!erkannt(d, n)) { fehler = "kein Compound File"; return false; }
    const uint16_t shift = (uint16_t)(d[30] | d[31] << 8), mshift = (uint16_t)(d[32] | d[33] << 8);
    if ((shift != 9 && shift != 12) || mshift != 6) { fehler = "Compound File: unbekannte Sektorgröße"; return false; }
    sektor = 1u << shift; miniSektor = 1u << mshift;
    miniGrenze = le32(d + 56);
    const uint32_t fatSektoren = le32(d + 44), verzeichnis = le32(d + 48), miniFatStart = le32(d + 60), miniFatAnzahl = le32(d + 64);
    uint32_t difat = le32(d + 68), difatAnzahl = le32(d + 72);
    // DIFAT: 109 Einträge im Kopf, danach Ketten von DIFAT-Sektoren.
    std::vector<uint32_t> fatListe;
    for (int i = 0; i < 109; i++) { uint32_t s = le32(d + 76 + 4 * i); if (s != FREI) fatListe.push_back(s); }
    for (uint32_t i = 0; i < difatAnzahl && difat != ENDE && difat != FREI; i++) {
      const uint8_t *p = sektorDaten(difat);
      if (!p) { fehler = "Compound File beschädigt (DIFAT)"; return false; }
      for (uint32_t k = 0; k + 1 < sektor / 4; k++) { uint32_t s = le32(p + 4 * k); if (s != FREI) fatListe.push_back(s); }
      difat = le32(p + sektor - 4);
    }
    if (fatListe.size() < fatSektoren || fatListe.size() > n / sektor + 1) { fehler = "Compound File beschädigt (FAT)"; return false; }
    for (uint32_t s : fatListe) {
      const uint8_t *p = sektorDaten(s);
      if (!p) { fehler = "Compound File beschädigt (FAT)"; return false; }
      for (uint32_t k = 0; k < sektor / 4; k++) fat.push_back(le32(p + 4 * k));
    }
    std::string v;
    if (!kette(verzeichnis, STROM_MAX, v)) { fehler = "Compound File beschädigt (Verzeichnis)"; return false; }
    for (size_t o = 0; o + 128 <= v.size(); o += 128) {
      const uint8_t *p = (const uint8_t *)v.data() + o;
      Eintrag e;
      const uint16_t l = (uint16_t)(p[64] | p[65] << 8);
      e.name = zeichen::utf16le(p, l >= 2 && l <= 64 ? l - 2 : 0);
      e.typ = p[66];
      e.links = le32(p + 68); e.rechts = le32(p + 72); e.kind = le32(p + 76);
      e.start = le32(p + 116);
      e.groesse = (uint64_t)le32(p + 120) | (sektor == 512 ? 0 : (uint64_t)le32(p + 124) << 32);
      eintraege.push_back(e);
    }
    if (eintraege.empty() || eintraege[0].typ != 5) { fehler = "Compound File ohne Wurzel"; return false; }
    if (miniFatAnzahl && miniFatStart != ENDE) {
      std::string m;
      if (!kette(miniFatStart, (uint64_t)miniFatAnzahl * sektor, m)) { fehler = "Compound File beschädigt (MiniFAT)"; return false; }
      for (size_t k = 0; k + 4 <= m.size(); k += 4) miniFat.push_back(le32((const uint8_t *)m.data() + k));
      if (!kette(eintraege[0].start, std::min<uint64_t>(eintraege[0].groesse, STROM_MAX), miniStrom)) { fehler = "Compound File beschädigt (Ministrom)"; return false; }
    }
    return true;
  }

  // Kinder eines Speichers (Ordners) – der Baum steht als Rot-Schwarz-Baum über links/rechts.
  std::vector<uint32_t> kinder(uint32_t ordner) const {
    std::vector<uint32_t> r, stapel;
    if (ordner >= eintraege.size()) return r;
    stapel.push_back(eintraege[ordner].kind);
    while (!stapel.empty() && r.size() <= eintraege.size()) {
      uint32_t i = stapel.back();
      stapel.pop_back();
      if (i >= eintraege.size()) continue;
      r.push_back(i);
      stapel.push_back(eintraege[i].links);
      stapel.push_back(eintraege[i].rechts);
    }
    return r;
  }

  int32_t finde(uint32_t ordner, const std::string &name) const {
    for (uint32_t i : kinder(ordner)) if (zeichen::klein(eintraege[i].name) == zeichen::klein(name)) return (int32_t)i;
    return -1;
  }

  bool strom(uint32_t i, std::string &aus) const {
    aus.clear();
    if (i >= eintraege.size() || eintraege[i].typ != 2) return false;
    const Eintrag &e = eintraege[i];
    if (e.groesse > STROM_MAX) return false;
    if (e.groesse < miniGrenze) {
      uint32_t s = e.start;
      for (size_t schritte = 0; s != ENDE && aus.size() < e.groesse; schritte++) {
        if (s >= miniFat.size() || schritte > miniFat.size()) return false;
        const uint64_t o = (uint64_t)s * miniSektor;
        if (o + miniSektor > miniStrom.size()) return false;
        aus.append(miniStrom, (size_t)o, miniSektor);
        s = miniFat[s];
      }
      if (aus.size() < e.groesse) return false;
      aus.resize((size_t)e.groesse);
      return true;
    }
    if (!kette(e.start, e.groesse, aus) || aus.size() < e.groesse) return false;
    return true;
  }
};

}  // namespace cfb
