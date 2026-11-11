---
name: cross-session-memory-pattern
description: "Persist project knowledge that is actually useful across sessions, with decay for stale facts, consolidation of duplicates, and provenance for everything stored."
---

# Cross Session Memory Pattern

Persist project knowledge that is actually useful across sessions, with decay for stale facts,
consolidation of duplicates, and provenance for everything stored.

## When to apply
Before writing anything to a persistent memory store, and periodically when reviewing what is stored.

## How to apply
1. Provenance: every stored item records where it came from and when.
2. Decay: time-box facts that can go stale (a file path, a config value, a person's role); re-verify or
   drop them past their useful window.
3. Consolidation: merge near-duplicate memories instead of accumulating near-identical entries.
4. Scope: write to the narrowest memory scope the fact actually needs (task-local by default; only an
   authorized, retention-policy-bound store gets durable writes), per each agent's `memory_scope` field.

## Anti-patterns
- Writing secrets or credentials into memory instead of references to them.
- Letting stale, unverified facts silently outrank newer evidence because they were written first.

## Output expectation
A memory store that stays small, current, and traceable to its source.
