---
name: explicit-invocation
description: "Resolve a user's explicit request for a named agent or skill: exact ID or slug first, then fuzzy name match, and ask only when still ambiguous."
---

# Explicit Invocation

## When to apply
The user names an agent (an ID such as AGENT-046, a slug, or a role name) or a skill, or asks to "use", "call", or "run" one.

## How to apply
1. Exact match first: agent ID, slug, or skill name. An exact match is final; do not second-guess it with routing.
2. If there is no exact match, match on name or alias. One clear winner is used and stated; several close candidates are listed for the user to pick.
3. Honor the user's choice even when another agent might fit better; mention the alternative in one line.
4. Load the chosen agent's prompt and its listed skill modules before acting.
5. If the named agent lacks a capability the task needs, say which capability and what the host must grant. Do not silently substitute another agent.

## Anti-patterns
- Re-routing an explicit request to a different agent without saying so.
- Guessing between two equally good matches.

## Output expectation
The resolved agent or skill, how it was matched, and the task handed to it unchanged.
