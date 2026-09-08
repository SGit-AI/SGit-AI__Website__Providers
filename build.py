#!/usr/bin/env python3
"""
build.py — the whole build system for providers.sgit.ai, the hub of the family.

Markdown in `content/` is the source of truth; this script renders it to static
HTML in `docs/`. No dependencies, no framework, no CDN: a site that argues for
credential hygiene should not ask a reader to trust forty transitive packages.

    python3 build.py            build docs/
    python3 build.py --check    build to a temp dir and diff against docs/ (CI)

Generated, not hand-written:
  * the comparison matrix          — from `patterns:` front-matter on provider pages
  * the ledger of claims           — from data/claims.yml, joined to every {{claim:id}}
  * the experiments index          — from the experiment pages' front-matter
  * each page's markdown twin      — docs/<path>/index.md, the house convention
"""

import html
import os
import re
import shutil
import sys
import tempfile
import filecmp
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
APPS = ROOT / "apps"
ASSETS = ROOT / "assets"
FILES = ROOT / "files"
DATA = ROOT / "data"
BRIEFS = ROOT / "briefs"
OUT = ROOT / "docs"

# The estate convention: one file owns the version, `bin/bump.py` moves it, the
# release commit's subject repeats it, and CI refuses to tag if the two disagree.
VERSION = (ROOT / "admin" / "build" / "version.txt").read_text().strip()
# The host is owned by docs/CNAME's source of truth, here, and every canonical URL
# on the site is checked against it before a release.
DOMAIN = "providers.sgit.ai"

SITE = {
    "domain": DOMAIN,
    "base": f"https://{DOMAIN}",
    "title": "Where the key goes",
    "vault_commit": "7d1916aca5f3",
    "version": VERSION,
}

# Two levels, as on the sibling sites: every group label is itself a link to a real
# page, so nothing is reachable only by opening a menu.
NAV = [
    ("The argument", "/", []),
    ("The four patterns", "/patterns/", []),
    ("Comparison", "/comparison/", []),
    ("Provider sites", "/sites/", []),
    ("The contract", "/contract/", []),
    ("Evidence", "/evidence/", []),
    ("Disclosures", "/disclosures/", []),
]

LICENCE_STAMP = (
    "This document is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0)."
)

NON_AFFILIATION = (
    "Independent work by SGit-AI. Not affiliated with, endorsed by, or sponsored by any "
    "provider written about here. Provider names identify the APIs these pages report on; "
    "all trademarks belong to their owners."
)

# ---------------------------------------------------------------- tiny YAML ---
# A deliberate subset: mappings, sequences, sequences of mappings, inline lists,
# quoted scalars. Anything hairier belongs in prose, not in front-matter.


def yaml_load(text):
    lines = []
    for raw in text.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    val, _ = _yaml_block(lines, 0, 0)
    return val


def _scalar(s):
    s = s.strip()
    if not s:
        return ""
    if s[0] in "\"'" and s[-1] == s[0] and len(s) > 1:
        body = s[1:-1]
        if s[0] == '"':                       # only double quotes take escapes
            body = body.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")
        return body
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        return [_scalar(x) for x in _split_commas(inner)] if inner else []
    if s == "true":
        return True
    if s == "false":
        return False
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d*\.\d+", s):
        return float(s)
    return s


def _split_commas(s):
    out, depth, cur, quote = [], 0, "", None
    for ch in s:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote, cur = ch, cur + ch
        elif ch in "[{":
            depth, cur = depth + 1, cur + ch
        elif ch in "]}":
            depth, cur = depth - 1, cur + ch
        elif ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out]


def _yaml_block(lines, i, indent):
    if i >= len(lines):
        return {}, i
    if lines[i][1].startswith("- "):
        return _yaml_seq(lines, i, indent)
    return _yaml_map(lines, i, indent)


def _yaml_map(lines, i, indent):
    out = {}
    while i < len(lines):
        ind, text = lines[i]
        if ind < indent:
            break
        if ind > indent:  # defensive: a stray deeper line
            i += 1
            continue
        key, _, rest = text.partition(":")
        key, rest = key.strip(), rest.strip()
        if rest:
            out[key] = _scalar(rest)
            i += 1
        else:
            i += 1
            if i < len(lines) and lines[i][0] > ind:
                out[key], i = _yaml_block(lines, i, lines[i][0])
            else:
                out[key] = None
    return out, i


def _yaml_seq(lines, i, indent):
    out = []
    while i < len(lines):
        ind, text = lines[i]
        if ind < indent or not text.startswith("- "):
            break
        body = text[2:].strip()
        if ":" in body and not body.startswith(("\"", "'")):
            # a mapping whose first pair is on the dash line
            sub_lines = [(0, body)]
            j = i + 1
            while j < len(lines) and lines[j][0] > ind:
                sub_lines.append((lines[j][0] - (ind + 2), lines[j][1]))
                j += 1
            item, _ = _yaml_map(sub_lines, 0, 0)
            out.append(item)
            i = j
        else:
            out.append(_scalar(body))
            i += 1
    return out, i


# ------------------------------------------------------------- markdown ------
# A subset of GFM: headings, paragraphs, lists, tables, fenced code, block
# quotes, rules, inline emphasis/code/links. Enough for a report; small enough
# to read in one sitting.

INLINE_CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
EM = re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])")
STRIKE = re.compile(r"~~([^~]+)~~")


def slugify(text):
    s = re.sub(r"<[^>]+>", "", text).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "section"


def inline(text, ctx):
    """Inline markdown → HTML. Code spans are extracted first so nothing
    inside them is interpreted."""
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = INLINE_CODE.sub(stash, text)
    text = shortcodes_inline(text, ctx)
    # GFM autolinks. Without this, <https://example.com/x> reaches the browser as an
    # unknown tag and the URL disappears from the page entirely — which is how §4's
    # vendor citation shipped with its URL invisible. Every quote there is supposed to
    # carry the product, the URL and the date read; two of the three were arriving.
    text = re.sub(
        r"<(https?://[^>\s]+)>",
        lambda m: f'<a href="{m.group(1)}" rel="noopener">{m.group(1)}</a>',
        text,
    )
    placeholders = {}

    def stash_html(fragment):
        placeholders[f"\x01{len(placeholders)}\x01"] = fragment
        return list(placeholders)[-1]

    # keep raw <chip …> etc. produced by shortcodes out of the escaper
    parts = re.split(r"(<[^>]+>)", text)
    text = "".join(stash_html(p) if p.startswith("<") and p.endswith(">") else html.escape(p, quote=False) for p in parts)

    text = LINK.sub(lambda m: _link(m, ctx), text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = EM.sub(r"<em>\1</em>", text)
    text = STRIKE.sub(r"<s>\1</s>", text)
    text = text.replace("--", "&ndash;") if False else text
    for k, v in placeholders.items():
        text = text.replace(k, v)
    for i, code in enumerate(spans):
        text = text.replace(f"\x00{i}\x00", f"<code>{html.escape(code, quote=False)}</code>")
    return text


def _link(m, ctx):
    label, href, title = m.group(1), m.group(2), m.group(3)
    ext = href.startswith("http") and SITE["domain"] not in href
    attrs = f' title="{html.escape(title)}"' if title else ""
    if ext:
        attrs += ' rel="noopener"'
        ctx["external_links"].add(href)
    return f'<a href="{html.escape(href)}"{attrs}>{label}</a>'


def render_markdown(md, ctx):
    lines = md.split("\n")
    out, i = [], 0
    last, spins = -1, 0
    while i < len(lines):
        if i == last:                      # every branch must consume at least one line
            spins += 1
            if spins > 1:
                raise SystemExit(f"build: parser stuck at line {i + 1}: {lines[i]!r}")
        else:
            last, spins = i, 0
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # fenced code
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            body, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            cls = "shell" if lang in ("bash", "sh", "console", "shell") else (f"lang-{lang}" if lang else "")
            out.append(f'<pre class="{cls}">{html.escape(chr(10).join(body))}</pre>')
            continue

        # a block shortcode on a line of its own: {{app}}, {{ledger}}, {{comparison}}…
        if re.fullmatch(r"\{\{[a-z-]+\}\}", stripped):
            out.append(shortcodes_block(stripped, ctx))
            i += 1
            continue

        # raw html block (an <aside>, a stat-tile row, the app slot)
        if stripped.startswith("<") and not stripped.startswith("<http"):
            block = []
            while i < len(lines) and lines[i].strip():
                block.append(lines[i])
                i += 1
            out.append(shortcodes_block("\n".join(block), ctx))
            continue

        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            anchor = slugify(text)
            rendered = inline(text, ctx)
            if level >= 2:
                ctx["toc"].append((level, anchor, re.sub(r"<[^>]+>", "", rendered)))
            out.append(f'<h{level} id="{anchor}">{rendered}</h{level}>')
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"(-{3,}|\*{3,})", stripped):
            out.append("<hr>")
            i += 1
            continue

        # table
        if "|" in stripped and i + 1 < len(lines) and re.fullmatch(r"\|?[\s:|-]+\|[\s:|-]*", lines[i + 1].strip()):
            head = _row(lines[i])
            aligns = [_align(c) for c in _row(lines[i + 1])]
            i += 2
            body = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                body.append(_row(lines[i]))
                i += 1
            th = "".join(f"<th{_style(a)}>{inline(c, ctx)}</th>" for c, a in zip(head, aligns + [None] * len(head)))
            trs = []
            for r in body:
                tds = "".join(f"<td{_style(a)}>{inline(c, ctx)}</td>" for c, a in zip(r, aligns + [None] * len(r)))
                trs.append(f"<tr>{tds}</tr>")
            out.append(
                '<div class="tablewrap"><table><thead><tr>' + th + "</tr></thead><tbody>" + "".join(trs) + "</tbody></table></div>"
            )
            continue

        # blockquote
        if stripped.startswith(">"):
            body = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                body.append(lines[i].strip()[1:].strip())
                i += 1
            out.append("<blockquote>" + render_markdown("\n".join(body), ctx) + "</blockquote>")
            continue

        # lists
        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            block, base = [], len(line) - len(line.lstrip(" "))
            while i < len(lines) and (
                re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) or (lines[i].strip() and (len(lines[i]) - len(lines[i].lstrip(" "))) > base)
            ):
                block.append(lines[i])
                i += 1
            out.append(_list(block, base, ctx))
            continue

        # paragraph
        para = [lines[i].strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not _breaks_paragraph(lines, i):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(" ".join(para), ctx) + "</p>")
    return "\n".join(out)


def _breaks_paragraph(lines, i):
    """A paragraph ends at whatever starts another block. Note the space required
    after a bullet: `**bold at the start of a line**` is not a list item."""
    line = lines[i]
    if re.match(r"^\s*([-*]\s+|\d+\.\s+|#{1,6}\s|>|```)", line):
        return True
    if line.strip().startswith("<") and not line.strip().startswith("<http"):
        return True
    if "|" in line and i + 1 < len(lines) and re.fullmatch(r"\|?[\s:|-]+\|[\s:|-]*", lines[i + 1].strip()):
        return True
    return False


def _row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, cur, esc = [], "", False
    for ch in line:
        if esc:
            cur, esc = cur + ch, False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def _align(cell):
    cell = cell.strip()
    if cell.startswith(":") and cell.endswith(":"):
        return "center"
    if cell.endswith(":"):
        return "right"
    return None


def _style(a):
    return f' style="text-align:{a}"' if a else ""


def _list(block, base, ctx):
    ordered = bool(re.match(r"^\s*\d+\.\s+", block[0]))
    items, cur = [], None
    for line in block:
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        indent = len(line) - len(line.lstrip(" "))
        if m and indent == base:
            if cur is not None:
                items.append(cur)
            cur = [m.group(3)]
        elif cur is not None:
            cur.append(line[base:] if len(line) > base else line.strip())
    if cur is not None:
        items.append(cur)
    lis = []
    for item in items:
        first, rest = item[0], [x for x in item[1:] if x.strip()]
        body = inline(first, ctx)
        if rest:
            sub_base = min(len(x) - len(x.lstrip(" ")) for x in rest)
            body += render_markdown("\n".join(x[sub_base:] if len(x) > sub_base else x for x in rest), ctx)
        lis.append(f"<li>{body}</li>")
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(lis) + f"</{tag}>"


# ------------------------------------------------------------- shortcodes ----

STATES = {
    "verified": ("verified", "st-v", "Verified by execution on this date, by us."),
    "measured": ("measured", "st-m", "Measured by our own pipeline on a named workload and date."),
    "docs": ("vendor docs", "st-d", "Read from the vendor's documentation on this date. Never executed by us."),
    "spec": ("specified, not shipped", "st-s", "A specification. It does not exist yet."),
    "unrun": ("written, not run", "st-u", "Code we wrote and have never executed."),
    "projected": ("projected", "st-p", "Arithmetic, not an invoice. The workings are shown."),
}


def chip(state, date=None, claim_id=None, label=None):
    text, cls, why = STATES.get(state, ("unknown", "st-u", ""))
    body = label or text
    if date:
        body += f" {date}"
    title = html.escape(why)
    if claim_id:
        return f'<a class="chip {cls}" href="/ledger/#claim-{claim_id}" title="{title}">{html.escape(body)}</a>'
    return f'<span class="chip {cls}" title="{title}">{html.escape(body)}</span>'


def shortcodes_inline(text, ctx):
    def claim_ref(m):
        cid = m.group(1)
        c = ctx["claims_by_id"].get(cid)
        if not c:
            raise SystemExit(f"build: unknown claim id {cid!r} referenced by {ctx['page']}")
        ctx["claim_uses"].setdefault(cid, set()).add(ctx["page"])
        return chip(c["state"], c.get("date_label"), cid)

    def live_ref(m):
        """{{live:Name}} and {{live:Name|path}} — a provider's base URL, resolved
        at build time from the measured `live:` in providers.yml. Typing a
        provider URL into prose is how a page ends up linking a host that stopped
        serving; this cannot, because it is the same value the tables use."""
        name, _, path = m.group(1).partition("|")
        for prov in _providers()["providers"]:
            if prov["name"].lower() == name.strip().lower():
                return _live(prov) + "/" + path.strip().lstrip("/")
        raise SystemExit(f"build: unknown provider {name!r} referenced by {ctx['page']}")

    text = re.sub(r"\{\{live:([^}]+)\}\}", live_ref, text)
    text = re.sub(r"\{\{claim:([a-z0-9-]+)\}\}", claim_ref, text)
    text = re.sub(
        r"\{\{badge:([a-z]+)(?:\|([^}]+))?\}\}",
        lambda m: chip(m.group(1), m.group(2)),
        text,
    )
    return text


def shortcodes_block(block, ctx):
    m = re.fullmatch(r"\s*\{\{([a-z-]+)\}\}\s*", block)
    if not m:
        # a hand-written HTML block: inline shortcodes still expand inside it, so a
        # claim chip can sit in a stat tile without going through the escaper.
        return shortcodes_inline(block, ctx)
    name = m.group(1)
    fn = BLOCKS.get(name)
    if not fn:
        raise SystemExit(f"build: unknown block shortcode {{{{{name}}}}} on {ctx['page']}")
    return fn(ctx)


# ------------------------------------------------------- generated blocks ----

PATTERN_NAMES = {
    "0": "0 &middot; key in the page",
    "1": "1 &middot; bounded key in the page",
    "2": "2 &middot; short-lived token",
    "3": "3 &middot; host holds the key",
}
VERDICT_MARK = {
    "yes": ('<span class="v v-yes">&check;</span>', "available"),
    "no": ('<span class="v v-no">&times;</span>', "unavailable"),
    "never": ('<span class="v v-never">&#9888;</span>', "available and never acceptable"),
    "spec": ('<span class="v v-spec">&#9686;</span>', "specified here, not shipped"),
    "na": ('<span class="v v-na">&mdash;</span>', "not applicable"),
}


def _providers():
    """The family, as synced from each provider site's own published markdown twin
    and search index by bin/sync-providers.py. The build never touches the network:
    a sync is a deliberate, dated act, and the date is printed wherever the data is."""
    return yaml_load((DATA / "providers.yml").read_text())


def _live(p):
    """Where a site actually serves today, as measured by bin/sync-providers.py
    rather than assumed: the canonical host once a probe of it returns that site's
    own index, and the GitHub Pages project path until then. Every link to a
    provider on this site goes through here, so none of them can be typed."""
    return (p.get("live") or p.get("canonical", "")).rstrip("/")


def block_family(ctx):
    """One card per site in the family. A planned site is not a link: there is
    nowhere for it to go, and a card that looks clickable and is not is a lie."""
    data = _providers()
    cards = []
    for p in data["providers"]:
        chips = "".join(chip(st) for st in (p.get("state_chips") or []))
        pending = p.get("state") == "planned"
        # The probe's answer, not the shape of the URL: a planned site's canonical
        # equals its live value and still does not resolve, so asking whether the
        # two match would call it live when nothing serves it.
        note = "" if p.get("canonical_resolves") == "yes" else ' &middot; <b>not serving yet</b>'
        body = (
            f'<span class="tag">{html.escape(str(p.get("kind", "provider")))}</span>'
            f'<h3>{html.escape(p["name"])}</h3>'
            f'<p>{html.escape(str(p.get("summary", "")))}</p>'
            f'<p class="small dim"><code>{html.escape(p["canonical"])}</code>{note}</p>'
            f'<div class="chips">{chips}</div>'
            f'<span class="go">{"Not built yet" if pending else "Read the report &rarr;"}</span>'
        )
        if pending:
            cards.append(f'<div class="card card-planned">{body}</div>')
        else:
            cards.append(f'<a class="card" href="{_live(p)}/" rel="noopener">{body}</a>')
    return '<div class="cards">' + "".join(cards) + "</div>"


def block_comparison(ctx):
    """One row per provider and product, one column per pattern — assembled from what
    each provider site publishes about itself rather than from a table kept here."""
    data = _providers()
    rows = []
    for p in data["providers"]:
        entries = p.get("patterns") or []
        for i, entry in enumerate(entries):
            # One provider, several products: name the site once and span its rows,
            # so the eye reads "ElevenLabs has two products" rather than two providers.
            cells = []
            for n in ("0", "1", "2", "3"):
                v = entry.get(f"p{n}") or {}
                verdict = {True: "yes", False: "no"}.get(v.get("verdict"), str(v.get("verdict", "na")).lower())
                mark, meaning = VERDICT_MARK.get(verdict, VERDICT_MARK["na"])
                cells.append(f'<td title="{meaning}">{mark}<span class="vnote">{html.escape(str(v.get("note", "")))}</span></td>')
            name = (
                f'<th scope="rowgroup" rowspan="{len(entries)}">'
                f'<a href="{_live(p)}/" rel="noopener">{html.escape(entry.get("provider", p["name"]))}</a></th>'
                if i == 0 else ""
            )
            rows.append(
                f'<tr>{name}'
                f'<td>{html.escape(str(entry.get("product", "")))}</td>' + "".join(cells)
                + f'<td>{html.escape(str(entry.get("server", "")))}</td></tr>'
            )
    head = "".join(f"<th>{n}</th>" for n in PATTERN_NAMES.values())
    legend = " &middot; ".join(f"{VERDICT_MARK[k][0]} {VERDICT_MARK[k][1]}" for k in VERDICT_MARK)
    return (
        '<div class="tablewrap"><table class="cmp"><thead><tr><th>Provider</th><th>Product</th>'
        + head + "<th>Needs a server for the safe pattern</th></tr></thead><tbody>"
        + "".join(rows) + "</tbody></table></div>"
        + f'<p class="small dim legend">{legend}</p>'
        + f'<p class="small dim">Synced from each provider site\'s own published front-matter on '
        f'<b>{html.escape(str(data.get("synced", "")))}</b> by <code>bin/sync-providers.py</code>. '
        "This hub keeps no opinion of its own about a provider: if a row is wrong, it is wrong on that "
        "provider\'s own page first.</p>"
    )


def block_evidence(ctx):
    """The roll-up only a hub can produce: how much of the family is actually
    verified, and how much is still somebody reading a vendor's documentation."""
    data = _providers()
    totals, per_site = {}, []
    for p in data["providers"]:
        counts = p.get("claims") or {}
        if not counts:
            continue
        for k, v in counts.items():
            totals[k] = totals.get(k, 0) + int(v)
        n = sum(int(v) for v in counts.values())
        bars = "".join(
            f'<span class="ebar st-{STATES[k][1][-1]}" style="width:{int(v) / n * 100:.1f}%" '
            f'title="{k}: {v}"></span>' for k, v in counts.items() if k in STATES
        )
        per_site.append(
            f'<tr><th scope="row"><a href="{_live(p)}/ledger/" rel="noopener">{html.escape(p["name"])}</a></th>'
            f'<td>{n}</td><td class="ebars">{bars}</td>'
            + "".join(f"<td>{counts.get(k, 0)}</td>" for k in STATES) + "</tr>"
        )
    tiles = "".join(
        f'<div class="tile"><b>{totals.get(k, 0)}</b><span>{STATES[k][0]}</span></div>'
        for k in STATES if totals.get(k)
    )
    head = "".join(f"<th>{STATES[k][0]}</th>" for k in STATES)
    return (
        f'<div class="tiles tiles-sm">{tiles}</div>'
        '<div class="tablewrap"><table><thead><tr><th>Site</th><th>Claims</th><th>Mix</th>'
        + head + "</tr></thead><tbody>" + "".join(per_site) + "</tbody></table></div>"
        + f'<p class="small dim">Synced {html.escape(str(data.get("synced", "")))} from each site\'s '
        "published claim index.</p>"
    )


def short_label(url):
    """A ledger row lists several pages; their full titles would each be a
    paragraph. The last path segment is what a reader recognises."""
    parts = [p for p in url.strip("/").split("/") if p]
    return html.escape(parts[-1] if parts else "the report")


def block_ledger(ctx):
    groups = {}
    for c in ctx["claims"]:
        groups.setdefault(c.get("group", "Other"), []).append(c)
    out = []
    for group, items in groups.items():
        out.append(f'<h3 id="{slugify(group)}">{html.escape(group)}</h3>')
        rows = []
        for c in items:
            used = sorted(ctx["claim_uses"].get(c["id"], set()), key=lambda u: ctx["page_urls"][u])
            links = ", ".join(
                f'<a href="{ctx["page_urls"][u]}" title="{html.escape(ctx["page_titles"][u])}">{short_label(ctx["page_urls"][u])}</a>'
                for u in used
            ) or '<span class="dim">&mdash;</span>'
            rows.append(
                f'<tr id="claim-{c["id"]}"><td>{inline(c["claim"], ctx)}</td>'
                f'<td>{chip(c["state"], c.get("date_label"))}</td>'
                f'<td class="small">{html.escape(str(c.get("source", "")))}</td>'
                f'<td class="small">{links}</td></tr>'
            )
        out.append(
            '<div class="tablewrap"><table class="ledger"><thead><tr><th>Claim</th><th>State</th>'
            "<th>How we know</th><th>Where it is said</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
        )
    counts = {}
    for c in ctx["claims"]:
        counts[c["state"]] = counts.get(c["state"], 0) + 1
    tiles = "".join(
        f'<div class="tile"><b>{counts.get(k, 0)}</b><span>{STATES[k][0]}</span></div>' for k in STATES if counts.get(k)
    )
    return f'<div class="tiles tiles-sm">{tiles}</div>' + "\n".join(out)


BLOCKS = {
    "comparison": block_comparison,
    "family": block_family,
    "evidence": block_evidence,
    "ledger": block_ledger,
}


# ------------------------------------------------------------------ shell ----


def rel_prefix(url):
    """How far a page sits below the site root: "" at /, "../" at /bench/."""
    depth = len([x for x in url.strip("/").split("/") if x])
    return "../" * depth


def relativise(doc, prefix):
    """Rewrite every root-absolute internal URL to one relative to this page.

    The site has to work wherever it is served from — the custom domain, a
    GitHub Pages project path (/<repo>/), a local directory, or inside a vault
    app frame, which has no origin at all. Root-absolute URLs work in exactly
    one of those, and the site spent its first deploy unstyled because of it.
    Directory URLs become explicit index.html so file:// works too.
    """

    def one(m):
        attr, target = m.group(1), m.group(2)
        path, _, frag = target.partition("#")
        path = path.lstrip("/")
        if path == "" or path.endswith("/"):
            path += "index.html"
        return f'{attr}="{prefix}{path}{"#" + frag if frag else ""}"'

    return re.sub(r'\b(href|src)="(/[^"]*)"', one, doc)


def nav_html(current):
    items = []
    for label, href, subs in NAV:
        here = href == current or any(s_href == current for _, s_href in subs)
        cls = "nl here" if here else "nl"
        if not subs:
            items.append(f'<div class="ni"><a class="{cls}" href="{href}">{html.escape(label)}</a></div>')
            continue
        sub = "".join(
            f'<a class="sl{" here" if s_href == current else ""}" href="{s_href}">{html.escape(s_label)}</a>'
            for s_label, s_href in subs
        )
        items.append(
            f'<div class="ni ni-has"><a class="{cls}" href="{href}">{html.escape(label)}'
            '<span class="caret">&#9662;</span></a>'
            f'<div class="sub">{sub}</div></div>'
        )
    return (
        '<nav class="site"><div class="row">'
        '<a class="brand" href="/">providers<span>.sgit.ai</span></a>'
        '<a class="parent" href="https://sgit.ai/vault/sg-bridge.html" rel="noopener" '
        'title="The window.sg bridge on sgit.ai — the host that would hold the key under pattern three, which is what this site is part of">'
        '&#8599; part of <b>sgit.ai</b></a>'
        '<span class="stage-pill">the index</span>'
        f'<a class="ver" href="/versions/" title="Site release history">{SITE["version"]}</a>'
        '<button class="nav-toggle" type="button" aria-expanded="false" aria-label="Menu">Menu</button>'
        '<div class="nav-items">' + "".join(items) + "</div>"
        '<a class="gh" href="https://github.com/SGit-AI/SGit-AI__Website__Providers" rel="noopener">&#9733; Source</a>'
        "</div></nav>"
    )


def footer_html():
    return f"""<footer class="site"><div class="cols">
  <div>
    <div class="brandline">providers<span>.sgit.ai</span></div>
    <p class="nonaff"><b>{NON_AFFILIATION}</b></p>
    <p>The index of the provider reports. This site holds no measurement of its own: every number
       on it is synced from the provider site that made it, and every table says which site and
       which version it came from.</p>
    <p class="licence">{LICENCE_STAMP} The code that builds it is Apache-2.0.</p>
    <p class="verline">site <a href="/versions/">{SITE['version']}</a> &middot; <a href="/evidence/">how the tables are made</a> &middot; <a href="/disclosures/">disclosures</a> &middot; <a href="index.md" title="The same page as plain markdown">this page as markdown</a></p>
  </div>
  <div>
    <h4>The argument</h4>
    <a href="/">Where the key goes</a>
    <a href="/patterns/">The four patterns</a>
    <a href="/comparison/">Comparison matrix</a>
    <a href="/contract/">What a provider site must publish</a>
  </div>
  <div>
    <h4>The family</h4>
    <a href="/sites/">Every provider site</a>
    <a href="/evidence/">Where these tables come from</a>
    <a href="/ledger/">The hub's own claims</a>
    <a href="/versions/">Versions</a>
    <a href="/disclosures/">Disclosures</a>
  </div>
  <div>
    <h4>The estate</h4>
    <a href="https://sgit.ai/why/" rel="noopener">Why sgit exists</a>
    <a href="https://sgit.ai/vault/sg-bridge.html" rel="noopener">The host bridge (pattern three)</a>
    <a href="https://open-source.sgit.ai/practice/" rel="noopener">Two licences, three layers</a>
    <a href="https://github.com/SGit-AI/SGit-AI__Website__Providers" rel="noopener">This site's source</a>
  </div>
</div>
<div class="footnote"><p>No analytics. No cookies. No third-party fonts, scripts or CDN &mdash; every byte of this site
is served from this domain. This site makes no API call at all: it has no key bar and no lab. The labs live on the
provider sites, where the key is.</p></div>
</footer>"""


def page_html(page, ctx, body):
    fm = page["fm"]
    desc = fm.get("description", "")
    prov = fm.get("provenance", {}) or {}
    toc = ""
    if fm.get("toc") and len(ctx["toc"]) > 2:
        links = "".join(
            f'<a class="lv{lv}" href="#{anchor}">{html.escape(text)}</a>' for lv, anchor, text in ctx["toc"] if lv == 2
        )
        toc = f'<aside class="toc"><b>On this page</b>{links}</aside>'
    provline = ""
    if prov:
        provline = (
            f'<p class="prov">Prose from the video vault at commit <code>{html.escape(str(prov.get("commit", SITE["vault_commit"])))}</code>, '
            f'{html.escape(str(prov.get("date", "")))}. '
            f'{html.escape(str(prov.get("note", "")))} '
            f'When the vault moves ahead, this page is behind &mdash; and says so rather than guessing.</p>'
        )
    prefix = rel_prefix(page["url"])
    lab = ' data-lab="1"' if fm.get("kind") == "experiment" or fm.get("app") else ""
    # lab.js is NOT deferred: each lab's own inline <script> runs during parse and
    # needs window.EL to exist by then. It is 12 KB, same-origin, and uncached only once.
    scripts = '<script src="/assets/lab.js"></script>' if lab else '<script src="/assets/site.js" defer></script>'
    return relativise(f"""<!doctype html>
<html lang="en" data-root="{prefix}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(fm['title'])} &mdash; {html.escape(SITE['title'])}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{SITE['base']}{page['url']}">
<meta property="og:type" content="{'website' if page['url'] == '/' else 'article'}">
<meta property="og:site_name" content="{SITE['domain']}">
<meta property="og:url" content="{SITE['base']}{page['url']}">
<meta property="og:title" content="{html.escape(fm['title'])}">
<meta property="og:description" content="{html.escape(desc)}">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="text/markdown" href="index.md" title="This page as markdown">
<link rel="stylesheet" href="/assets/site.css">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
{scripts}
</head>
<body{lab}>
{nav_html(page['nav_match'])}
<div class="disclosure-strip"><div class="row"><b>Independent.</b> No commercial relationship with any provider
indexed here &mdash; no credits, no programme, no agreement &mdash; checked 8 September 2026.
<a href="/disclosures/">Disclosures</a> &middot; <a href="/evidence/">how every number here is evidenced</a></div></div>
<main class="doc{' doc-wide' if fm.get('wide') else ''}">
<p class="crumb"><a href="/">providers.sgit.ai</a>{page['crumb']}</p>
<h1>{html.escape(fm['title'])}</h1>
{f'<p class="lead">{inline(fm["lead"], ctx)}</p>' if fm.get('lead') else ''}
{provline}
{toc}
{body}
<p class="pagenav"><a href="/ledger/">Every claim on this site, with its state &rarr;</a>
<a href="/disclosures/">Disclosures &rarr;</a></p>
</main>
{footer_html()}
</body>
</html>
""", prefix)


# ------------------------------------------------------------------ build ----


def read_page(path):
    text = path.read_text()
    if not text.startswith("---"):
        raise SystemExit(f"build: {path} has no front-matter")
    _, fm_text, body = text.split("---", 2)
    fm = yaml_load(fm_text)
    rel = path.relative_to(CONTENT)
    slug = str(rel.with_suffix("")).replace("index", "").strip("/")
    url = "/" + (slug + "/" if slug else "")
    return {"path": path, "fm": fm, "body": body.lstrip("\n"), "url": url, "src_md": text}


def build(out_dir):
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    claims = yaml_load((DATA / "claims.yml").read_text())
    for c in claims:
        c["date_label"] = c.get("date", "")
    claims_by_id = {c["id"]: c for c in claims}

    pages = sorted((read_page(p) for p in CONTENT.rglob("*.md")), key=lambda p: (p["fm"].get("order", 500), p["url"]))
    page_urls = {p["path"].name: p["url"] for p in pages}
    page_urls = {str(p["path"]): p["url"] for p in pages}
    page_titles = {str(p["path"]): p["fm"]["title"] for p in pages}

    ctx_shared = {
        "claims": claims,
        "claims_by_id": claims_by_id,
        "claim_uses": {},
        "pages": pages,
        "page_urls": page_urls,
        "page_titles": page_titles,
        "external_links": set(),
    }

    # two passes: the first collects claim usage so the ledger can join on it.
    for _ in range(2):
        rendered = {}
        for page in pages:
            fm = page["fm"]
            crumbs = ""
            if page["url"] != "/":
                parts = [x for x in page["url"].strip("/").split("/") if x]
                parent = "/" + parts[0] + "/"
                if len(parts) > 1 and any(q["url"] == parent for q in pages):
                    crumbs = ' / <a href="' + parent + '">' + parts[0] + "</a>"
                elif len(parts) > 1:
                    crumbs = " / " + parts[0]
                crumbs += f" / {html.escape(fm['title'])}"
            page["crumb"] = crumbs
            page["nav_match"] = "/" + (page["url"].strip("/").split("/")[0] + "/" if page["url"] != "/" else "")
            ctx = dict(ctx_shared)
            ctx.update({"page": str(page["path"]), "page_url": page["url"], "fm": fm, "toc": []})
            body = render_markdown(page["body"], ctx)
            rendered[page["url"]] = (page, ctx, body)

    for url, (page, ctx, body) in rendered.items():
        target = out_dir / url.strip("/") / "index.html" if url != "/" else out_dir / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_html(page, ctx, body))
        twin = page["src_md"].rstrip("\n")
        if LICENCE_STAMP not in twin:
            twin += f"\n\n---\n\n{LICENCE_STAMP}\n"
        (target.parent / "index.md").write_text(twin)

    # static assets, verbatim
    shutil.copytree(ASSETS, out_dir / "assets")
    # The hub carries no downloadable examples and no brief pack of its own; both
    # trees stay optional so adding one later needs no change here.
    if FILES.is_dir():
        shutil.copytree(FILES, out_dir / "files")
    if BRIEFS.is_dir():
        for src in sorted(BRIEFS.rglob("*")):
            if src.is_file():
                dst = out_dir / "briefs" / src.relative_to(BRIEFS)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    (out_dir / "CNAME").write_text(SITE["domain"] + "\n")
    (out_dir / ".nojekyll").write_text("")
    (out_dir / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['base']}/sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE['base']}{u}</loc></url>" for u in sorted(rendered))
    (out_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>\n"
    )
    (out_dir / "assets" / "site-index.json").write_text(site_index(rendered, claims))
    (out_dir / "llms.txt").write_text(llms_txt(rendered))
    (out_dir / "llms-full.txt").write_text(llms_full(rendered))
    print(f"build: {len(rendered)} pages, {len(claims)} claims → {out_dir}")
    unused = [c["id"] for c in claims if c["id"] not in ctx_shared["claim_uses"]]
    if unused:
        print("build: claims in the ledger that no page cites: " + ", ".join(unused))
    return rendered


def site_index(rendered, claims):
    """What the ask pane matches against. Built here rather than fetched from
    anywhere: the pane's default tier answers with no key and no network call
    beyond this file, which is the only way it can be honest about tier one."""
    import json

    pages = []
    for url, (page, ctx, body) in sorted(rendered.items()):
        fm = page["fm"]
        headings = [text for lv, _a, text in ctx["toc"]]
        pages.append({
            "url": url,
            "title": fm["title"],
            "description": fm.get("description", ""),
            "lead": re.sub(r"<[^>]+>", "", inline(fm.get("lead", ""), ctx)),
            "headings": headings,
            "kind": fm.get("kind", "page"),
        })
    return json.dumps({
        "version": SITE["version"],
        "built": "8 September 2026",
        "pages": pages,
        "claims": [
            {"id": c["id"], "state": c["state"], "date": c.get("date", ""),
             "claim": re.sub(r"[*`]", "", c["claim"])}
            for c in claims
        ],
    }, indent=1)


def llms_txt(rendered):
    lines = [
        f"# {SITE['domain']}",
        f"> site {SITE['version']}",
        "",
        "> The index of a family of independent provider reports, organised around one question:",
        "> where does the API credential live, and what bounds it. Four client-side credential",
        "> patterns, a site per provider, and every number synced from the site that measured it.",
        "> Not affiliated with, endorsed by, or sponsored by any provider indexed here.",
        "",
        "This hub runs no API and makes no measurement of its own. Its comparison tables are",
        "generated from each provider site's own published markdown and claim index; the",
        "sync date and each site's version are printed beside the tables. See /evidence/.",
        "",
        "Every factual claim this hub makes itself carries one of six states: verified, measured,",
        "vendor docs, specified-not-shipped, written-not-run, projected. The list is at /ledger/.",
        "Every page is also served as markdown at <page>/index.md.",
        f"Licence: {LICENCE_STAMP}",
        "",
        "## Pages",
    ]
    for url, (page, _ctx, _body) in sorted(rendered.items()):
        lines.append(f"- [{page['fm']['title']}]({SITE['base']}{url}): {page['fm'].get('description', '')}")
    return "\n".join(lines) + "\n"


def llms_full(rendered):
    """The whole site as one markdown document. The estate ships one of these
    beside llms.txt so an agent can read the site without crawling it — and here it
    costs nothing, because markdown is already the source of truth."""
    parts = [
        f"# {SITE['domain']} — the whole site as markdown",
        f"site {SITE['version']} · source vault commit {SITE['vault_commit']} · "
        "every claim's verification state is at /ledger/",
        "",
        "Independent work by SGit-AI. Not affiliated with, endorsed by, or sponsored by any "
        "provider indexed here. Provider names identify the APIs these pages report on; all "
        "trademarks belong to their owners.",
        "",
        LICENCE_STAMP,
        "",
    ]
    for url, (page, _ctx, _body) in sorted(rendered.items()):
        parts += [
            "\n" + "=" * 78,
            f"PAGE {url}  —  {page['fm']['title']}",
            "=" * 78 + "\n",
            page["src_md"].strip(),
        ]
    return "\n".join(parts) + "\n"


def main():
    if "--check" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "docs"
            build(target)
            diff = dircmp_report(target, OUT)
            if diff:
                print("build --check: docs/ is stale. Run `python3 build.py` and commit.", file=sys.stderr)
                for d in diff[:40]:
                    print("  " + d, file=sys.stderr)
                sys.exit(1)
            print("build --check: docs/ matches the sources.")
        return
    build(OUT)


def dircmp_report(a, b, prefix=""):
    out = []
    cmp = filecmp.dircmp(str(a), str(b))
    out += [f"only in build: {prefix}{x}" for x in cmp.left_only]
    out += [f"only in docs/: {prefix}{x}" for x in cmp.right_only]
    out += [f"differs: {prefix}{x}" for x in cmp.diff_files]
    for sub in cmp.common_dirs:
        out += dircmp_report(Path(a) / sub, Path(b) / sub, prefix + sub + "/")
    return out


if __name__ == "__main__":
    main()
