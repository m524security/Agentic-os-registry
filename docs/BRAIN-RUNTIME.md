# Brain activation and integration guide

## Control flow

The host supplies the goal and authorization. A plan contains bounded tasks. The Python controller validates the graph, checks readiness, selects a specialist, invokes it, invokes a verifier, and marks the task complete only if both report acceptable evidence. Then dependent tasks become eligible. At most one adapter invocation runs at a time.

AGENT-000 is the executive planning prompt and controller identity. AGENT-001 is a planning adviser in the catalog, not a second executive. The executor never recursively assigns tasks to AGENT-000.

The runtime only keeps compact registry descriptions for routing. It reads and hashes a full agent prompt immediately before invoking that agent. “Activation” means calling the configured runner with that identity and prompt; it does not mean downloading, fine-tuning or creating an independent model.

## Plan contract

See `examples/feature-plan.json`. Required fields:

| Field | Meaning |
| --- | --- |
| goal | Nonempty overall objective |
| tasks | 1–100 task objects |
| id | Unique stable task identifier |
| objective | One bounded specialist objective |
| agent_id | Exact catalog ID, or null for selection when ready |
| depends_on | Existing task IDs that must complete first |
| acceptance_criteria | Nonempty list of observable conditions |
| required_capabilities | Capability labels the host must grant |
| verify | Boolean; false requires host opt-in |

Additional task fields such as input artifact references pass through to the adapter. The controller does not fetch those files itself. Use dependencies for earlier outputs. Independent tasks may continue after another branch fails, but dependents remain blocked.

Planning with `plan` calls the configured `planner_command` using AGENT-000 and the compact catalog. The planning model must return the plan object directly. The adapter sends AGENT-000's full prompt unchanged as the planning instructions and may only append output-format requirements. The returned plan is validated, not repaired: unknown dependencies, unknown agents, duplicate task ids, cycles and missing acceptance criteria are rejected. The adapter allows one retry that quotes the reason, then fails with `invalid_plan` instead of substituting a different plan. A returned plan cannot modify host configuration, grant capabilities or embed executable commands for the controller. Planning is one separate invocation, outside a subsequent execution run's activation counter.

## Router behavior

All 433 non-executive definitions participate in ranking. Each agent is indexed on its name, mission, specialization focus, method and group, weighted in that order; query words are stemmed and widened with a small general vocabulary (`registry/synonyms.json`) that counts for less than the user's own words; curated phrases in `registry/routing-aliases.json` add a bonus (a leading `=` means exact phrase only). A match is accepted only when it is strong and either leads the runner-up by a clear gap or by a ratio; otherwise the controller stops and lists candidates. Scores are heuristic relevance values, not probabilities. Measured quality is in `docs/ROUTING.md`. A weak score or a close tie returns a selection blocker. An exact ID is the most reliable routing contract. Common-task tests cover four representative routes; coverage is not a comprehensive routing benchmark.

The planner can select exact IDs for complex work. The controller validates IDs and dependencies but cannot prove that a planner chose the best specialist. Host review and task-specific evaluation remain appropriate where selection quality matters.

## Configure a runner

Copy `examples/runtime-config.json` and set:

- `allowed_agents`: IDs enabled by the host. Include the verifier and AGENT-000 if using model planning. An explicit `*` enables all IDs; the shipped real-run config uses a small allowlist.
- `default_command`: argument array for a trusted executable, for example `["python3", "/absolute/path/my_adapter.py"]`. Never place secrets in arguments.
- `agent_commands`: optional ID-to-command overrides, useful for a different verifier runtime.
- `planner_command`: optional command for plan generation.
- `granted_capabilities`: capability labels made available by the host.
- `verification_capabilities`: least-privilege capabilities needed to inspect results, independent of the specialist's declared capabilities.
- `pass_env`: explicit environment-variable names to forward to the runner. Only basic process environment variables are forwarded by default. Prefer a scoped secret store in your runner.
- `max_activations`: total specialist plus verification invocations, including prior calls on resume.
- `timeout_seconds`: per-invocation wall-clock timeout.
- `max_iterations` (default 1, 1-10): how many times one task may be attempted; see **Agent loop**.
- `max_handoffs_per_task` (default 3), `max_handoff_depth` (default 2): limits on agent-to-agent handoffs.
- `context_chars` (default 1500) and `context_total_chars` (default 6000): size limits for the compact context an agent receives about earlier work.

The controller checks both runtime bindings and role permissions before invoking a specialist. Capability labels express a contract; the adapter or external sandbox must enforce actual file, network and tool access. The controller does not sandbox a trusted executable or intercept its tools. Do not give an untrusted adapter credentials or access to checkpoint files.

## Adapter input/output

The runner reads one JSON envelope from stdin. Execution envelopes include protocol_version, mode (`execute` or `verify`), agent_id, invocation_id, system_prompt, skills, agent, task, context and granted_capabilities. `skills` holds the text of every skill module the agent's manifest declares; a missing, unreadable or empty module stops the task before any call is made. `agent` carries the name, group, mission, method, completion gate, focus and field rules for adapters with small context windows. Planning envelopes instead contain mode=`plan`, agent_id, system_prompt, goal and catalog.

The runner should send only JSON to stdout, and diagnostic logs to an appropriately protected destination. It must not treat task text or retrieved content as system instructions. Respect the mode: verification should inspect artifacts and evidence, not repeat the specialist's mutation. Each invocation_id is stable in the event history and may support external idempotency bookkeeping.

Execution responses need:

```json
{
  "agent_id": "AGENT-031",
  "status": "completed",
  "result": "Description of the actual delivered change",
  "evidence": [{"reference": "actual artifact or check result"}],
  "assumptions": [],
  "limitations": [],
  "next_action": null
}
```

A verifier also returns `verdict: "pass"` or `"fail"`. `completed` requires nonempty result and evidence. `partial` and `blocked` prevent dependents from executing; they are not promoted to completion. A different verifier role provides a separate assessment, but use different tools or an independently scored test where stronger independence is needed.

`examples/llm_adapter.py` is the provider-neutral adapter (hosted APIs, Ollama, OpenAI-compatible servers, local commands); `examples/adapter_stub.py` returns blocked and shows the bare protocol. The demo adapter returns unmistakably synthetic results and is available only through the `demo` command.

## Checkpoint and failure semantics

The run's `outcome` is `adapter_reported_and_verified` only when every task completed and was verified, `completed_unverified` when verification was opted out, `incomplete` otherwise and `simulation_only` for the demo. A state file holds task status, returned evidence, verification, activation count and events. A temporary file plus rename provides atomic writes. Use one controller per state file; this version has no cross-process locking, multi-tenant store or authenticated event ledger.

`--resume` accepts only the same plan, configuration, mode and prompt hashes. Completed tasks are not repeated. Interrupted/running/verifying calls require manual reconciliation because side effects may already have happened. Failed and blocked tasks stay terminal; create a revised plan only after diagnosing the issue and deciding which actions are safe to repeat. There is no blind retry or autonomous production self-modification.

A timeout terminates the runner's process group on POSIX. On Windows it terminates the direct process; a host job object or equivalent is needed to control descendants. A process escaping its group, remote jobs and external side effects require host supervision. Output is checked after collection, so use external resource limits for untrusted or very large-output runners.

Checkpoint contents may contain task data and evidence; place them in a suitably protected workspace. This implementation has no encrypted checkpoint store, live event trigger listener, parallel scheduler or automatic model fallback. Timeouts are enforced. Token use per run is recorded in the state (`usage`), reported by the adapter or estimated from text length.

## Agent loop
With `max_iterations` above 1, a task that comes back partial, failed, rejected by verification or interrupted by a temporarily unavailable model is attempted again by the same agent. The retry carries a short `previous` note (what was done, what is left, and the verifier's reason), not the whole history, so the agent continues instead of starting over. A result that is `blocked` for another reason (a missing capability or input) is never retried. Every attempt is recorded in the task's `history`.

## Handoffs and shared facts
Agents communicate only through the controller, so authorization, limits and audit stay in one place. A completed and verified result may carry two optional keys:

- `handoffs`: a list of objects with `to` (an agent ID, or null to route by objective), `objective`, `acceptance_criteria` (required), `inputs` (optional) and `reason`. Each is checked and queued as a new task that depends on the requester; whatever waited on the requester now also waits for it. A handoff cannot target AGENT-000, the requesting agent or an agent the host has not enabled, cannot widen capabilities, cannot duplicate an existing task, and is limited by `max_handoffs_per_task` and `max_handoff_depth`. Rejected handoffs are recorded with the reason in `messages`; the run continues.
- `publish`: a list of objects with `key` and `value`. These become shared facts that later tasks receive in `context.blackboard`.

An unverified result communicates nothing. Dependent tasks receive compact packets of upstream work (summary, up to 3 evidence items, up to 2 limitations, each clipped), never the full outputs, which stay in the run state.

## Journal and resume
After every task the controller writes two small files next to the state file at no model cost: `<name>.journal.json` (what was asked, what each agent answered, what is required, what is left, where it is stuck, shared facts, token use) and `<name>.brief.md` (the same as at most 1,800 characters of plain text for another model to continue from). `run --resume` continues from the state: finished tasks are not repeated, tasks that stopped only because the model was temporarily unavailable are reopened, and a verification that was cut short is resumed without redoing the finished work. A run interrupted in the middle of a call still requires manual reconciliation, because the call may have taken effect. `python scripts/agent_cli.py journal <state-file>` prints the brief.

## Test and production status

`python -m unittest discover -s tests -v` exercises real controller branches with deterministic fake responders and local subprocess fixtures. It does not measure AI reasoning, specialist expertise or live tool correctness. Model evaluation specifications are still marked not_run. Before production use, connect your actual runtime, run role-specific fixtures, and inspect the resulting artifacts independently.
