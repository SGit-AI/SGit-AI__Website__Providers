---
title: The four client-side credential patterns
description: "Client side is not one thing. It is four patterns that differ in where the credential lives and what bounds it — plus a second axis, what your tool keeps, and the intersection of the two."
lead: "\"Client side\" is not one thing. It is four patterns, and they differ in exactly two ways: **where the credential lives**, and **what bounds it**. Every provider site in this family answers with one of these, per product, because a vendor with several products has several answers."
order: 10
toc: true
provenance:
  commit: 7d1916aca5f3
  date: 8 September 2026
  note: "Canonical here. A provider site answers these rather than redefining them."
---

## The four

{{claim:patterns-canonical}}

| # | Pattern | Where the credential lives | What bounds it | Verdict |
|---|---|---|---|---|
| **0** | **Key in the page** | In the delivered application | **Nothing** | **Never.** Anybody who opens the page has the key and the account. A plan quota is a ceiling, not a bound: it belongs to the whole account |
| **1** | **Bounded key** in the page | In the page, provisioned per user with a spending limit and a reset | **Money, and a reset window** | Acceptable where the platform can mint one. The limit *is* the blast radius, so choosing the number is a risk decision rather than a default |
| **2** | **Short-lived token** | Not in the page. A server exchanges the real key for a token with a short life | **Time, and the server's policy** | The standard answer — and it needs a server: the vendor's, if it offers one for that product, otherwise yours |
| **3** | **Host holds the key** | Never in the application. The application asks a host, which holds the key and enforces the terms | **The host, which the application cannot reach** | The strongest, and this estate's own: the only pattern where the bounded thing cannot reach the bounding thing |

**The ladder is not a maturity model.** Pattern 1 with a $5 limit can be a better answer than pattern 2 with a badly-scoped minter. The question is always *what is the blast radius, and who chose it.*

## Why pattern three is different in kind

Patterns 0 to 2 all end with a credential in the hands of the code that spends it — for a moment in pattern 2, for good in pattern 0. Pattern 3 does not: the application asks for a **result**, and the host holds the credential, applies the terms, and returns only the output.

In this estate the vault host already does that for a model call: the app frame never sees the key and cannot read the sealed config under any grant it can be given, and the terms — allowed models, spend cap per session, per-app overrides — live in the vault with the content they govern. **The terms travel with the data**, so a vault shared read-only carries neither the key nor the ability to spend against it.

Whether that generalises past a model call is the open question this family exists to answer. For a voice API the answer is written down and not yet built {{claim:sg-tts-spec}}.

## The second axis: what the tool keeps

The four patterns are a property of **the provider**. There is a second axis and it is a property of **your tool**: what state it keeps. It decides whether the tool works for somebody with no key at all, and whether it survives being downloaded and run somewhere else.

| Tier | What it keeps | Works with no key? | Survives being downloaded? |
|---|---|---|---|
| **1** | Nothing. A pure function in a page | **Yes** | Yes, completely |
| **2** | This browser's `localStorage`, on this device | No | Yes, and it carries no key with it |
| **3** | A vault, which holds the key the page never sees | Yes — the *vault* holds it | **No.** A vault app's calls fail on a static host, because the key is sealed to its owner |

**The intersection is one sentence:** a tier-two tool holding a key in `localStorage` is **pattern 0 with a ceiling**, and a tier-three tool is **pattern 3**. Said once, the two axes stop competing to explain the same thing.

**And the honest finding is the empty corner.** Across this family, tier three has no working tool: the pattern the argument recommends is the one it has not yet demonstrated. That is a state the ledger has a word for, and the pages use it rather than avoiding the subject.

## What this means for a reader who has to ship

Three questions, in order, and the provider sites answer them per product:

1. **Can the vendor mint a bounded credential for the product I am using?** If yes, pattern 1 is available and the limit is your blast radius. If no, no amount of care in the page changes it.
2. **Does the vendor run a minter for that product?** Some do, for some products, and it is easy to read a rule written for one product as a rule for the vendor. [That mistake has already been made once in this family and corrected in public.](/contract/)
3. **Is there a host that can hold the key for you?** If there is, nothing else on this page matters. If there is not, you are choosing between 1 and 2 and the answer is a risk decision, not a technical one.

[Which provider can do what →](/comparison/)

---

This document is released under the Creative Commons Attribution 4.0 International licence (CC BY 4.0).
