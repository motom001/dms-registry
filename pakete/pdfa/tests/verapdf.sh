#!/usr/bin/env bash
# Prüft Archivfassungen mit veraPDF (Profil PDF/A-2b) – dem Prüfwerkzeug der PDF Association (GPL-3.0+/MPL-2.0, Java).
# veraPDF läuft nur hier im Test, nie im Paket. Feste Version, Prüfsumme der heruntergeladenen Datei geprüft.
#
#   tests/verapdf.sh <datei.pdf> ...
#
# Braucht Java 8 oder neuer. Lädt veraPDF beim ersten Mal nach ~/.cache/dms-registry/verapdf-<version>/.
set -euo pipefail
VERSION=1.30.1
SHA256=9f03fc5da454348329f4054256351aa6c6a91683329978e8294f21fe8a5d7abc
URL="https://software.verapdf.org/releases/${VERSION%.*}/verapdf-greenfield-${VERSION}-installer.zip"
ZIEL="${XDG_CACHE_HOME:-$HOME/.cache}/dms-registry/verapdf-$VERSION"
[ $# -gt 0 ] || { echo "Aufruf: tests/verapdf.sh <datei.pdf> ..." >&2; exit 2; }
command -v java >/dev/null || { echo "veraPDF braucht Java" >&2; exit 1; }

if [ ! -x "$ZIEL/verapdf" ]; then
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL --retry 3 -o "$tmp/verapdf.zip" "$URL"
  ist=$(sha256sum "$tmp/verapdf.zip" | cut -d' ' -f1)
  if [ "$ist" != "$SHA256" ]; then echo "veraPDF $VERSION: Prüfsumme $ist, erwartet $SHA256" >&2; exit 1; fi
  (cd "$tmp" && unzip -q verapdf.zip)
  # Unbeaufsichtigt installieren (IzPack): nur die Kommandozeile.
  cat > "$tmp/auto.xml" <<XML
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<AutomatedInstallation langpack="eng">
  <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel id="welcome"/>
  <com.izforge.izpack.panels.target.TargetPanel id="install_dir"><installpath>$ZIEL</installpath></com.izforge.izpack.panels.target.TargetPanel>
  <com.izforge.izpack.panels.packs.PacksPanel id="sdk_pack_select">
    <pack index="0" name="veraPDF GUI" selected="false"/>
    <pack index="1" name="veraPDF CLI" selected="true"/>
    <pack index="2" name="veraPDF Documentation" selected="false"/>
    <pack index="3" name="veraPDF Sample Plugins" selected="false"/>
  </com.izforge.izpack.panels.packs.PacksPanel>
  <com.izforge.izpack.panels.install.InstallPanel id="install"/>
  <com.izforge.izpack.panels.finish.FinishPanel id="finish"/>
</AutomatedInstallation>
XML
  java -jar "$tmp/verapdf-greenfield-$VERSION/verapdf-izpack-installer-$VERSION.jar" "$tmp/auto.xml" >/dev/null
fi

fehler=0
for f in "$@"; do
  aus=$("$ZIEL/verapdf" --flavour 2b --format text --verbose "$f" 2>&1 || true)
  if echo "$aus" | grep -q '^PASS '; then echo "✓ veraPDF PDF/A-2b: $(basename "$f")"
  else echo "✗ veraPDF PDF/A-2b: $(basename "$f")"; echo "$aus" | head -40; fehler=$((fehler + 1)); fi
done
exit $fehler
