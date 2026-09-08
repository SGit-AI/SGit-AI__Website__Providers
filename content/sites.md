---
title: The provider sites
description: "One site per provider, each answering the same nine sections about a different API. What is live, what is planned, and what adding one actually takes."
lead: "One site per provider, each answering **the same questions about a different API**. The point of a family rather than one big site is that the questions stay fixed while the answers vary — which is the only way the comparison means anything."
order: 30
toc: true
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
---

{{family}}

## Why one site per provider rather than one page each

A page per provider on one site drifts into a feature grid: the same six headings, filled in with whatever the vendor's marketing says, and no room for the part that matters. A **site** per provider has room for the part that matters — the labs, the examples, the failures, the cost table, the ledger — and it forces the shared material out into a hub, which is this.

The split is:

| Lives here | Lives on the provider site |
|---|---|
| The four credential patterns, and the tier axis | Which of them **this** provider supports, per product |
| The claim-state model, and the family roll-up | That site's own ledger, every claim with its date |
| The comparison across providers | The cost table, the failures, the workloads |
| Disclosures, estate-wide | The disclosure line for that provider, at the top of every page |
| The page contract every site obeys | Everything the contract asks for |

## What adding a provider actually takes

The ElevenLabs site proved this by carrying a stub of the next one: **a provider page is one Markdown file with front-matter**, and the comparison follows from it. At the hub level, adding a site to this family is:

1. **A repository**, from the same template — the build system, the gate and the release pipeline are the same files.
2. **A `patterns:` block** in its report's front-matter, per product. That is what this hub syncs.
3. **A row in `data/providers.yml`**, added by running `bin/sync-providers.py` rather than typed.

**No template surgery, and no edit to the comparison page.** If adding the second provider requires either, the contract is wrong and the fix belongs in the contract rather than in the page.

## What each site owes

The short version — [the long version is the contract](/contract/):

- **Nine sections, in order**, with cost and failures given the visual weight.
- **No claim without a state**, and the states joined to the pages at build time.
- **Credential rules per product**, never per vendor.
- **Disclosure visible without scrolling**, on every page, not only on its own page.
- **A markdown twin at every path**, so an agent never has to parse HTML.
- **Cross-links that point at pages**, never at domains — a domain link is a referral rather than a composition.
