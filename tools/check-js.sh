#!/usr/bin/env bash
# Syntax-check every file in assets/*.js and every inline <script> in the built
# pages. The site ships no build step for its JavaScript, so this is the only
# thing standing between a typo and a page whose table of contents never appears.
#
# Unlike the provider sites, this hub has no apps/ directory: it runs no lab and
# makes no API call, so the only script here is the shared site script.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v node >/dev/null || { echo "check-js: node not found — skipping"; exit 0; }
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fail=0
for f in assets/*.js; do [ -e "$f" ] || continue; node --check "$f" || fail=1; done
if [ -d docs ]; then
  python3 - "$tmp" <<'PY'
import pathlib, re, sys
tmp = pathlib.Path(sys.argv[1])
for src in sorted(pathlib.Path("docs").rglob("*.html")):
    for n, block in enumerate(re.findall(r"<script>(.*?)</script>", src.read_text(), re.S)):
        name = str(src.relative_to("docs")).replace("/", "_").removesuffix(".html")
        (tmp / f"{name}.{n}.js").write_text(block)
PY
fi
for f in "$tmp"/*.js; do [ -e "$f" ] || continue; node --check "$f" || { echo "  ^ in ${f##*/}"; fail=1; }; done
[ "$fail" = 0 ] && echo "check-js: all scripts parse."
exit $fail
