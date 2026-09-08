---
title: Release history
description: "Every release of this site, with what changed. The version is owned by admin/build/version.txt, must appear in the release commit's subject, and CI verifies the two agree before it tags anything."
lead: "Every release of this hub, with what changed and when. The estate's convention: **one file owns the version**, the release commit's subject repeats it, and the pipeline refuses to tag anything if the two disagree."
order: 95
---

<div class="tablewrap"><table class="vers"><thead><tr><th>Version</th><th>Date</th><th>What changed</th></tr></thead><tbody>
<!-- releases -->
    <tr><td class="vnum">v0.1.0</td><td>2026-09-08</td><td>First release. The hub of the *.providers.sgit.ai family: the four credential patterns as canonical shared content with the capability-tier axis and their intersection; a comparison matrix synced from each provider site's own published front-matter rather than kept here; the family index; the page contract every provider site obeys, including the per-product rule that has already caught somebody; the six claim states with a roll-up of the family's actual mix; estate-wide disclosures; and the estate pipeline — validate → tag → deploy, a secret scan, relative URLs and a licence stamp, all enforced rather than promised.</td></tr>
</tbody></table></div>

## How a release is made here

The same three steps as every other site in this estate — `validate` → `tag-release` → `deploy`.

**One file owns the version:** `admin/build/version.txt`. The nav badge, the footer, `llms.txt` and the table above are all rendered from it, and the gate fails if any of them disagree.

```bash
bin/bump.py "what changed in this release"     # --major for vR.M+1.0
python3 build.py
admin/build/validate.sh
git commit -am "site v0.1.1: what changed in this release"
```

**The commit subject is load-bearing.** `tag-release` reads `version.txt`, finds the commit whose *subject* carries the same version, and tags it — HEAD on a direct push, HEAD's parent when a pull request lands as a merge.

## The sync is not part of the build

`bin/sync-providers.py` refreshes `data/providers.yml` from the provider sites. **It is never run by CI**, because a build that reaches the network is a build that breaks when somebody else deploys, and because a sync should be a dated act rather than a silent one. `--check` reports drift without changing anything.

---

This document is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0).
