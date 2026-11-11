---
name: live-model-connection
description: "Connect an adapter to any model endpoint, cloud or local: keep keys in the environment, pin the model, bound the call, and report connection failures precisely."
---

# Live Model Connection

## When to apply
Wiring the registry or any agent to a model endpoint (hosted API, Ollama, an OpenAI-compatible local server, or a local command), or diagnosing why a call fails.

## How to apply
1. Read any API key only from the process environment; never from task data, prompts, or files in the repository. Local servers usually need none.
2. Make the model and endpoint configurable; keep no default that silently changes provider.
3. Send the agent's system prompt as system instructions and the task as user data.
4. Enforce a timeout and a maximum response size; fail closed on both.
5. For a local server, check that it is running and the model is installed before blaming the adapter.
6. Distinguish failures: missing key, authentication rejected, rate limited, server error, malformed reply. Report each by name.
7. Never print the key or full request headers in logs or errors.
8. Smoke-test with a trivial task before running a real plan.

## Anti-patterns
- Embedding a key in a config file that is committed.
- Treating every non-200 as the same error.

## Output expectation
A connection check result naming the model, endpoint host, and pass or the exact failure class.
