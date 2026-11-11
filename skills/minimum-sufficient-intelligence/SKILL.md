---
name: minimum-sufficient-intelligence
description: "Prefer a deterministic script, a single tool call, or one focused model call before escalating to autonomous multi-step or multi-agent execution."
---

# Minimum Sufficient Intelligence

Prefer a deterministic script, a single tool call, or one focused model call before escalating to
autonomous multi-step or multi-agent execution.

## When to apply
At the start of every task, before choosing how much machinery to bring to bear on it.

## How to apply
1. Can a deterministic script or existing tool answer this exactly? Use it; do not route it to a model.
2. Can one focused model call, with no tool loop, complete it? Use that before an agentic loop.
3. Only escalate to multi-step autonomous execution, or to multiple specialist agents, when the task
   genuinely requires branching judgment or coordination a single call cannot provide.
4. Re-evaluate mid-task: if a simpler path becomes available, drop back down to it.

## Anti-patterns
- Spinning up a multi-agent workflow for a task one script could finish deterministically.
- Treating "agentic" as always better, independent of whether the task needs the extra autonomy.

## Output expectation
The task completed at the lowest level of machinery that reliably does the job.
