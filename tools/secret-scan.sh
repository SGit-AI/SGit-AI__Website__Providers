#!/usr/bin/env bash
# secret-scan.sh — the required check. This repository is public; the vault its
# content came from was not, so every safety property that material relied on is
# gone. A leaked key here would be the site's own headline.
#
# Runs over the working tree (or, with --staged, over what is about to be committed).
# Exits non-zero on the first match, and prints the file and line.
set -uo pipefail
cd "$(dirname "$0")/.."

PATTERNS=(
  'sk_[A-Za-z0-9]{32,}'                 # ElevenLabs
  'sk-or-v1-[A-Za-z0-9]{16,}'           # OpenRouter
  'sk-[A-Za-z0-9]{32,}'                 # OpenAI-shaped
  # A key pasted into a curl example. The trailing length qualifier matters: the
  # published briefs quote this scan's own grep pattern, and a header name next to
  # an empty placeholder is documentation, not a leak.
  'xi-api-key:[[:space:]]*sk_[A-Za-z0-9]{20,}'
  'sgit_private_vault_[A-Za-z0-9]+'     # vault keys
  'hf_[A-Za-z0-9]{20,}'                 # Hugging Face
  'AKIA[0-9A-Z]{16}'                    # AWS
  'ghp_[A-Za-z0-9]{36}'                 # GitHub PAT
  'AIza[0-9A-Za-z_-]{35}'               # Google
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'
)

status=0
for p in "${PATTERNS[@]}"; do
  # --exclude-dir keeps the scanner out of git internals; everything else,
  # including the built site under docs/, is in scope on purpose.
  if hits=$(grep -rInE --binary-files=without-match \
        --exclude-dir=.git --exclude="$(basename "$0")" \
        "$p" . 2>/dev/null); then
    echo "SECRET SCAN FAILED — pattern /$p/ matched:"
    echo "$hits" | head -20
    status=1
  fi
done

if [ "$status" = 0 ]; then
  echo "secret-scan: clean (${#PATTERNS[@]} patterns, whole tree including docs/)."
fi
exit $status
