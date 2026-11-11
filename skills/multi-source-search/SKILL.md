---
name: multi-source-search
description: "Run several differently-phrased searches in parallel, deduplicate and cross-check results, and rank sources by authority and freshness."
---

# Multi-Source Search

## When to apply
Broad, comparative, or hard-to-find questions where one search would return a skewed or thin result.

## How to apply
1. Write 3-8 query variants: exact terms, synonyms, the question reframed as a claim, and one adversarial query that looks for disconfirming evidence.
2. Search each variant; do not reuse near-identical phrasing.
3. Pool results; deduplicate by canonical URL and by repeated syndicated text.
4. Score each source: authority (primary vs derivative), freshness, specificity, independence from the others.
5. Cross-check every key fact against at least two independent sources, or label it single-source.
6. Note search blind spots: paywalls, regional results, languages not covered.

## Anti-patterns
- Counting ten reposts of one article as ten confirmations.
- Letting the first result set the frame for the whole answer.

## Output expectation
A ranked source table (source, date, authority, what it supports) and a per-claim confirmation count.
