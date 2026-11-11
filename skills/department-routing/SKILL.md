---
name: department-routing
description: "Route an incoming task to the specialist department (engineering, design, product, research, security, infrastructure, data, or other domain) before routing to an individual specialist within it."
---

# Department Routing

Route an incoming task to the specialist department (engineering, design, product, research, security,
infrastructure, data, or other domain) before routing to an individual specialist within it.

## When to apply
Any time a task's department is not already stated, and before the brain's lexical/alias router narrows
to a single AGENT-NNN.

## How to apply
1. Extract the deliverable noun from the task (a diagram, a patch, a model, a dataset, a report).
2. Map the deliverable to exactly one department using the registry's `category` field as ground truth,
   not the department's informal name.
3. If the task spans two departments (e.g. "secure the API and document it"), split it into one task per
   department rather than forcing a single specialist to cover both.
4. Hand the department-scoped task to the capability resolver for specialist selection.

## Anti-patterns
- Picking a specialist by title alone before confirming the department is correct.
- Silently merging a cross-department task into one agent's scope instead of splitting it.

## Output expectation
A department label plus the original task, unchanged, ready for specialist routing.
