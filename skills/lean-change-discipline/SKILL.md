---
name: lean-change-discipline
description: "The smallest change that fully solves the task: scope listed first, no unrequested machinery, evidence over confidence, named shortcuts and a closing note on what was skipped and the remaining risk."
---

# Lean Change Discipline

The smallest change that fully and correctly solves the task, handed back with a one-line account of what
was skipped and what risk remains. This is the registry's standing discipline for every coding,
refactoring, and review specialist — the same discipline `brain/LINE-CODE-AUDITOR.md` applies at the
line level, stated here as a skill any agent can cite.

## When to apply
Every software-engineering, verification-recovery, and code-review task, by default — not only when a
task explicitly asks for a minimal or lean solution.

## How to apply
1. **Scope first.** Read the task and the code it touches. List every caller, test, fixture, config, and
   export the change must reach. That list is the scope; nothing outside it is in scope without being
   named and justified.
2. **Smallest complete option.** In order, prefer: nothing (the capability already exists) > the pattern
   the codebase already uses > the standard library or platform feature > an already-installed
   dependency > new code written directly > a new abstraction. Stop at the first option that fully works.
3. **Finish what the change touches.** Being lean about the solution never means leaving a caller, test,
   or fixture broken. Every part the task's scope requires gets finished.
4. **No unrequested machinery.** No abstraction, config flag, wrapper, or "for later" extensibility point
   the task did not ask for; name any simpler option considered in one line instead of silently building
   the bigger one.
5. **Evidence, not confidence.** New non-trivial logic (a branch, a loop, a parser, money- or
   security-relevant code) carries a small test or an explicit check; trivial changes do not need one —
   see `evidence-first-verification.md`.
6. **Name the shortcut.** A deliberate shortcut with a known limit gets a one-line note naming the limit
   and when it should be revisited, attached to the change itself, not left implicit.
7. **Close with risk.** End the handoff with one or two lines: what was skipped or not checked, and any
   risk the requester must know before relying on the change.

## Levels
- **lean** — build exactly what was asked; name the smaller option and let the requester choose if one
  exists.
- **standard** (default) — the full discipline above.
- **strict** — also challenge any part of the request itself that the stated need does not justify,
  before building.

## Anti-patterns
- Adding an interface, plugin point, or config option with exactly one real caller.
- A "lean" diff that leaves a broken caller, test, or fixture outside its stated scope.
- Reporting success with no evidence trail an independent reviewer could check.

## Output expectation
A diff or patch scoped to the named list, a KEEP/SIMPLIFY/MERGE/REPLACE/DELETE account of anything
touched but not changed, and a closing one-to-two-line skipped/risk note.
