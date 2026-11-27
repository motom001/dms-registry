// Erzeugt die Code-Matrizen für die Tests (tests/codes/*.txt) – nur von Hand nötig, wenn sich die Beispiele ändern.
// Nutzt den Schreiber von zxing-cpp (derselbe Commit wie code/bauen.sh), nativ gebaut:
//
//   cmake -S <zxing-cpp> -B nb -DBUILD_SHARED_LIBS=OFF -DZXING_WRITERS=OLD -DZXING_EXAMPLES=OFF -DZXING_BLACKBOX_TESTS=OFF
//   cmake --build nb && g++ -std=c++20 -I <zxing-cpp>/core/src tests/erzeuge.cpp nb/core/libZXing.a -o erzeuge
//   ./erzeuge tests/codes
//
// Je Datei: eine Zeile je Modulreihe, „1“ = dunkel, „0“ = hell; ohne Ruhezone (die setzt der Test). Strichcodes haben
// genau eine Zeile – der Test zieht sie in die Höhe. Die vCards, der Link und der GiroCode kommen aus
// tests/erzeuge_vcard.mjs (npm-Paket qrcode). Nur erfundene Werte und reservierte Beispiel-Domains.
#include <fstream>
#include <iostream>
#include <string>

#include "BitMatrix.h"
#include "MultiFormatWriter.h"

using namespace ZXing;

static void schreibe(const std::string &ordner, const std::string &name, BarcodeFormat f, const std::wstring &text, int breite = 0, int hoehe = 0) {
  MultiFormatWriter w(f);
  w.setMargin(0);
  if (f == BarcodeFormat::QRCode || f == BarcodeFormat::Aztec) w.setEccLevel(f == BarcodeFormat::Aztec ? 33 : 1);
  BitMatrix m = w.encode(text, breite, hoehe);
  bool strich = !(f == BarcodeFormat::QRCode || f == BarcodeFormat::Aztec || f == BarcodeFormat::DataMatrix || f == BarcodeFormat::PDF417);
  std::ofstream aus(ordner + "/" + name + ".txt");
  for (int y = 0; y < (strich ? 1 : m.height()); y++) {
    for (int x = 0; x < m.width(); x++) aus << (m.get(x, y) ? '1' : '0');
    aus << '\n';
  }
  std::cout << name << ": " << m.width() << "×" << (strich ? 1 : m.height()) << '\n';
}

int main(int argc, char **argv) {
  if (argc < 2) { std::cerr << "Ordner fehlt\n"; return 1; }
  std::string o = argv[1];
  // Link wie auf dem HU-Bericht (Digitaler Untersuchungsbericht) – erfundene Such-ID, Berichtsnummer und Kennnummer.
  schreibe(o, "dub", BarcodeFormat::QRCode, L"https://www.kba-online.de/dub/#/zugriffsdaten/A1B2C3D4E5F6/P0123456789/0815");
  schreibe(o, "ean13", BarcodeFormat::EAN13, L"4006381333931");
  schreibe(o, "code128", BarcodeFormat::Code128, L"RE-2026-004711");
  schreibe(o, "itf", BarcodeFormat::ITF, L"12345678901231");
  schreibe(o, "datamatrix", BarcodeFormat::DataMatrix, L"Paket 00340434161094042557");
  schreibe(o, "aztec", BarcodeFormat::Aztec, L"Fahrkarte Musterstadt-Beispielhausen 2. Klasse");
  schreibe(o, "pdf417", BarcodeFormat::PDF417, L"Bordkarte MUSTER/JONAS XY1234 Sitz 12A", 400, 120);
  return 0;
}
