---
name: engineering-role-patterns
description: "Apply the planner / implementer / reviewer / tester / security-specialist split consistently, so no single role both builds and is the sole judge of its own work."
---

# Engineering Role Patterns

Apply the planner / implementer / reviewer / tester / security-specialist split consistently, so no single
role both builds and is the sole judge of its own work.

## When to apply
Any engineering task that includes a quality gate — which is nearly all of them.

## How to apply
1. Planner decomposes the task and names its dependencies before any code is written.
2. Implementer builds strictly inside the planned scope.
3. Reviewer and tester are separate from the implementer, even when the same underlying model performs
   both roles in sequence — the manifest's `verification` entries are evaluated independently of the
   agent that produced the work.
4. Security specialist is pulled in explicitly for trust-boundary or credential-handling changes, not
   assumed to be covered by a general reviewer.

## Anti-patterns
- Letting the implementer mark its own output `completed` without a separate verification pass.
- Skipping the planner step on "simple" tasks that turn out to have hidden dependencies.

## Output expectation
A visible handoff between roles, each with its own recorded evidence.
