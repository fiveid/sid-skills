#!/usr/bin/env bash
# Install the quality gate's pinned tools. Used by CI and for local runs.
#
#   scripts/install-tools.sh
#
# Python tools go into .venv from requirements-quality.txt (every package hash-pinned).
# Binaries go into .tools/, each download checked against the SHA-256 recorded below.
# Re-running is safe: a tool already at its pinned version is skipped.
# Versions and the reasons for them are recorded in QUALITY.md.

set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

BETTERLEAKS_VERSION=1.9.0
LYCHEE_VERSION=0.24.2
APM_VERSION=0.35.0

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)
    PLATFORM=linux-x64
    BETTERLEAKS_SHA=f8b185a39ffcece2a1ca82bf3a4e7435cd81963ffd16b7a9128daf75f35f6de7
    LYCHEE_SHA=1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a
    APM_SHA=5aa23ce61eebae9411668f507772cdb5d87252c760078dc59b5acdc5188d785b
    ;;
  Linux-aarch64 | Linux-arm64)
    PLATFORM=linux-arm64
    BETTERLEAKS_SHA=1d39116e0a58dc94574715e2aa12a2dbd5062f193eee3fec011fef6ba06bd13b
    LYCHEE_SHA=91a7bd65685da41b90ccb9bc867a3d649a7818042dae04ff405e55a25bddee4c
    APM_SHA=ada8901ce1b29e5d188629eeed64e8499853a8cb5f047630ebedbde24008508e
    ;;
  Darwin-arm64)
    PLATFORM=darwin-arm64
    BETTERLEAKS_SHA=83dd7eaab13d44a1e8e347a17064cdef153a1478db473276d41b38d55613d3f2
    LYCHEE_SHA=c9d3740ea2d891854d37116c9fba840f37b6e7c89d330e7db84ac333631c4977
    APM_SHA=cb2c54152e3bd39acfe2fbda4a2aa91d2af914e24859d3623423efd7b27e3dd0
    ;;
  Darwin-x86_64)
    PLATFORM=darwin-x64
    BETTERLEAKS_SHA=68dfd83458d9e7f90663daa7a81c7f944083b170dae82e4f5f8d0581ed519ef1
    LYCHEE_SHA=887503a9cff667d322b8d0892b40bf49976eb9507af8483220a3706cdad55978
    APM_SHA=ee17daf433c49ed481d9f2ddee31825cbced9390637cab9a5138815bbace327c
    ;;
  *)
    echo "No pinned tool binaries for $(uname -s) $(uname -m)." >&2
    exit 1
    ;;
esac

case "$PLATFORM" in
  linux-x64) BL_ASSET=linux_x64 LY_ASSET=x86_64-unknown-linux-gnu APM_ASSET=linux-x86_64 ;;
  linux-arm64) BL_ASSET=linux_arm64 LY_ASSET=aarch64-unknown-linux-gnu APM_ASSET=linux-arm64 ;;
  darwin-arm64) BL_ASSET=darwin_arm64 LY_ASSET=aarch64-apple-darwin APM_ASSET=darwin-arm64 ;;
  darwin-x64) BL_ASSET=darwin_x64 LY_ASSET=x86_64-apple-darwin APM_ASSET=darwin-x86_64 ;;
esac

sha256() {
  if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1
}

# download <url> <expected sha256> <output file>
download() {
  curl -sSfL --retry 3 -o "$3" "$1"
  local actual
  actual=$(sha256 "$3")
  if [ "$actual" != "$2" ]; then
    echo "Checksum mismatch for $1: expected $2, got $actual" >&2
    rm -f "$3"
    exit 1
  fi
}

# installed <name> <version>: true if this version is already in place
installed() { [ -f ".tools/.$1-$2" ]; }

mkdir -p .tools/bin
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

if ! installed betterleaks "$BETTERLEAKS_VERSION"; then
  download "https://github.com/betterleaks/betterleaks/releases/download/v${BETTERLEAKS_VERSION}/betterleaks_${BETTERLEAKS_VERSION}_${BL_ASSET}.tar.gz" \
    "$BETTERLEAKS_SHA" "$tmp/betterleaks.tar.gz"
  tar -xzf "$tmp/betterleaks.tar.gz" -C .tools/bin betterleaks
  rm -f .tools/.betterleaks-* && touch ".tools/.betterleaks-$BETTERLEAKS_VERSION"
fi

if ! installed lychee "$LYCHEE_VERSION"; then
  download "https://github.com/lycheeverse/lychee/releases/download/lychee-v${LYCHEE_VERSION}/lychee-${LY_ASSET}.tar.gz" \
    "$LYCHEE_SHA" "$tmp/lychee.tar.gz"
  tar -xzf "$tmp/lychee.tar.gz" -C "$tmp"
  cp "$tmp/lychee-${LY_ASSET}/lychee" .tools/bin/lychee
  rm -f .tools/.lychee-* && touch ".tools/.lychee-$LYCHEE_VERSION"
fi

if ! installed apm "$APM_VERSION"; then
  download "https://github.com/microsoft/apm/releases/download/v${APM_VERSION}/apm-${APM_ASSET}.tar.gz" \
    "$APM_SHA" "$tmp/apm.tar.gz"
  rm -rf .tools/apm && mkdir -p .tools/apm
  tar -xzf "$tmp/apm.tar.gz" -C .tools/apm --strip-components=1
  rm -f .tools/.apm-* && touch ".tools/.apm-$APM_VERSION"
fi

if [ ! -x .venv/bin/python ]; then
  "${PYTHON:-python3}" -m venv .venv
fi
.venv/bin/pip install --quiet --disable-pip-version-check --require-hashes -r requirements-quality.txt

echo "Quality tools installed: .venv (Python tools), .tools/ (betterleaks $BETTERLEAKS_VERSION, lychee $LYCHEE_VERSION, apm $APM_VERSION)."
