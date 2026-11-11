---
name: reversibility-aware-autonomy
description: "Classify every consequential action's reversibility and blast radius before it executes, and scale caution — confirmation, dry-run, narrower scope — to match."
---

# Reversibility-Aware Autonomy

Classify every consequential action's reversibility and blast radius before it executes, and scale
caution — confirmation, dry-run, narrower scope — to match.

## When to apply
Before any action with real-world or shared-state side effects: deletes, deploys, credential changes,
destructive migrations, or anything touching data the agent does not own outright.

## How to apply
1. Classify: fully reversible (safe to retry) / reversible with cost (backup needed first) /
   irreversible (requires explicit authorization).
2. Classify blast radius: scoped to the task's own output / affects shared state / affects other users
   or systems.
3. Irreversible or wide-blast-radius actions require host-level authorization and, where available, a
   dry run before the real one.
4. Prefer the reversible path even if slower, when both paths satisfy the task.

## Anti-patterns
- Running an irreversible, wide-blast-radius action because a reversible equivalent was "slower."
- Treating "I checked carefully" as a substitute for a dry run or backup when one is available.

## Output expectation
A stated reversibility/blast-radius classification attached to every consequential action taken.
