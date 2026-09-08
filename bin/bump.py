#!/usr/bin/env python3
"""Bump the site version, exactly once per release, in the two places that own it.

    bin/bump.py "what changed in this release"      # next minor
    bin/bump.py --major "what changed"              # vR.M+1.0

Does three things and stops:
  1. admin/build/version.txt  -> the next version
  2. content/versions.md      -> a new row at the top of the release history
  3. prints the commit subject CI requires

The pipeline enforces all of this from the other side: tag-release reads
version.txt, finds the commit whose subject carries the same version, and refuses
to tag if the two disagree or if the bump was not the next minor. Doing it by hand
is how a release ends up with a duplicated row in the table or a tag pointing at
the wrong commit, both of which have happened on sibling sites. So it is a script.

Run `python3 build.py` afterwards — it propagates the new version to every page's
badge, the footer and llms.txt, and the gate fails if any of them disagree.
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "admin/build/version.txt"
HISTORY = ROOT / "content/versions.md"
MARKER = "<!-- releases -->\n"


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--major"]
    major = "--major" in sys.argv[1:]
    if len(args) != 1:
        print(__doc__)
        return 2
    summary = args[0]

    cur = VERSION_FILE.read_text().strip()
    m = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", cur)
    if not m:
        print(f"version.txt does not carry a vX.Y.Z version: {cur!r}", file=sys.stderr)
        return 1
    rel, maj, mnr = (int(x) for x in m.groups())
    new = f"v{rel}.{maj + 1}.0" if major else f"v{rel}.{maj}.{mnr + 1}"

    md = HISTORY.read_text()
    if f'class="vnum">{new}<' in md:
        print(f"content/versions.md already lists {new} — the version was not bumped", file=sys.stderr)
        return 1
    if MARKER not in md:
        print(f"content/versions.md has no '{MARKER.strip()}' marker to insert below", file=sys.stderr)
        return 1

    row = (f'    <tr><td class="vnum">{new}</td><td>{date.today().isoformat()}</td>'
           f'<td>{summary}</td></tr>\n')
    HISTORY.write_text(md.replace(MARKER, MARKER + row, 1))
    VERSION_FILE.write_text(new + "\n")

    print(f"{cur} -> {new}")
    print("  · admin/build/version.txt")
    print("  · content/versions.md (row added)")
    print()
    print("next:")
    print("  python3 build.py")
    print("  admin/build/validate.sh")
    print(f'  git commit -am "site {new}: {summary}" && git push origin dev')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
