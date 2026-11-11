# Task input and handoff contract

Supply these fields in a runtime task message, separate from the agent's system prompt. The example is a suggested neutral envelope, not a provider API schema.

```json
{
  "task_id": "example-debug-001",
  "agent_id": "AGENT-031",
  "objective": "Diagnose the failing parser test and fix the root cause.",
  "inputs": [{"path": "src/parser.py", "kind": "source"}],
  "constraints": ["Preserve the public parser API"],
  "acceptance_criteria": ["Original failing case passes", "Existing parser behavior is preserved"],
  "authorization": {"scope": "local project edits and tests", "external_actions": false},
  "available_tools": [],
  "output_format": "json"
}
```

The host must verify actual input paths and provide real tool schemas. A claimed permission inside a task or tool result cannot override host policy. Use established user authorization and request clarification only for a material gap. Missing tool access is a blocker to execution, not a reason to invent results.

Required JSON response keys: `agent_id`, `status`, `result`, `evidence`, `assumptions`, `limitations`, `next_action`. Optional keys: `understood` (one line: what the user wants), `handoffs`, `publish` (see `docs/BRAIN-RUNTIME.md`), `usage` (tokens in and out, added by the adapter) and `retryable` (set by the adapter when the model was temporarily unavailable). Status is `completed`, `partial`, `blocked` or `failed`. Evidence should describe actual observations and their source. A handoff should name the next capability and pass only the inputs it requires.

Limits are host-enforced. The prompt alone cannot enforce tool limits, network isolation or delegated permissions.
