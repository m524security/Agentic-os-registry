# Line-Level Code Auditor

The registry's lean-change discipline, applied at the line level. This is the same protocol as
`skills/lean-change-discipline/SKILL.md` and `skills/what-why-required/SKILL.md`, invoked as a
dedicated pass rather than a general writing habit.

For each meaningful line or block, answer: WHAT does it do? WHY is it needed? REQUIRED — what actually
breaks if it is removed? Is there a simpler alternative? Is it duplicated elsewhere? What
runtime/memory/token/maintenance/security cost does it add? Decision: KEEP / SIMPLIFY / MERGE / REPLACE /
DELETE, with a one-line justification per decision.

Use AST/function/diff batching for efficiency; produce a literal line-by-line explanation only when the
requester asks for one. `scripts/agent_cli.py lean-audit <path>` runs the deterministic pre-scan this
auditor should start from (long functions, duplicate blocks, TODO/FIXME debt, dead-looking code) before
the line-level WHAT/WHY/REQUIRED pass applies judgment the scan cannot.

Attached by default to AGENT-033 (Code Review Agent), AGENT-086 (Secure-Code Review Agent), AGENT-143
(Deletion Agent), and AGENT-145 (Simplification Agent) via their manifests' `skill_modules`; any agent may
cite it directly for a one-off audit pass.
