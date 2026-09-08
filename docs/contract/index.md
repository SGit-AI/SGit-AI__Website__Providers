---
title: The contract — what a provider site owes
description: "The nine fixed sections, the six claim states, the composition rules and the build discipline that every site in this family obeys, so that a second provider is a Markdown file rather than a rewrite."
lead: "The reason a comparison across these sites means anything is that they are not free to answer different questions. This is the contract: **nine sections, six states, and a short list of things that are build failures rather than review comments.**"
order: 40
toc: true
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
  note: "The nine sections come from the source vault's TEMPLATE.md; everything else was learned by building the first site."
---

## 1 · The nine sections, fixed

Not added to, not reordered, not merged. A provider page that skips §9 is the thing this family exists not to be.

| # | Section | What it is for |
|---|---|---|
| 1 | **Disclosure** | One line: commercial relationship, or none, with the date it was checked |
| 2 | **What it grants** | The capability block — verb × object class × reach, reversibility marked — in two layers: what the platform can grant per product, and what *your* scoped key grants |
| 3 | **Which pattern** | Which of [the four](/patterns/) this provider supports and which it forbids, **per product** |
| 4 | **Where the key goes** | The exact mechanism, quoted with the product it belongs to, the URL and the date read |
| 5 | **The bounding primitive** | What caps the blast radius — and what it does **not** cap |
| 6 | **The minimal working example** | The smallest thing that runs, as a file rather than a snippet |
| 7 | **What we use it for** | Named workloads, so the page is a report rather than a tutorial |
| 8 | **What it cost** | Date, workload size, model, request count, price. These go stale fastest |
| 9 | **What went wrong** | The failures, the limits hit, the surprises. **The section nobody else writes** |

**Sections 8 and 9 get the visual weight.** If a reader takes one screenshot from a provider site, it should be §9.

## 2 · The rule that has already caught somebody

**Credential rules are stated per product, never per vendor.**

The first site in this family had to correct its own source brief on exactly this: a "never expose your key client-side" rule, a 15-minute signed URL and a hostname allowlist were quoted as the vendor's rules when they belong to one of that vendor's products. The endpoint actually in use has none of those mechanisms. Quoting the wrong product's rule would have sent a reader off to build a signed-URL minter for an endpoint that does not accept one.

So: **every quote carries the product it belongs to, the URL, and the date it was read.** The correction is published on the site rather than quietly applied, because a site that corrects itself in public is the only kind whose uncorrected claims are worth anything.

## 3 · The six claim states

{{evidence}}

Every factual claim on every site in this family carries one of these, and the join is done at build time: **a claim that appears on a page and not in that site's ledger fails the build.** [More on why, and what the states mean →](/evidence/)

## 4 · Composition rules

- **A cross-link points at the page that answers the question**, never at a domain. A domain link is a referral rather than a composition, and it is this family's one recorded defect.
- **Every page is served as markdown at the same path**, so an agent never has to parse HTML and never has to leave the markdown surface once it arrives.
- **Machine-readable where it is cheap**: `llms.txt`, `llms-full.txt`, and a claim index each site publishes for its own search. This hub syncs from those rather than from anything bespoke.
- **The canonical URL is the intent, the link is the reality.** While a domain is unconfigured, links go where the site actually serves {{claim:domains-unconfigured}} and the page says so.

## 5 · What is a build failure rather than a review comment

Learned by building the first site, and each one is enforced by a check rather than remembered:

| Check | Why it exists |
|---|---|
| The build is **reproducible** — the committed output matches the sources | Markdown is the source of truth; a stale build publishes prose nobody wrote |
| **Version agreement** across every page badge, the release history and both machine indexes | A blanket bump that misses a page ships two versions of one site |
| **Internal links resolve**, and every canonical URL is on the host in `CNAME` | The two ways a static site quietly breaks |
| **No root-absolute internal URL** | The first site shipped one and served unstyled under a project path for a day |
| **No bare `<https://…>` autolink** | It reaches the browser as an unknown tag and the URL vanishes from the page |
| **A key-shape scan** over the whole tree, including the built output | These repositories are public; the vaults they came from were not |
| **Every claim cited**, and every state dated | The contract, enforced instead of promised |
| **The disclosure line present** on every page, and no vendor described as a collaborator it is not | A disclosure found at the bottom does the opposite of its job |

## 6 · The release discipline

The same as every other site in this estate: **validate → tag → deploy**, in that order, with a failure at any stage stopping the release. One file owns the version, the release commit's subject repeats it, and CI refuses to tag if the two disagree. Every push to the release branch is a minor.

That is not ceremony. It is what makes "as of v0.2.1, this claim was verified" a statement somebody can check a year later.

---

This document is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0).
