#!/bin/sh
# Builds the site into public/. Used by DigitalOcean App Platform, which has no Zola on its build image.
#
# First it checks the pinned sdr-ui (config.toml [extra.ui]) against the hosted manifest: a page whose integrity hash does
# not match what the CDN serves would render unstyled, so a mismatch (or an unpublished version) fails the build instead.
set -eu
ZOLA_VERSION="0.23.6"

pin() { sed -n "/^\[extra.ui\]/,/^\[/s/^$1 = \"\(.*\)\"/\1/p" config.toml; }
base=$(pin base)
manifest=$(curl -fsSL "${base}manifest.json") || { echo "sdr-ui: ${base}manifest.json is not published" >&2; exit 1; }
for pair in "css sdr-ui.css" "boot boot.js" "transitions transitions.js"; do
  key=${pair% *}; file=${pair#* }
  want=$(pin "$key")
  got=$(printf '%s' "$manifest" | tr -d '\n ' | sed -n "s/.*\"$file\":{\"sri\":\"\([^\"]*\)\".*/\1/p")
  [ "$want" = "$got" ] || { echo "sdr-ui: config.toml pins $file at $want, ${base} serves $got" >&2; exit 1; }
done
echo "sdr-ui $(pin version): pin matches ${base}"

if ! command -v zola >/dev/null 2>&1; then
  curl -sSL "https://github.com/getzola/zola/releases/download/v${ZOLA_VERSION}/zola-v${ZOLA_VERSION}-x86_64-unknown-linux-gnu.tar.gz" | tar xz zola
  ZOLA=./zola
else
  ZOLA=zola
fi
"$ZOLA" build
