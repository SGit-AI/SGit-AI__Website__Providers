---
title: The hub's own claim ledger
description: "This hub reports on other sites, so it makes few claims of its own — but the ones it makes are held to the same rule as the sites it indexes: every claim carries a state, a date and a source, and a claim that appears on a page and not in this table fails the build."
lead: "**Six claims, because a hub should not have many.** The measurements belong to the provider sites; what is left here is what the hub itself asserts — about the family, the domains, and the synced tables. Each row says how we know."
order: 55
toc: true
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
---

## Why this table is short

A provider site earns its claims by running the API: it has a ledger of dozens of rows because it
has dozens of measurements. This hub runs nothing. It has exactly the claims it needs to describe
the family and the sync, and no more — and where it repeats a provider's finding, the row names the
site that measured it rather than restating it as the hub's own work.

That is the same rule the [contract](/contract/) puts on every site in the family, applied here first.
[What the six states mean →](/evidence/)

{{ledger}}

## What is not in this table

Everything the provider sites measured. The counts on the [comparison matrix](/comparison/) and on
[the sites page](/sites/) are read from each site's published index at sync time, and the state chips
there link into **that site's** ledger, not this one. The hub does not hold a second copy of anybody's
claims, because a copy is a thing that can drift. [How the sync works →](/evidence/)
