---
title: Evidence — the six states, and the family's mix
description: "Every claim on every site in this family carries one of six verification states. Here is what each means, why the model exists, and how much of the family is actually verified rather than read in a vendor's documentation."
lead: "**No claim without a state.** Six of them, joined to the pages that make them at build time, so a claim cannot appear on a page without appearing in a ledger. This page says what they mean — and rolls up how much of the family is actually verified."
order: 50
toc: true
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
---

## The six states

| Chip | Means | What you may do with it |
|---|---|---|
| {{badge:verified}} | Somebody ran it and watched it work, on that date, in a named place | Treat as fact for that date and that setup |
| {{badge:measured}} | Our own pipeline produced this number on a named workload | Treat as fact about *our* workload; yours will differ |
| {{badge:docs}} | Read in the vendor's documentation on that date; never executed by us | Check it against the vendor before relying on it — and tell us if it moved |
| {{badge:spec}} | A written specification for something that does not exist | Never plan around it. Future tense only |
| {{badge:unrun}} | Code we wrote and have never executed | Read it, then run it and find out. Expect it to be wrong somewhere |
| {{badge:projected}} | Arithmetic, with its workings shown | Re-do the arithmetic with your own numbers |

## Why a model rather than a disclaimer

Because the alternative is a page that is *mostly* true and gives you no way to tell which parts.

The first site in this family was written by a machine that **could not reach the API it was documenting**. A small, specific set of things was verified in a browser by a human; everything else was read from the vendor's reference. A disclaimer at the top would have covered both and distinguished neither. Six states, attached per sentence and joined to a table, mean a reader can see exactly which half they are standing on.

**It also changes what a correction is.** When that site's first render finally ran, four claims changed state in one afternoon and two predictions turned out wrong. With a ledger, that is a dated row moving from `written, not run` to `verified` — visible, checkable, and worth publishing. Without one, it is a paragraph quietly rewritten.

## The mix, across the family

{{evidence}}

**Read the `docs` column as the honest debt.** Those are facts taken from a vendor's own documentation and never executed by anybody here — true when read, on the date shown, and the first thing to check if something behaves oddly. **Read `unrun` as the invitation:** code published so somebody can run it, badged so nobody mistakes it for tested.

**And read `verified` narrowly.** It means somebody watched it work once, in one place, on one account tier. The most-cited verified claim in this family — that a provider's alignment matches its audio to the millisecond — was measured on nine files on a free-tier key in one afternoon. That is enormously better than a guess, and it is not a guarantee.

## Where the claims live

Each provider site keeps its own ledger, publishes it as a page, and publishes a machine-readable index of it that this hub syncs. **The hub does not hold a copy of anybody's claims** — the counts above are read from those indexes at sync time {{claim:family-live}}, and the links go to the ledgers themselves.
