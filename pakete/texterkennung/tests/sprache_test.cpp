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
  // Sprachen je Seite (#579): Mischseite mit zwei Sprachen, kurzer fremder Satz zählt nicht.
  const std::string deu = "Sehr geehrte Frau Petra Muster, anbei leiten wir Ihnen das Schreiben der französischen Botschaft weiter. Die Unterlagen für die Beglaubigungen liegen bei, bitte prüfen Sie diese und senden Sie uns die Formulare bis zum Monatsende zurück.";
  const std::string fra = "Madame, nous avons bien reçu votre demande et nous vous remercions pour votre patience. Les documents demandés par les services consulaires de l'ambassade sont listés dans cette lettre et nous restons à votre disposition.";
  pruefe(sprachenEinerSeite(deu) == std::vector<std::string>{"deu"}, "Seite deutsch");
  pruefe(sprachenEinerSeite(fra) == std::vector<std::string>{"fra"}, "Seite französisch");
  std::vector<std::string> m = sprachenEinerSeite(deu + "\n\n" + fra);
  pruefe(m.size() == 2 && ((m[0] == "deu" && m[1] == "fra") || (m[0] == "fra" && m[1] == "deu")), "Mischseite: zwei Sprachen");
  pruefe(sprachenEinerSeite(deu + "\n \nMerci beaucoup et à bientôt.") == std::vector<std::string>{"deu"}, "Kurzer fremder Satz: keine Mischseite");
  pruefe(sprachenEinerSeite("12,50 EUR 4711").empty(), "Seite nur Zahlen: keine Sprache");
  auto da = [](const std::string &k) { return k == "rus"; };
  pruefe(spracheFuerSchrift("Cyrillic", "deu", da) == "rus", "Kyrillisch: rus dazu");
  pruefe(spracheFuerSchrift("Cyrillic", "rus+deu", da).empty(), "Kyrillisch: rus schon dabei");
  pruefe(spracheFuerSchrift("Arabic", "deu", da).empty(), "Arabisch: Sprachdaten fehlen");
  pruefe(spracheFuerSchrift("Latin", "deu", da).empty(), "Latein: nichts dazu");
  return fehler ? 1 : 0;
}
