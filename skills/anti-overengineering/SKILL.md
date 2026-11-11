---
name: anti-overengineering
description: "Detect unjustified abstraction, wrappers, extra dependencies, premature extensibility, and complexity that the task did not ask for."
---

# Anti-Overengineering

Detect unjustified abstraction, wrappers, extra dependencies, premature extensibility, and complexity
that the task did not ask for.

## When to apply
Before adding any abstraction layer, configuration option, new dependency, or "for later" extensibility
point, and when reviewing someone else's change for the same.

## How to apply
1. Ask whether the simpler, direct version actually fails the task's real requirements — not a
   hypothetical future one.
2. Prefer: nothing > an existing pattern in the codebase > the platform/standard library > an installed
   dependency > new code > a new abstraction, in that order.
3. Flag any wrapper, interface, or config knob with exactly one real caller or one real value as
   unjustified until a second real need appears.
4. Treat "we might need this later" as a reason to note the limitation, not a reason to build it now.

## Anti-patterns
- Adding a plugin/strategy pattern for a single hardcoded implementation.
- Pulling in a dependency to save a few lines of code that are easy to write directly.

## Output expectation
Each added abstraction paired with the concrete, current requirement that justifies it.
