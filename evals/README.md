# Evaluation status

`STRUCTURAL-VALIDATION.json` reports catalog checks for 434 standalone prompts. `BRAIN-TEST-RESULTS.json` records the automated test run. `DEMO-TRACE.json` records six simulated activations for a dependency-ordered feature workflow.

`agent-cases.json` contains 1,302 prompt evaluation specifications. These have not been executed against AI models. Supply representative fixtures, independently scored expected results, model and tool versions, and prompt hashes before interpreting them as expertise evidence.

The automated tests cover scheduling, subprocess behavior, the provider-neutral adapter (against local mocks of Anthropic, OpenAI-compatible and Ollama servers, including weak-model behavior), direct agent/skill calls and the Claude Code pack. They are not proof of live model quality, production safety, semantic routing accuracy across all roles, or browser tool readiness. `python scripts/agent_cli.py check-live` is the one-command smoke test against your real model, hosted or local.
