// ZIP lesen (Office Open XML und OpenDocument sind ZIP-Archive): Inhaltsverzeichnis, Einträge „gespeichert“ oder
// „Deflate“ (zlib). Mit Grenzen gegen ZIP-Bomben: Größe je Eintrag, Verhältnis gepackt/entpackt, Zahl der Einträge.
// Verschlüsselte Einträge und ZIP64 liest es nicht.
#pragma once
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>

#include <zlib.h>

namespace zip {

struct Eintrag {
  std::string name;
  uint32_t lokal = 0;       // Lage des lokalen Kopfs
  uint32_t gepackt = 0, entpackt = 0;
  uint16_t methode = 0, flags = 0;
};

constexpr size_t EINTRAEGE_MAX = 20000;
constexpr uint32_t EINTRAG_MAX = 96u * 1024u * 1024u;  // entpackt je Eintrag
constexpr uint32_t VERHAELTNIS_MAX = 1000;             // entpackt höchstens 1000-mal so groß wie gepackt

inline uint16_t le16(const uint8_t *p) { return (uint16_t)(p[0] | p[1] << 8); }
inline uint32_t le32(const uint8_t *p) { return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24; }

class Archiv {
  const uint8_t *d = nullptr;
  size_t n = 0;
 public:
  std::vector<Eintrag> eintraege;
  std::string fehler;

  bool oeffne(const uint8_t *daten, size_t laenge) {
    d = daten; n = laenge;
    if (n < 22) { fehler = "zu kurz für ein ZIP-Archiv"; return false; }
    // Ende des Inhaltsverzeichnisses: höchstens 64 KB Kommentar am Schluss.
    size_t e = n - 22, grenze = n > 22 + 65535 ? n - 22 - 65535 : 0;
    for (;; e--) {
      if (le32(d + e) == 0x06054b50) break;
      if (e == grenze) { fehler = "Inhaltsverzeichnis des ZIP-Archivs fehlt"; return false; }
    }
    const uint16_t anzahl = le16(d + e + 10);
    const uint32_t groesse = le32(d + e + 12), start = le32(d + e + 16);
    if (anzahl == 0xffff || start == 0xffffffff) { fehler = "ZIP64-Archive liest das Paket nicht"; return false; }
    if ((size_t)start + groesse > n) { fehler = "Inhaltsverzeichnis des ZIP-Archivs beschädigt"; return false; }
    size_t p = start;
    for (size_t i = 0; i < anzahl && i < EINTRAEGE_MAX; i++) {
      if (p + 46 > n || le32(d + p) != 0x02014b50) { fehler = "Eintrag im ZIP-Archiv beschädigt"; return false; }
      Eintrag z;
      z.flags = le16(d + p + 8);
      z.methode = le16(d + p + 10);
      z.gepackt = le32(d + p + 20);
      z.entpackt = le32(d + p + 24);
      const uint16_t ln = le16(d + p + 28), lx = le16(d + p + 30), lk = le16(d + p + 32);
      z.lokal = le32(d + p + 42);
      if (p + 46 + ln > n) { fehler = "Eintrag im ZIP-Archiv beschädigt"; return false; }
      z.name.assign((const char *)d + p + 46, ln);
      eintraege.push_back(z);
      p += 46 + (size_t)ln + lx + lk;
    }
    return true;
  }

  const Eintrag *finde(const std::string &name) const {
    for (auto &e : eintraege) if (e.name == name) return &e;
    return nullptr;
  }

  bool verschluesselt() const {
    for (auto &e : eintraege) if (e.flags & 1) return true;
    return false;
  }

  // Inhalt eines Eintrags; false mit `fehler`, wenn er sich nicht lesen lässt.
  bool lies(const Eintrag &z, std::string &aus) {
    aus.clear();
    if (z.flags & 1) { fehler = "Eintrag ist verschlüsselt"; return false; }
    if (z.entpackt > EINTRAG_MAX) { fehler = z.name + " ist zu groß (" + std::to_string(z.entpackt / 1048576) + " MB)"; return false; }
    if (z.gepackt && z.entpackt / z.gepackt > VERHAELTNIS_MAX) { fehler = z.name + ": verdächtig stark gepackt"; return false; }
    if ((size_t)z.lokal + 30 > n || le32(d + z.lokal) != 0x04034b50) { fehler = z.name + ": lokaler Kopf beschädigt"; return false; }
    const size_t daten = (size_t)z.lokal + 30 + le16(d + z.lokal + 26) + le16(d + z.lokal + 28);
    if (daten + z.gepackt > n) { fehler = z.name + ": abgeschnitten"; return false; }
    if (z.methode == 0) {
      if (z.gepackt != z.entpackt) { fehler = z.name + ": Größen passen nicht"; return false; }
      aus.assign((const char *)d + daten, z.gepackt);
      return true;
    }
    if (z.methode != 8) { fehler = z.name + ": Packverfahren " + std::to_string(z.methode) + " unbekannt"; return false; }
    // Die angegebene Größe kann lügen: höchstens so viel entpacken, wie angegeben ist (und nie mehr als die Grenze).
    aus.resize(z.entpackt);
    z_stream s;
    memset(&s, 0, sizeof s);
    if (inflateInit2(&s, -MAX_WBITS) != Z_OK) { fehler = "zlib"; return false; }
    s.next_in = const_cast<Bytef *>(d + daten);
    s.avail_in = z.gepackt;
    s.next_out = (Bytef *)aus.data();
    s.avail_out = (uInt)aus.size();
    int r = inflate(&s, Z_FINISH);
    const size_t geschrieben = aus.size() - s.avail_out;
    inflateEnd(&s);
    if (r != Z_STREAM_END) {
      fehler = z.name + ": " + (r == Z_BUF_ERROR || r == Z_OK ? "größer als angegeben" : "Daten beschädigt");
      aus.clear();
      return false;
    }
    aus.resize(geschrieben);
    return true;
  }

  bool lies(const std::string &name, std::string &aus) {
    const Eintrag *e = finde(name);
    if (!e) { fehler = name + " fehlt"; return false; }
    return lies(*e, aus);
  }
};

}  // namespace zip
