# Handback — providers.sgit.ai v0.1.0

What was built, what is verified, and the four things that need a human.

## What this is

The hub for the `*.providers.sgit.ai` family: nine pages holding the material that is
*shared* across provider reports — the four credential patterns, the capability-tier axis,
the claim-state model, the page contract, and the comparison tables. It deliberately holds
no measurement of its own.

| Page | What it is for |
|---|---|
| `/` | The argument in one paragraph, the family, the two axes, and the one measurement worth reading first |
| `/patterns/` | The four credential patterns × three capability tiers, with the empty corner named |
| `/comparison/` | Provider × pattern, synced from the provider sites |
| `/sites/` | Every site in the family, what it costs to add one, and what each site owes |
| `/contract/` | What a site must publish to be in this family — the checklist the gate enforces |
| `/evidence/` | The six claim states, and the family's current mix |
| `/ledger/` | The hub's own six claims |
| `/disclosures/` | Commercial relationships (there are none), and how that is kept true |
| `/versions/` | Release history |

## Verified before handing back

```
admin/build/validate.sh
── 1/4  build      build --check: docs/ matches the sources
── 2/4  site gate  check_site: 9 pages pass every acceptance assertion
── 3/4  secrets    secret-scan: clean (10 patterns, whole tree including docs/)
── 4/4  scripts    check-js: all scripts parse
validate: OK — v0.1.0 on providers.sgit.ai
```

Two checks are specific to this repository and worth knowing about:

- **`check_family_links_live`** fails the build if any page links a provider by a canonical
  domain that does not resolve. Because neither domain is pointed yet, every family link
  goes to the GitHub Pages project path where the site actually serves.
- **`check_four_patterns`** is the hub's equivalent of the provider sites' nine-section
  check: all four patterns present, in order, on the page that is canonical for them.

## The sync, and why the build is offline

`bin/sync-providers.py` fetches two artefacts each provider site already publishes for its
own purposes — the markdown twin of its report (for the `patterns:` front-matter block) and
its claim index (for the state counts) — and writes `data/providers.yml`. The build reads
that file and makes no network call at all, so a release cannot fail because somebody
else's site is down, and a stale table is *visible* (the sync date is printed under it)
rather than guessed at.

`bin/sync-providers.py --check` reports drift without changing anything. It is deliberately
not wired into CI: a sync is a dated act, and CI silently refreshing it would defeat the point.

Last sync: **2026-09-08**, against ElevenLabs at site v0.3.0.

## Four things that need a human

1. **DNS.** Neither `providers.sgit.ai` nor `elevenlabs.providers.sgit.ai` is pointed at its
   repository. `docs/CNAME` already carries the intended host for each site, and both sites
   are built entirely with page-relative URLs (enforced by `check_relative_urls`), so
   pointing the DNS is the only remaining step — nothing in either repository changes.
2. **GitHub Pages source.** Set Pages to *GitHub Actions* for this repository. The workflow
   passes `enablement: true`, which usually suffices, but the first deploy is worth watching.
3. **The second provider.** OpenRouter is in `data/providers.yml` as `planned`, with its
   pattern-one capability recorded from the ElevenLabs site's stub. Building it is what will
   actually test the claim in `/sites/` — that adding a provider needs a repository, a
   `patterns:` block and a sync, and no edit to this hub's pages.
4. **The empty corner.** Pattern three has no working tool anywhere in the family. `/patterns/`
   says so rather than avoiding it; when `sg.tts` ships, that cell changes state on the
   provider site and the hub picks it up on the next sync.

## Licence

Content CC BY 4.0, stamped in the footer, in every markdown twin and in both machine-readable
indexes. Code Apache-2.0. Both are checked by the gate.
