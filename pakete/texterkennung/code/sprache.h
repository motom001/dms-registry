// Sprache eines Texts erkennen – wie im DMS (shared/src/textsprache.ts, #395): häufige Funktionswörter und typische
// Buchstaben je Sprache zählen, offline und ohne fremde Dienste. Dazu die Sprache passend zu einer Schrift (osd).
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <set>
#include <string>
#include <vector>

struct ErkannteSprache { std::string sprache; double konfidenz = 0; };

namespace sprache_intern {

struct Liste { const char *kennung; const char *woerter; const char *zeichen; bool kyrillisch; };

// Bewusst kurz und selbst zusammengestellt (dieselben Listen wie im DMS).
static const Liste LISTEN[] = {
  {"deu", "der die das und ist nicht ein eine einen einem dem den des mit von zu auf für im sie wir ich es bitte ihre ihr sehr sind wird werden auch oder bei nach aus über wie als vom zum zur noch nur haben hat wurde unter diese dieser sich", "äöüß", false},
  {"eng", "the and of to is for on with that this you your are be by from at we our it not have has will please or was were dear any which their there been would should these thank", "", false},
  {"fra", "le la les et des du un une est pour dans que qui sur pas avec vous nous au aux ce cette sont par ne plus votre vos il elle être merci madame monsieur nos leur été avez sera", "éèêàçœùî", false},
  {"spa", "el la los las y de del que en un una es por para con no se su sus al lo como más pero usted muy gracias este esta señor estimado nuestro hemos tiene están", "ñ¿¡áíóú", false},
  {"ita", "il lo la gli le e di del della che è per non un una con sono si al alla ma come anche questo questa nel suo sua grazie gentile nostro dei delle alle sul", "àèìòù", false},
  {"nld", "de het een en van is dat niet op te met voor zijn er aan ook als bij uw wij u door naar maar dit wordt deze geen onze hebben heeft graag", "", false},
  {"tur", "ve bir bu da de ile için çok ne gibi daha olan olarak değil ama sonra kadar her ben biz siz mi mı var yok şu ki veya sayın teşekkür ederiz lütfen", "ığş", false},
  {"pol", "i w z na nie się jest to że do jak ale co od po za tak dla czy jego jej przez są być już tylko oraz pan pani prosimy dziękujemy który która", "ąęłńśźżć", false},
  {"por", "o a os as e de do da dos das que em um uma é para com não por no na se mais como ao seu sua ou foi são obrigado você nossa nosso pelo pela", "ãõçâêô", false},
  {"rus", "и в не на я что с он как это по но из у к за то же от так все она бы мы вы для уважаемый спасибо ваш наш", "ыэъё", true},
  {"ukr", "і в не на я що з він як це по але із у к за те від так все вона б ми ви для шановний дякуємо ваш наш є", "іїєґ", true},
};

// Nächstes UTF-8-Zeichen ab i (Codepunkt), i rückt vor.
inline uint32_t zeichen(const std::string &s, size_t &i) {
  unsigned char c = (unsigned char)s[i++];
  if (c < 0x80) return c;
  int n = c >= 0xf0 ? 3 : c >= 0xe0 ? 2 : c >= 0xc0 ? 1 : 0;
  uint32_t u = c & (0x3f >> n);
  while (n-- > 0 && i < s.size()) u = (u << 6) | ((unsigned char)s[i++] & 0x3f);
  return u;
}
inline bool lateinisch(uint32_t u) { return (u >= 'a' && u <= 'z') || (u >= 'A' && u <= 'Z') || (u >= 0xc0 && u <= 0x24f && u != 0xd7 && u != 0xf7); }
inline bool kyrillisch(uint32_t u) { return u >= 0x400 && u <= 0x4ff; }
inline bool arabisch(uint32_t u) { return u >= 0x600 && u <= 0x6ff; }
// Kleinbuchstaben für ASCII, Latein-1, Kyrillisch (genug für die Funktionswörter).
inline uint32_t klein(uint32_t u) {
  if (u >= 'A' && u <= 'Z') return u + 32;
  if (u >= 0xc0 && u <= 0xde && u != 0xd7) return u + 32;
  if (u >= 0x410 && u <= 0x42f) return u + 32;
  if (u >= 0x400 && u <= 0x40f) return u + 80;
  return u;
}
inline void utf8(std::string &s, uint32_t c) {
  if (c < 0x80) s += (char)c;
  else if (c < 0x800) { s += (char)(0xc0 | c >> 6); s += (char)(0x80 | (c & 0x3f)); }
  else if (c < 0x10000) { s += (char)(0xe0 | c >> 12); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
  else { s += (char)(0xf0 | c >> 18); s += (char)(0x80 | (c >> 12 & 0x3f)); s += (char)(0x80 | (c >> 6 & 0x3f)); s += (char)(0x80 | (c & 0x3f)); }
}

}  // namespace sprache_intern

// Sprache eines Texts; leere Kennung, wenn er zu kurz oder zu uneindeutig ist.
inline ErkannteSprache erkenneSprache(const std::string &roh) {
  using namespace sprache_intern;
  const std::string text = roh.size() > 20000 ? roh.substr(0, 20000) : roh;
  // Wörter in Kleinbuchstaben und die Schrift.
  std::vector<std::string> woerter;
  std::string wort, kleinText;
  bool wortKyr = false;
  int nLat = 0, nKyr = 0, nAra = 0;
  std::vector<bool> kyr;
  for (size_t i = 0; i < text.size();) {
    uint32_t u = zeichen(text, i);
    bool buchstabe = lateinisch(u) || kyrillisch(u) || arabisch(u);
    if (lateinisch(u)) nLat++; else if (kyrillisch(u)) nKyr++; else if (arabisch(u)) nAra++;
    uint32_t k = klein(u);
    utf8(kleinText, k);
    if (buchstabe) { utf8(wort, k); wortKyr = wortKyr || kyrillisch(u); }
    else if (!wort.empty()) { woerter.push_back(wort); kyr.push_back(wortKyr); wort.clear(); wortKyr = false; }
  }
  if (!wort.empty()) { woerter.push_back(wort); kyr.push_back(wortKyr); }
  int beste = std::max({nLat, nKyr, nAra});
  if (beste < 20) return {};
  if (beste == nAra) return {"ara", 0.6};
  const bool kyrText = beste == nKyr;
  std::vector<std::string> liste;
  for (size_t i = 0; i < woerter.size(); i++) if (!kyrText || kyr[i]) liste.push_back(woerter[i]);
  if (liste.size() < 8) return {};
  struct Punkte { const char *s; double p; int woerter; };
  std::vector<Punkte> punkte;
  for (const Liste &l : LISTEN) {
    if (l.kyrillisch != kyrText) continue;
    std::set<std::string> menge;
    const char *a = l.woerter;
    while (*a) { const char *b = strchr(a, ' '); if (!b) b = a + strlen(a); menge.insert(std::string(a, b)); a = *b ? b + 1 : b; }
    int p = 0;
    for (const std::string &w : liste) if (menge.count(w)) p++;
    int z = 0;
    for (size_t i = 0; l.zeichen[i];) {
      size_t j = i; zeichen(l.zeichen, j);
      std::string c(l.zeichen + i, j - i);
      for (size_t pos = kleinText.find(c); pos != std::string::npos; pos = kleinText.find(c, pos + c.size())) z++;
      i = j;
    }
    // Buchstaben zählen halb und höchstens so viel wie die Wörter – sie entscheiden nur knappe Fälle.
    punkte.push_back({l.kennung, p + std::min(z * 0.5, (double)std::max(p, 2)), p});
  }
  std::sort(punkte.begin(), punkte.end(), [](const Punkte &x, const Punkte &y) { return x.p > y.p; });
  if (punkte.empty() || punkte[0].woerter < 3) return {};
  double zweite = punkte.size() > 1 ? punkte[1].p : 0;
  double abstand = (punkte[0].p - zweite) / punkte[0].p;
  double anteil = std::min(1.0, punkte[0].woerter / (double)liste.size() / 0.15);
  return {punkte[0].s, std::min(1.0, abstand * 0.7 + anteil * 0.3)};
}

// Erkennt osd eine Schrift, die die Sprachen nicht lesen (z. B. Kyrillisch), die erste passende verfügbare Sprache;
// sonst leer. da(k): ob die Sprachdaten von k vorhanden sind.
template <class Da>
std::string spracheFuerSchrift(const std::string &schrift, const std::string &sprachen, Da da) {
  std::vector<std::string> passend;
  if (schrift == "Cyrillic") passend = {"rus", "ukr"};
  else if (schrift == "Arabic") passend = {"ara"};
  else return "";
  for (const std::string &k : passend) if (sprachen.find(k) != std::string::npos) return "";
  for (const std::string &k : passend) if (da(k)) return k;
  return "";
}
