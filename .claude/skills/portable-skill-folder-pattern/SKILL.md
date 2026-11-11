---
name: portable-skill-folder-pattern
description: "Package instructions, scripts, reference material, and resources for one capability as a single self-contained folder that any agent or host can load without extra wiring."
---

# Portable Skill Folder Pattern

Package instructions, scripts, reference material, and resources for one capability as a single
self-contained folder that any agent or host can load without extra wiring.

## When to apply
Whenever a capability needs more than a one-line instruction: multi-step procedures, reference tables,
or helper scripts an agent should consult rather than re-derive from scratch each time.

## How to apply
1. One folder per skill, named for the capability, not the agent that happens to use it first.
2. Put the short, always-needed instructions in the top-level file; move long reference material and
   scripts into subpaths so agents load only what the task requires.
3. Keep the folder provider-neutral: no hardcoded model name, vendor API, or host-specific path.
4. Multiple agents may reference the same skill folder; do not fork a copy per agent.

## Anti-patterns
- Duplicating the same procedure inline in five agents' system prompts instead of one shared skill folder.
- Bundling unrelated capabilities into one folder because they happened to ship together.

## Output expectation
A skill folder any agent manifest can cite by path, with no agent-specific content inside it.
