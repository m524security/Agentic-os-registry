---
name: progressive-skill-disclosure
description: "Expose only a skill's short description up front; load its full instructions and resources only once a task has actually matched that skill."
---

# Progressive Skill Disclosure

Expose only a skill's short description up front; load its full instructions and resources only once a
task has actually matched that skill.

## When to apply
Whenever a skill library grows past a handful of entries, so routing and prompting do not pay the token
cost of every skill on every task.

## How to apply
1. Keep a compact index (name + one-line purpose) separate from each skill's full body.
2. Match tasks against the compact index first.
3. Load the full skill file only for the one or two skills a matched task actually needs.
4. Never require an agent to read every skill file to find the relevant one.

## Anti-patterns
- Concatenating every skill file into every system prompt "just in case."
- An index entry so vague that disclosure cannot tell skills apart.

## Output expectation
A short index that reliably narrows to the right full skill file without loading the rest.
