---
title: Comparison — provider × pattern
description: "One row per provider and product, one column per credential pattern, synced from each provider site's own published front-matter rather than kept here."
lead: "One row per provider and product, one column per pattern. **This hub keeps no opinion of its own**: every row is copied from that provider's site at sync time, so a wrong row is wrong on the provider's own page first — which is where a correction belongs."
order: 20
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
---

{{comparison}}

## How this table is made

Each provider site publishes two things for its own purposes: **the markdown twin of its report**, which carries a `patterns:` block in its front-matter, and **the claim index** its own search pane matches against. `bin/sync-providers.py` reads both and writes `data/providers.yml`; the build reads that file and never touches the network.

That is deliberate in three ways:

- **A sync is a dated act.** The date is printed under the table, and CI does not silently refresh it. If the data is stale, the staleness is visible rather than guessed at.
- **The build is reproducible and offline.** A site whose build depends on the network is a site that breaks when somebody else deploys.
- **There is one source of truth per fact, and it is not here.** A hub that maintains its own table of other people's properties will drift from them, and it will be the hub that is wrong.

`bin/sync-providers.py --check` reports drift without changing anything, which is the form CI could take if this ever needs to be automatic.

## Reading down the columns

**Column 0 is the same everywhere:** possible, and never acceptable. It is in the table because "the browser can call it" is what people usually mean by client-side, and CORS permitting a call says nothing about whether the credential is bounded.

**Column 1 is where providers part company.** One in this family can mint a key with a spend limit and a reset {{claim:openrouter-402}}; the other cannot, at any price {{claim:no-per-key-spend-limit}}. That is not a difference of degree, and it is the single most useful thing this table shows.

**Column 2 needs a server, and the question is whose.** "Available with a server" and "available" are not the same claim; the last column says which.

**Column 3 is the one this estate can extend to any provider** by adding a verb to the host bridge and a terms file to the vault. It is shipped for a model router and specified for a voice API {{claim:sg-tts-spec}} — and until it ships, the column is a plan rather than a product.
