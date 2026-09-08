---
title: Where the key goes — provider reports for people who have to deploy one
description: "The hub of the *.providers.sgit.ai family: four credential patterns, one page contract, and one site per provider reporting what it cost on a named workload, what broke, and where the key has to live."
lead: "One question decides most integrations and almost nobody writes it down: **where does the credential live, and what bounds it.** This is the hub for a family of sites that answer it one provider at a time — with dates, costs and failures attached."
order: 1
toc: true
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
  note: "The four patterns come from the source vault; everything about a provider comes from that provider's own site."
---

<div class="warnbox"><p><b>Neither domain in this family resolves yet.</b> {{claim:domains-unconfigured}} <code>providers.sgit.ai</code> and <code>elevenlabs.providers.sgit.ai</code> are not yet pointed at their repositories, so both sites serve from their GitHub Pages project paths — and every link here goes to where a site <em>actually is</em> rather than where it will be. A build check fails if one points at a canonical domain instead, because a hub whose links are all dead is worse than no hub.</p></div>

## The argument, in one paragraph

Vendor documentation tells you what an API does. It does not tell you **what it cost on a named workload on a named date**, **what broke**, or **which credential patterns the product can actually support** — and the third one is the question that decides your architecture. A site in this family exists to answer those three, per provider, with every claim carrying the state that says how far it can be trusted.

The strongest form of the answer is a pattern rather than a rule: *a browser application can use a paid API without ever holding the key, because a host holds it and enforces the terms.* That is [pattern three](/patterns/), it is [specified and not shipped](/contract/) {{claim:sg-tts-spec}}, and saying so is the point.

## The family

{{family}}

## The two axes

Everything in this family is indexed on two questions that are usually mixed together. They are orthogonal, and the intersection is [on the patterns page](/patterns/).

<div class="beforeafter"><div class="ba now"><h4>The credential pattern — a property of the <em>provider</em></h4><p>Where the credential lives and what bounds it: <b>nothing</b>, <b>a spend limit</b>, <b>a clock</b>, or <b>a host the application cannot reach</b>. It is decided by what the vendor's product can mint, and no amount of care in your code changes it.</p><p><a href="/patterns/">The four patterns &rarr;</a></p></div><div class="ba then"><h4>The capability tier — a property of <em>your tool</em></h4><p>What state it keeps: <b>none</b>, <b>this device</b>, or <b>a vault</b>. It decides whether your tool works for somebody with no key, and whether it survives being downloaded and run somewhere else.</p><p><a href="/patterns/#the-second-axis-what-the-tool-keeps">The tier axis &rarr;</a></p></div></div>

## What makes this different from a review site

**Nothing here is replaceable by a link to the vendor.** If a section could be, it should be deleted — the vendor's own documentation is better and stays fresher.

**Every claim carries a state.** Six of them, from *verified by execution on this date* to *specified and not shipped*, joined to the pages that make them at build time. A claim that appears on a page and not in a ledger fails the build. [How that works, and the current mix across the family →](/evidence/)

**The failures are published.** Including our own: the first render in this family broke four times before it made a sound, and [one of the four was our bug rather than the vendor's](https://sgit-ai.github.io/SGit-AI__Website__Provider__ElevenLabs/video/).

**And there is no commercial relationship with anybody.** [None](/disclosures/), checked and dated, with the page built before there was anything to disclose so that its later appearance cannot be read as a signal.

## The one measurement worth reading first

<div class="fails"><div class="fail ok"><p class="who">3 September 2026 · OpenRouter</p><h3>A 402 that was the point, not an outage</h3><p>At <b>$4.79 used against a $5.00 limit</b> on a provisioned key, every audio request was refused: <code>402 — this request requires at least $0.50 in balance for audio output</code>, with <code>limit_source: openrouter_key_limit</code>. {{claim:openrouter-402}}</p><p>That is a bound doing its job, observed rather than described: chosen in advance, enforced by the platform rather than by our code, and visible in the refusal. <b>It is the only evidence in this family that any of this is enforceable in practice</b> — and the reason the comparison is worth generating, because the other provider here cannot do it at all {{claim:no-per-key-spend-limit}}.</p></div></div>

---

This document is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0).
