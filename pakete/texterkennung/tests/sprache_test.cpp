// Test der Spracherkennung (code/sprache.h), nativ übersetzt von code/bauen.sh.
#include <cstdio>
#include <string>
#include "sprache.h"

static int fehler = 0;
static void pruefe(bool ok, const char *was) { std::printf("%s %s\n", ok ? "ok" : "FEHLER", was); if (!ok) fehler++; }

int main() {
  ErkannteSprache d = erkenneSprache("Sehr geehrte Frau Petra Muster, wir bedanken uns für Ihre Anfrage und senden Ihnen die Rechnung für den Monat Januar. Bitte überweisen Sie den Betrag bis zum Ende des Monats.");
  pruefe(d.sprache == "deu" && d.konfidenz >= 0.5, "Deutscher Brief");
  ErkannteSprache e = erkenneSprache("Dear Mr Jonas, thank you for your order. Please find attached the invoice for the services we have provided and let us know if there are any questions.");
  pruefe(e.sprache == "eng" && e.konfidenz >= 0.5, "Englischer Brief");
  ErkannteSprache f = erkenneSprache("Madame, nous vous remercions pour votre commande. Vous trouverez dans cette lettre la facture pour le mois de janvier et les conditions de paiement.");
  pruefe(f.sprache == "fra", "Französischer Brief");
  ErkannteSprache r = erkenneSprache("Уважаемый Маркус, спасибо за ваш заказ. Мы отправляем вам счет за январь и просим оплатить его до конца месяца, так как это важно для нас.");
  pruefe(r.sprache == "rus", "Russischer Brief");
  pruefe(erkenneSprache("12,50 EUR 13.01.2027 4711 0815").sprache.empty(), "Nur Zahlen: keine Sprache");
  pruefe(erkenneSprache("").sprache.empty(), "Leer: keine Sprache");
  auto da = [](const std::string &k) { return k == "rus"; };
  pruefe(spracheFuerSchrift("Cyrillic", "deu", da) == "rus", "Kyrillisch: rus dazu");
  pruefe(spracheFuerSchrift("Cyrillic", "rus+deu", da).empty(), "Kyrillisch: rus schon dabei");
  pruefe(spracheFuerSchrift("Arabic", "deu", da).empty(), "Arabisch: Sprachdaten fehlen");
  pruefe(spracheFuerSchrift("Latin", "deu", da).empty(), "Latein: nichts dazu");
  return fehler ? 1 : 0;
}
