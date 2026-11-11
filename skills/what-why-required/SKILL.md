---
name: what-why-required
description: "Before any non-trivial line, block, or new file survives review, it must answer: what does it do, why is it needed, and is it actually required."
---

# What / Why / Required

Before any non-trivial line, block, or new file survives review, it must answer: what does it do, why is
it needed, and is it actually required.

## When to apply
Reviewing or writing new logic: a branch, a loop, a parser, a new file, money- or security-relevant code,
or anything a reader cannot parse at a glance.

## How to apply
For each meaningful line or block, answer in order:
1. WHAT does it do?
2. WHY is it needed — which concrete requirement forces it to exist?
3. REQUIRED — what actually breaks if it is removed? If nothing breaks, it is not required.
4. Is there a simpler alternative that satisfies the same requirement?
5. Is it duplicated elsewhere in the codebase already?
6. What ongoing cost does it add — runtime, memory, tokens, maintenance, attack surface?
7. Decision: KEEP / SIMPLIFY / MERGE / REPLACE / DELETE.

Batch this by function or by diff hunk for efficiency; produce a literal line-by-line pass only when the
reviewer specifically asks for one.

## Anti-patterns
- Keeping code because it is already written, not because step 3 justified it.
- Skipping the duplication check and merging in a second implementation of an existing helper.

## Output expectation
A KEEP/SIMPLIFY/MERGE/REPLACE/DELETE decision per unit reviewed, each with its one-line justification.
