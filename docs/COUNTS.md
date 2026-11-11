# Counts

- 435 definitions: the executive brain AGENT-000 and 434 specialists and advisers.
- 30 groups, 30 field-expertise packs, 435 per-agent specialization focus lines (`registry/expertise.json`).
- 33 skills (`skills/<name>/SKILL.md`), each also generated as a Claude Code skill; 435 generated Claude Code subagents.
- Evaluation specifications: `evals/agent-cases.json`, not model-executed.
- Automated tests: see `evals/BRAIN-TEST-RESULTS.json`.
- 12 browser connection profiles and 10 MCP patterns; the browser agents attach a pinned Playwright MCP server in the Claude Code pack. Not live-tested here.
