<p align="center"><img src="assets/logo.svg" alt="Agentic OS Registry" width="520"></p>

# Agentic OS Registry

A catalog of specialist AI agents with a small controller that runs them, plus a ready-made Claude Code pack. Every agent is an exact
system prompt and a manifest; every prompt is compiled from the agent's own focus and a field-expertise pack, so each agent starts from
the working knowledge of its discipline rather than a generic role line. The controller works with **any model**: hosted APIs, or a
small local model (for example a 2B model on Ollama) through the same adapter.

<!-- STATS:START -->
435 agents (the executive brain AGENT-000 and 434 specialists and advisers) in 30 groups across 10 categories, 33 skills, 435 generated Claude Code subagents.
<!-- STATS:END -->

- **Use it in Claude Code:** copy the included `.claude/` pack, then call `@agent-...` or `/skill-name`.
- **Use it with any model:** call one agent or skill from the terminal, or run a multi-agent plan with `brain/runtime.py`.
- **Extend it:** edit one JSON file or run one command; prompts, indexes, docs and the Claude Code pack rebuild from it.

## Contents

1. [Quick start](#quick-start)
2. [Requirements and install](#requirements-and-install)
3. [Connect a model](#connect-a-model)
4. [Call a specific agent or skill](#call-a-specific-agent-or-skill)
5. [Work on a task until it is done](#work-on-a-task-until-it-is-done) and [run a multi-agent plan](#run-a-multi-agent-plan)
6. [Use it in Claude Code](#use-it-in-claude-code)
7. [Token and CPU use](#token-and-cpu-use) and [web search, crawling and browsers](#web-search-crawling-and-browsers)
8. [How an agent is built](#how-an-agent-is-built)
9. [Add or change an agent or skill](#add-or-change-an-agent-or-skill)
10. [Skills](#skills)
11. [Agent directory](#agent-directory)
12. [Quality, testing and limits](#quality-testing-and-limits)
13. [Safety](#safety)
14. [Troubleshooting](#troubleshooting)
15. [Repository layout](#repository-layout)

## Quick start

```bash
git clone <your-repo-url> agentic-os-registry && cd agentic-os-registry
python scripts/agent_cli.py validate                      # 1. confirm the package is intact
python scripts/agent_cli.py find "review code for security defects"   # 2. see which agents fit
python scripts/agent_cli.py check-live                    # 3. test your model connection (see "Connect a model")
python scripts/agent_cli.py ask AGENT-086 "review src/auth.py for injection risks"   # 4. call one agent
```

| I want to... | Do this |
| --- | --- |
| Call one agent or skill | `python scripts/agent_cli.py ask <AGENT-ID, slug or skill> "message"` |
| Find the right agent | `python scripts/agent_cli.py find "what I need"` |
| Read an agent's full prompt | `python scripts/agent_cli.py show AGENT-238` |
| Work on one task until it is done, resumably | `python scripts/agent_cli.py work AGENT-030 "task"` |
| Run several agents on a goal | [Run a multi-agent plan](#run-a-multi-agent-plan) |
| Use the agents in Claude Code | `python scripts/agent_cli.py install-claude-code` |
| Add an agent | [Add or change an agent or skill](#add-or-change-an-agent-or-skill) |

## Requirements and install

- Python 3.9 or newer. The standard library is enough; there is nothing to `pip install`.
- A model to talk to (see next section). Browser automation additionally needs Node.js and a host that provides a browser tool.
- Run commands from the repository root. Use `python` or `python3`, whichever your system provides; the shipped configs work with both.

## Connect a model

One adapter, `examples/llm_adapter.py`, serves every provider. Choose it with `--provider` (or `LLM_PROVIDER`) and test with `check-live`.

| Provider | Value | Default address | Notes |
| --- | --- | --- | --- |
| Ollama (local) | `ollama` | `localhost:11434` | Default when nothing is set. Model auto-detected if exactly one chat model is installed |
| llama.cpp server | `llamacpp` | `localhost:8080/v1` | OpenAI-compatible |
| LM Studio | `lmstudio` | `localhost:1234/v1` | OpenAI-compatible |
| vLLM | `vllm` | `localhost:8000/v1` | OpenAI-compatible |
| Any OpenAI-compatible server | `openai` + `LLM_BASE_URL` | `api.openai.com/v1` | Hosted OpenAI needs `LLM_API_KEY` |
| Anthropic | `anthropic` | `api.anthropic.com` | `ANTHROPIC_API_KEY`; used automatically when the key is set and nothing else is |
| Any command-line program | `command` | none | `LLM_COMMAND='["llama-cli","-m","model.gguf"]'`: prompt on stdin, reply on stdout |

```bash
# local 2B model, no key and no internet needed
ollama pull qwen2.5:1.5b
python scripts/agent_cli.py check-live --provider ollama --model qwen2.5:1.5b

# hosted
ANTHROPIC_API_KEY=... python scripts/agent_cli.py check-live
LLM_PROVIDER=openai LLM_API_KEY=... LLM_MODEL=<model> python scripts/agent_cli.py check-live
```

Settings (environment variables or CLI flags `--provider --model --base-url --profile`): `LLM_PROVIDER`, `LLM_MODEL`, `LLM_BASE_URL`,
`LLM_API_KEY`, `LLM_PROFILE`, `LLM_CONTEXT` (Ollama context tokens), `LLM_TIMEOUT` (seconds; default 600 for local, 110 for Anthropic),
`LLM_COMMAND`, `LLM_KEEP_ALIVE` (how long Ollama keeps the model loaded, default 10m), `LLM_SKILL_CHARS`, `SEARCH_URL`. Keys are read only from the environment
and are never printed.

### Small and local models

The adapter picks a **prompt profile** from the model name (override with `LLM_PROFILE`):

| Profile | Chosen for | What is sent | Reply limit |
| --- | --- | --- | --- |
| `tiny` | up to about 4B parameters (`:1.5b`, `2b`, `3b`, `tinyllama`, `phi3:mini`) | identity, mission, focus, method, gate, field rules, skill names (about 1.5 KB) | 700 tokens |
| `compact` | about 5-14B or unknown local models | adds the field expertise, procedure, evidence section and two trimmed skills (about 4-5 KB) | 1500 tokens |
| `full` | larger or hosted models | the complete prompt and every skill module | 4096 tokens |

Condensed profiles keep the essentials, add optional sections only while they fit, and **report anything left out** in the response's
`notes` field. For weak models the adapter also asks for JSON mode where the server supports it, repairs sloppy JSON, retries an unparseable
reply once, and never counts prose as success: unstructured text becomes a *partial* result with no evidence, and a verifier that does not
return a clear pass with evidence fails closed. Models under about 14B do best on narrow, checkable tasks; keep plans to a few tasks.

## Call a specific agent or skill

An explicit request is final. Matching order: exact agent ID, exact slug, exact skill name, then ranked matching. Ranked matching only
acts when one agent is clearly ahead; otherwise it lists candidates for you to choose.

```bash
python scripts/agent_cli.py ask AGENT-086 "review src/auth.py for injection risks"
python scripts/agent_cli.py ask agent-426-web-crawl-agent "summarize https://example.com/docs" --web
python scripts/agent_cli.py ask web-research "current LTS versions of Node.js" --web
python scripts/agent_cli.py ask AGENT-420 "document the CLI" --skill clear-communication      # add a skill to any agent
python scripts/agent_cli.py ask AGENT-433 "how do I run this offline?" --provider ollama --model qwen2.5:1.5b
python scripts/agent_cli.py find "check my tls configuration"       # ranked candidates with scores
python scripts/agent_cli.py skills                                  # list skills
python scripts/agent_cli.py show web-research                       # print an agent prompt or a skill
```

Every agent loads the skill modules its manifest declares. If a declared skill file is missing, unreadable or empty the call stops with a
named error instead of running without it.

## Work on a task until it is done

`work` is the one-command version of understand, execute and loop. The agent states what it understood, does the work, and if the result is
partial (or fails verification, or the model was briefly unavailable) it is called again with a short note of what is done and what is left,
not the whole history, up to `--turns` times. Every step is saved, so a stopped run continues from what is left.

```bash
python scripts/agent_cli.py work AGENT-030 "add a --json flag to the CLI and test it" --turns 3
python scripts/agent_cli.py work AGENT-030 "..." --verify          # add an independent verification pass
python scripts/agent_cli.py journal .agentic/runs/<run>.json        # print the saved brief: asked, done, left, stuck
python scripts/agent_cli.py work --resume .agentic/runs/<run>.json # continue from what is left
python scripts/agent_cli.py ask AGENT-433 "next question" --session demo   # keep a compact record of a conversation
```

The saved brief (at most 1,800 characters: what was asked, what is done, what is left, why it stalled, facts later steps need) is written by
the controller at no model cost, and any model can continue from it if a context window fills up or a provider stops answering.
`AGENT-434` (Session Journal Agent) explains how to read and write that record. Sessions keep only the last few exchanges in about 1,500
characters, so a long conversation costs about the same on every turn.

## Run a multi-agent plan

The controller in `brain/runtime.py` turns a goal into ordered tasks, activates only the agent each ready task needs, runs a separate
verification role and checkpoints state. A plan looks like `examples/feature-plan.json`: tasks with `id`, `objective`, `agent_id` (or null to
route), `depends_on`, `acceptance_criteria`, `required_capabilities` and `verify`.

```bash
python brain/runtime.py demo --plan examples/feature-plan.json --state demo.json     # simulation, no model
python brain/runtime.py plan "your goal" --config examples/runtime-config.live.json --out plan.json
python brain/runtime.py run --plan plan.json --config examples/runtime-config.live.json --state run.json
python brain/runtime.py run --plan plan.json --config examples/runtime-config.live.json --state run.json --resume
python brain/runtime.py route "Review accessibility and keyboard navigation"
```

- **Planning** sends AGENT-000's full prompt to the model unchanged. The returned plan is validated, not repaired: unknown dependencies,
  unknown agents, duplicate ids, cycles and missing criteria are rejected (one retry quotes the reason, then it fails with `invalid_plan`).
- **Configs:** `examples/runtime-config.live.json` (any model) and `examples/runtime-config.local.json` (long timeouts for local models).
  Keys: `allowed_agents` (`["*"]` for all), `granted_capabilities`, `timeout_seconds`, `max_iterations` (attempts per task, default 1; the
  examples use 3), `max_handoffs_per_task`, `max_handoff_depth`, `context_chars`, `verifier_agent_id`, `pass_env`, `default_command`,
  `planner_command`. Details in `docs/BRAIN-RUNTIME.md`.
- **Agents talk through the controller.** A verified result may include `handoffs` (work another agent should do; each is validated and queued
  as a new task) and `publish` (facts later tasks receive). Dependent tasks get compact packets of earlier work, not full outputs. Nothing
  moves between agents unchecked: no handoff to AGENT-000, to yourself, to an agent the host has not enabled, or with wider capabilities.
- **Outcome:** `adapter_reported_and_verified` only when every task completed and was verified; otherwise `incomplete`,
  `completed_unverified` or `simulation_only`.
- Interrupted calls are never replayed automatically, because side effects may already have happened. Work that stopped only because the
  model was temporarily unavailable is reopened on `--resume`; finished tasks are not repeated.

## Use it in Claude Code

The generated pack is included: `.claude/agents/<category>/<slug>.md` (one subagent per agent) and `.claude/skills/<name>/SKILL.md`.

```bash
python scripts/agent_cli.py install-claude-code                 # into the current project's .claude/
python scripts/agent_cli.py install-claude-code --scope user    # into ~/.claude/
python scripts/agent_cli.py check-claude-code                   # verify the pack is complete and in sync
```

Then call an agent with `@agent-086-secure-code-review-agent review src/auth`, or a skill with `/web-research <question>`. Install never
overwrites a file you changed unless you pass `--force`. Each subagent's `tools` are derived from its manifest capabilities (least privilege:
read-only agents get Read/Grep/Glob, edit agents add Edit/Write, execution roles add Bash, research agents get WebSearch/WebFetch) and its
`skills:` from `skill_modules`. The browser agents (AGENT-046, 056, 428) attach a pinned Playwright MCP server scoped to that subagent and are
denied file writes. Edit `agents/` and `skills/`, never `.claude/`; regenerate with `python scripts/build_all.py`.

Claude.ai chat and Cowork do not read `.claude/agents`. For those, `python scripts/agent_cli.py show AGENT-NNN` prints a prompt you can paste
as instructions. Native loading there was not tested.

## Token and CPU use

Measured on this repository (characters; about 4 per token):

| What | Size or time |
| --- | --- |
| Full prompt file (shared standard plus the agent part) | about 6.4 KB mean, 8.4 KB max, of which about 3.8 KB is the shared prefix |
| Prompt sent by the `tiny` profile | about 1.4 KB mean (about 350 tokens) |
| Prompt sent by the `compact` profile | about 4.1 KB mean (about 1,000 tokens) |
| Skills added to a `full` prompt | the most relevant skill in full, others as one-line summaries, up to `LLM_SKILL_CHARS` (default 4,500) |
| Routing index load | about 5 ms (it is precomputed) |
| Command start-up (`find`, `route`) | about 60 ms |

How usage is kept down: answers are asked for in the fewest words that stay correct; the first line states the understood request so a
misreading is caught early; dependent tasks get clipped packets instead of full outputs; a retry sends only what is done and what is left; a
cached shared prefix is reused across agents; Ollama keeps the model loaded between agents instead of reloading it; small models get condensed prompts; and web pages are clipped before they reach the model.
Token use per run is recorded in the state file (`usage`, reported by the provider or estimated from text length). Nothing here caps or
meters tokens; it only avoids spending them.

## Web search, crawling and browsers

| Need | How | Notes |
| --- | --- | --- |
| Fetch pages | `web_fetch` capability: the host fetches URLs found in the task (`tools/webtools.py`) | http(s) only; private and loopback addresses refused unless `WEB_ALLOW_PRIVATE=1` |
| Bounded crawl | `crawl_runtime` capability: robots rules, visited set, delays, page and depth limits | at most 50 pages, depth 3 |
| Web search | `web_search`: Anthropic's built-in search tool, or `SEARCH_URL` pointing at a SearXNG-style JSON endpoint | works with any model; nothing bundled |
| Parallel multi-source search | skill `multi-source-search` with AGENT-427 | |
| Browser automation | Claude Code pack with the Playwright MCP server; skill `browser-automation` with AGENT-428 | needs a host with a browser tool; the standalone adapter returns `blocked` for `browser_control` |

Retrieved text reaches the model as untrusted data in the user message, never the system prompt, and the pages used are recorded as
evidence. A task that needs a capability the adapter cannot provide returns `blocked` without calling the model.

## How an agent is built

```
registry/expertise.json  ──►  scripts/build_prompts.py  ──►  agents/<category>/AGENT-NNN/system-prompt.md
agents/*/AGENT-NNN/manifest.json  ─┘                          registry/*.json, docs/AGENTS.md, README directory  (build_catalog.py)
                                                              .claude/agents, .claude/skills                      (agent_cli.py build-claude-code)
```

Every prompt has two parts. The **operating standard** comes first and is identical for all agents: the quality standard; how to work
(state what the user wants in one line, answer exactly that in the fewest words that stay correct, pick the simplest method, give every line of
code a short reason, say exactly what is left if work remains); task intake; tools and authority; and the response contract (status, result,
evidence, assumptions, limitations, handoff, with optional `understood`, `handoffs` and `publish`). The **agent part** follows: its role and
mission, its own **specialization focus**, the **field expertise** of its group (what a master knows, how they work, where work goes wrong, what
done looks like), the operating procedure and its completion gate. Because the shared part is byte-identical and first, a server that caches
the start of a prompt (hosted caches, llama.cpp, Ollama) processes it once and reuses it across agents. "30+ years" is a quality standard for
judgment, not a claim of real experience.

The manifest holds the mission, method, completion gate, suggested capabilities, `skill_modules`, permissions and output contract.
`tools` is intentionally empty: a manifest grants nothing; the host decides what each agent may use.

## Add or change an agent or skill

Everything derived (prompts, hashes, indexes, per-category lists, `docs/AGENTS.md`, the directory below and the Claude Code pack) is
rebuilt by one command, and `--check` verifies nothing is stale.

```bash
python scripts/build_all.py            # rebuild everything derived
python scripts/build_all.py --check    # fail if anything is out of date
python -m unittest discover -s tests   # run the tests
```

**Change an agent's expertise:** edit `registry/expertise.json` (`agents` for one agent's focus line, `groups` for the field pack shared by a
group), then `python scripts/build_all.py`.

**Add an agent:** write a spec and run the tool; it validates, creates the manifest, adds the focus, aliases and evaluation cases, and rebuilds.

```json
{
  "id": "AGENT-435", "name": "Release Notes Agent", "category": "software-engineering", "group": "Software Engineering / Dev",
  "mission": "Write accurate release notes from merged changes",
  "method": "Read the merged changes, group them by user impact and verify each entry against the change itself",
  "gate": "Every note maps to a merged change and no merged user-facing change is missing",
  "focus": "Release notes: lead with user impact, link each entry to its change, call out breaking changes and migrations first, and never describe behavior you did not verify.",
  "capabilities": ["repository_read", "scoped_file_edit"],
  "skills": ["clear-communication"],
  "aliases": ["release notes", "changelog"]
}
```

```bash
python scripts/add_agent.py spec.json
```

**Add a skill:** create `skills/<name>/SKILL.md` with front matter (`name` equal to the folder name, `description` of 40-300 characters) and the
sections *When to apply*, *How to apply* and *Output expectation*; list it in the `skill_modules` of the agents that should load it (every
skill must be used by at least one agent); then `python scripts/build_all.py`.

**Improve routing for your phrasing:** add phrases to `registry/routing-aliases.json` (a leading `=` means exact phrase only) or words to
`registry/synonyms.json`. See `docs/ROUTING.md`.

## Skills

Plain folders `skills/<name>/SKILL.md` that follow the standard skill layout. Each agent loads the skills named in its manifest; every agent
loads `evidence-first-verification`.

<!-- SKILLS:START -->
| Skill | What it gives an agent |
| --- | --- |
| `anti-overengineering` | Detect unjustified abstraction, wrappers, extra dependencies, premature extensibility, and complexity that the task did not ask for. |
| `authorized-security-assessment` | Run security assessment inside written authorization: confirm scope and rules first, use non-destructive validation, and report only validated findings. |
| `browser-automation` | Drive a real browser reliably: use structured page snapshots, deterministic steps, evidence screenshots, and confirmation before irreversible actions. |
| `calibrated-reasoning` | Reason like a careful expert: grade evidence, separate observed from inferred from assumed, state confidence, and test your own answer before giving it. |
| `clear-communication` | Write answers people can act on: result first, plain words, exact details, honest limits and one focused question at most. |
| `continuous-learning-pattern` | Turn a repeated observation into a confidence-weighted candidate skill, and promote it to a reusable skill only after it is evaluated, not on first occurrence. |
| `cross-session-memory-pattern` | Persist project knowledge that is actually useful across sessions, with decay for stale facts, consolidation of duplicates, and provenance for everything stored. |
| `data-analysis-rigor` | Produce numbers that survive scrutiny: check grain and joins, reconcile totals, state definitions and uncertainty, and chart honestly. |
| `department-routing` | Route an incoming task to the specialist department (engineering, design, product, research, security, infrastructure, data, or other domain) before routing to an individual specialist within it. |
| `engineering-role-patterns` | Apply the planner / implementer / reviewer / tester / security-specialist split consistently, so no single role both builds and is the sole judge of its own work. |
| `evidence-first-verification` | Every material claim of success must map to a test, a build artifact, a log, a measurement, or another independently inspectable source — never to the claim itself. |
| `explicit-invocation` | Resolve a user's explicit request for a named agent or skill: exact ID or slug first, then fuzzy name match, and ask only when still ambiguous. |
| `gpu-compute-specialist` | Tune GPU and accelerator workloads from evidence: confirm the bottleneck on the device, fix memory and transfer behavior first, and verify numerical correctness after every change. |
| `incident-response-method` | Handle an incident in order: triage, contain, preserve evidence, eradicate, recover and learn, with a single timeline and recorded decisions. |
| `lean-change-discipline` | The smallest change that fully solves the task: scope listed first, no unrequested machinery, evidence over confidence, named shortcuts and a closing note on what was skipped and the remaining risk. |
| `live-model-connection` | Connect an adapter to any model endpoint, cloud or local: keep keys in the environment, pin the model, bound the call, and report connection failures precisely. |
| `minimum-sufficient-intelligence` | Prefer a deterministic script, a single tool call, or one focused model call before escalating to autonomous multi-step or multi-agent execution. |
| `multi-source-search` | Run several differently-phrased searches in parallel, deduplicate and cross-check results, and rank sources by authority and freshness. |
| `physical-ai-specialist` | Design and evaluate robotics and embodied-AI work safely: define the safety envelope first, validate in simulation, measure the sim-to-real gap and keep hardware changes reviewable. |
| `portable-skill-folder-pattern` | Package instructions, scripts, reference material, and resources for one capability as a single self-contained folder that any agent or host can load without extra wiring. |
| `progressive-skill-disclosure` | Expose only a skill's short description up front; load its full instructions and resources only once a task has actually matched that skill. |
| `reversibility-aware-autonomy` | Classify every consequential action's reversibility and blast radius before it executes, and scale caution — confirmation, dry-run, narrower scope — to match. |
| `root-cause-analysis` | Find the cause of a failure, not its symptom: reproduce, build the timeline, test one hypothesis at a time, fix the cause and prove it with a regression check. |
| `secure-code-review` | Review code for security defects by tracing untrusted input to sensitive sinks and checking authorization, secrets, cryptography and error handling on every path. |
| `signed-skill-governance` | Verify a skill's provenance, security review status, evaluation results, and trust metadata before it is promoted into active use by any agent. |
| `small-model-operation` | Get dependable work from small or local models: short prompts, one decision per call, strict JSON, host-side retrieval, and fail-closed verification. |
| `specialist-role-contracts` | Every specialist agent commits to a role-specific contract: the expertise it claims, the process it follows, the deliverable shape it produces, and the quality bar that gates completion. |
| `test-design` | Design tests that fail when the behavior is wrong: behavior first, boundaries, determinism, and a check that each test can actually fail. |
| `threat-modeling` | Model threats before choosing controls: assets, trust boundaries, entry points and attacker goals, ranked by realistic impact with mitigations and residual risk. |
| `tool-communication-protocol` | Exchange structured requests and responses between brain, model, and tools without ambiguity: validate every message, bound every call, never replay side effects. |
| `web-crawling` | Crawl a bounded set of pages politely and safely: respect scope, robots rules and rate limits, deduplicate, and stop at defined limits. |
| `web-research` | Plan and run live web research: decompose the question, search several sources, read primary pages, and report cited findings with dates. |
| `what-why-required` | Before any non-trivial line, block, or new file survives review, it must answer: what does it do, why is it needed, and is it actually required. |
<!-- SKILLS:END -->

`python scripts/agent_cli.py lean-audit <path>` runs a deterministic pre-scan (TODO/FIXME markers, long Python functions, duplicate blocks) that
the necessity-first review in `brain/LINE-CODE-AUDITOR.md` builds on; it is wired to AGENT-033, 086, 143 and 145.

## Agent directory

Every agent, grouped by category and field. A longer table with each agent's specialization is in [docs/AGENTS.md](docs/AGENTS.md), and the full
prompts are in `agents/<category>/AGENT-NNN/system-prompt.md`.

<!-- AGENT_SUMMARY:START -->
| Category | Groups | Agents |
| --- | --- | ---: |
| meta | Brain / Meta Agents, Agent-System Optimization, Governance, Communication / Coordination | 46 |
| memory-learning | Memory / Context / Learning, Skill Management | 29 |
| software-engineering | Software Engineering / Dev, Code Necessity / Anti-Overengineering, Code Understanding | 46 |
| computer-tools | Computer / Web / Tool, Document / Multimodal | 27 |
| research-science | Research / Scientific | 17 |
| data-knowledge | Data / Knowledge | 12 |
| cybersecurity | Cybersecurity / Safety, Reconnaissance / Attack Surface, Vulnerability Assessment, Defensive Security Operations, Security Engineering, Agent / LLM Security, Cyber Governance | 129 |
| verification-recovery | Verification / Quality, Recovery / Self-Correction, Assumption / Gap Hunters, Reality / Evidence, Failure Intelligence | 46 |
| infrastructure | Infrastructure / Operations, Environment / Setup, Workflow / Lifecycle, Economy / Efficiency | 61 |
| os-systems | OS / Systems Engineering | 22 |
<!-- AGENT_SUMMARY:END -->

<!-- AGENTS:START -->
### meta

**Brain / Meta Agents** (18)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-000 | Executive Activation Brain | Activate the smallest sufficient set of specialists as tasks become ready. |
| AGENT-001 | Master Orchestrator / Brain | Coordinate the complete user goal. |
| AGENT-002 | User Intent Interpreter | Recover the user's intended outcome. |
| AGENT-003 | Requirement Extractor | Extract testable requirements. |
| AGENT-004 | Ambiguity Resolver | Resolve consequential ambiguity. |
| AGENT-005 | Goal Formalizer | Convert intent into measurable goals. |
| AGENT-006 | Task Decomposer | Decompose work into executable tasks. |
| AGENT-007 | Strategic Planner | Choose an execution strategy. |
| AGENT-008 | Dynamic Replanner | Adapt an active plan to new evidence. |
| AGENT-009 | Agent Router | Route a task to the right specialist. |
| AGENT-010 | Agent Spawn Manager | Manage specialist lifecycle. |
| AGENT-011 | Parallel-Agent Manager | Coordinate concurrent specialists. |
| AGENT-012 | Dependency/DAG Manager | Maintain a dependency graph. |
| AGENT-013 | Priority Scheduler | Schedule work by priority. |
| AGENT-014 | Compute Usage Manager | Allocate task compute and spending. |
| AGENT-015 | Termination/Completion Judge | Judge whether work is complete. |
| AGENT-422 | Open-Source License Compliance Agent | Inventory software licensing obligations. |
| AGENT-429 | Agent and Skill Invocation Agent | Resolve explicit requests for a named agent or skill and hand over the task unchanged. |

**Agent-System Optimization** (8)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-173 | Agent Necessity Agent | Judge whether a new agent is needed. |
| AGENT-174 | Agent Merger | Merge overlapping agent responsibilities. |
| AGENT-175 | Agent Splitter | Split an overbroad agent role. |
| AGENT-176 | Tool-vs-Agent Judge | Choose between a tool and an agent. |
| AGENT-177 | Workflow-vs-Agent Judge | Choose between a workflow and an agent. |
| AGENT-178 | Agent ROI Evaluator | Evaluate agent return on investment. |
| AGENT-179 | Skill Discovery/Creation Agent | Discover or specify a missing skill. |
| AGENT-180 | Architecture Pruning Agent | Prune unnecessary architecture. |

**Governance** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-366 | Human Approval Controller | Manage required human approvals. |
| AGENT-367 | Action Risk Classifier | Classify action risk. |
| AGENT-368 | Reversibility Judge | Judge action reversibility. |
| AGENT-369 | Blast-Radius Estimator | Estimate an action's blast radius. |
| AGENT-370 | Least-Privilege Controller | Coordinate least-privilege policy. |
| AGENT-371 | Credential Scope Controller | Control credential scope. |
| AGENT-372 | Data Classification Agent | Classify data sensitivity. |
| AGENT-373 | Privacy/PII Agent | Minimize personal-data exposure. |
| AGENT-374 | Audit Agent | Audit system actions. |
| AGENT-375 | Policy Enforcement Agent | Enforce applicable policy decisions. |

**Communication / Coordination** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-376 | Agent Protocol Manager | Manage agent communication protocols. |
| AGENT-377 | Message Schema Validator | Validate inter-agent message schemas. |
| AGENT-378 | Agent Capability Advertiser | Advertise an agent's real capabilities. |
| AGENT-379 | Capability Discovery Agent | Discover available agent capabilities. |
| AGENT-380 | Handoff Validator | Validate a task handoff. |
| AGENT-381 | Shared-State Coordinator | Coordinate shared mutable state. |
| AGENT-382 | Conflict Resolution Agent | Resolve conflicting agent proposals. |
| AGENT-383 | Consensus Agent | Reach evidence-based multi-agent agreement. |
| AGENT-384 | Agent Reputation/Reliability Tracker | Track agent reliability. |
| AGENT-385 | Delegation Auditor | Audit delegated work. |

### memory-learning

**Memory / Context / Learning** (11)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-016 | Working-Memory Agent | Maintain current task state. |
| AGENT-017 | Long-Term Memory Agent | Maintain durable authorized knowledge. |
| AGENT-018 | Episodic Memory Agent | Record meaningful task episodes. |
| AGENT-019 | Semantic Memory Agent | Maintain reusable factual knowledge. |
| AGENT-020 | Session Summarizer | Summarize a session for continuity. |
| AGENT-021 | Context Retrieval Agent | Retrieve relevant prior context. |
| AGENT-022 | Context Compression Agent | Compress context without losing decisions. |
| AGENT-023 | Token Optimizer | Reduce token consumption. |
| AGENT-024 | Knowledge-Graph Agent | Maintain a knowledge graph. |
| AGENT-025 | Reflection/Learning Agent | Learn from observed outcomes. |
| AGENT-434 | Session Journal Agent | Keep a compact resumable record of what was asked, answered, required and left undone. |

**Skill Management** (18)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-333 | Skill Discovery Agent | Discover relevant reusable skills. |
| AGENT-334 | Skill Router | Route work to an appropriate skill. |
| AGENT-335 | Skill Composer | Compose compatible skills. |
| AGENT-336 | Skill Authoring Agent | Author a reusable skill specification. |
| AGENT-337 | Skill Critic | Critique a skill's instructions. |
| AGENT-338 | Skill Testing Agent | Test a skill against representative tasks. |
| AGENT-339 | Skill Benchmark Agent | Benchmark skill effectiveness. |
| AGENT-340 | Skill Version Manager | Version reusable skills. |
| AGENT-341 | Skill Dependency Agent | Manage skill dependencies. |
| AGENT-342 | Skill Conflict Detector | Detect conflicting skill instructions. |
| AGENT-343 | Skill Security Scanner | Scan skills for security risks. |
| AGENT-344 | Skill Provenance Agent | Record skill provenance. |
| AGENT-345 | Skill Trust Agent | Assess skill trustworthiness. |
| AGENT-346 | Skill Deprecation Agent | Deprecate obsolete skills. |
| AGENT-347 | Skill Deduplication Agent | Deduplicate overlapping skills. |
| AGENT-348 | Skill Compression Agent | Compress skill instructions. |
| AGENT-349 | Skill Marketplace/Registry Agent | Maintain a skill registry. |
| AGENT-350 | Skill Evolution Agent | Improve skills from evaluation evidence. |

### software-engineering

**Software Engineering / Dev** (28)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-026 | Software Architect | Design software architecture. |
| AGENT-027 | Coding Agent | Implement a bounded coding task. |
| AGENT-028 | Codebase Exploration Agent | Explore an unfamiliar codebase. |
| AGENT-029 | Repository Understanding Agent | Explain repository structure and operation. |
| AGENT-030 | Feature Implementation Agent | Implement an end-user feature. |
| AGENT-031 | Debugging Agent | Find and fix a software defect. |
| AGENT-032 | Refactoring Agent | Improve code structure safely. |
| AGENT-033 | Code Review Agent | Review a proposed code change. |
| AGENT-034 | Unit-Test Generator | Design meaningful unit tests. |
| AGENT-035 | Integration-Test Agent | Verify component integrations. |
| AGENT-036 | E2E Testing Agent | Verify complete user journeys. |
| AGENT-037 | Regression Testing Agent | Detect behavioral regressions. |
| AGENT-038 | Build/Compile Agent | Produce and diagnose compiled builds. |
| AGENT-039 | Dependency Manager | Manage project dependencies. |
| AGENT-040 | Package/Environment Agent | Prepare a project execution environment. |
| AGENT-041 | Git Agent | Perform scoped version-control work. |
| AGENT-042 | GitHub/PR Agent | Prepare reviewable pull requests. |
| AGENT-043 | CI/CD Agent | Design reliable delivery pipelines. |
| AGENT-044 | Deployment Agent | Deploy an authorized software release. |
| AGENT-045 | Performance/Profiling Agent | Diagnose application performance. |
| AGENT-406 | Frontend Engineering Agent | Build responsive user-facing web interfaces. |
| AGENT-407 | Backend Engineering Agent | Implement reliable application services and business logic. |
| AGENT-408 | UX/UI Design Agent | Design usable user journeys and interface systems. |
| AGENT-409 | Accessibility Engineering Agent | Identify and remediate accessibility barriers. |
| AGENT-410 | Mobile Application Engineering Agent | Build mobile applications for the requested platform. |
| AGENT-418 | Distributed Systems Engineering Agent | Design behavior across independently failing components. |
| AGENT-420 | Technical Documentation Agent | Create maintainable developer and user documentation. |
| AGENT-421 | Localization and Internationalization Agent | Adapt software for languages and regional conventions. |

**Code Necessity / Anti-Overengineering** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-141 | Line Necessity Agent | Assess whether a code line is necessary. |
| AGENT-142 | Line Explanation Agent | Explain individual lines of code. |
| AGENT-143 | Deletion Agent | Remove demonstrably unnecessary code. |
| AGENT-144 | Anti-Overengineering Agent | Prevent unnecessary engineering complexity. |
| AGENT-145 | Simplification Agent | Simplify a software solution. |
| AGENT-146 | Abstraction Justification Agent | Judge the need for an abstraction. |
| AGENT-147 | Dependency Necessity Agent | Judge whether a dependency is necessary. |
| AGENT-148 | Complexity Limit Agent | Manage software complexity limits. |
| AGENT-149 | Minimal Implementation Agent | Build the smallest complete implementation. |
| AGENT-150 | Code Duplication/Consolidation Agent | Consolidate duplicated code appropriately. |

**Code Understanding** (8)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-151 | Execution Trace Explainer | Explain an execution trace. |
| AGENT-152 | Variable Provenance Agent | Trace variable origins and transformations. |
| AGENT-153 | Function Contract Agent | Specify function contracts. |
| AGENT-154 | Dependency Graph Explainer | Explain dependency relationships. |
| AGENT-155 | State Mutation Tracker | Track state mutations. |
| AGENT-156 | Side-Effect Agent | Analyze side effects. |
| AGENT-157 | Error-Path Explainer | Explain error propagation. |
| AGENT-158 | Teach Me This Codebase Agent | Teach a codebase to a learner. |

### computer-tools

**Computer / Web / Tool** (17)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-046 | Browser Agent | Complete browser-based tasks. |
| AGENT-047 | Computer-Use Agent | Operate a computer interface. |
| AGENT-048 | GUI/Vision Navigation Agent | Navigate visual interfaces. |
| AGENT-049 | Terminal/Shell Agent | Run shell operations reliably. |
| AGENT-050 | File-System Agent | Manage user files and directories. |
| AGENT-051 | HTTP/API Agent | Interact with HTTP APIs. |
| AGENT-052 | MCP Agent | Coordinate MCP tool interactions. |
| AGENT-053 | External-Tool Discovery Agent | Discover an external tool capability. |
| AGENT-054 | API Discovery Agent | Discover an API's usable contract. |
| AGENT-055 | Authentication/Session Agent | Manage authorized authentication state. |
| AGENT-056 | Form/Workflow Automation Agent | Automate a form or workflow. |
| AGENT-057 | Sandbox Execution Agent | Execute code within isolation. |
| AGENT-426 | Web Crawl Agent | Crawl a bounded set of web pages and extract structured records. |
| AGENT-428 | Browser Automation Operator | Operate a real browser through structured snapshots with evidence and confirmation gates. |
| AGENT-430 | Live Model Connection Agent | Connect adapters to live model APIs and diagnose connection failures. |
| AGENT-432 | Claude Code Integration Agent | Install and verify the registry as Claude Code subagents and skills. |
| AGENT-433 | Local Model Operations Agent | Configure and operate small or local models so agents work reliably offline. |

**Document / Multimodal** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-101 | Document Reader | Read documents accurately. |
| AGENT-102 | PDF Agent | Work with PDF content and layout. |
| AGENT-103 | Spreadsheet Agent | Build or analyze spreadsheets. |
| AGENT-104 | Presentation Agent | Create coherent presentations. |
| AGENT-105 | OCR/Document-Vision Agent | Recover text from document images. |
| AGENT-106 | Image Understanding Agent | Interpret supplied images. |
| AGENT-107 | Image Generation Agent | Create images from a visual brief. |
| AGENT-108 | Audio Agent | Analyze or process audio. |
| AGENT-109 | Speech/Voice Agent | Transcribe or produce speech. |
| AGENT-110 | Video Understanding Agent | Understand video sequences. |

### research-science

**Research / Scientific** (17)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-058 | General Research Agent | Research a factual question. |
| AGENT-059 | Deep-Research Agent | Investigate a complex research problem. |
| AGENT-060 | Search Strategy Agent | Design an effective search strategy. |
| AGENT-061 | Literature-Review Agent | Synthesize a research literature. |
| AGENT-062 | Academic-Paper Finder | Find relevant academic papers. |
| AGENT-063 | Paper Reader/Extractor | Extract a paper's actual findings. |
| AGENT-064 | Citation Agent | Create accurate citations. |
| AGENT-065 | Hypothesis Generator | Generate falsifiable hypotheses. |
| AGENT-066 | Experiment Designer | Design an informative experiment. |
| AGENT-067 | Scientific Critic | Critique scientific reasoning. |
| AGENT-068 | Simulation Agent | Model and simulate a system. |
| AGENT-069 | Statistical Analysis Agent | Analyze data statistically. |
| AGENT-070 | Reproducibility Agent | Make a scientific result reproducible. |
| AGENT-071 | Scientific Report Writer | Write a scientific report. |
| AGENT-411 | Machine Learning Modeling Agent | Select and evaluate predictive modeling approaches. |
| AGENT-412 | Model Training and Fine-Tuning Agent | Design reproducible model training and adaptation runs. |
| AGENT-427 | Multi-Source Search Agent | Run parallel differently-phrased searches and cross-check results across independent sources. |

### data-knowledge

**Data / Knowledge** (12)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-072 | Data Analyst | Analyze a business or research dataset. |
| AGENT-073 | SQL Agent | Write and inspect SQL. |
| AGENT-074 | Database Agent | Design or maintain databases. |
| AGENT-075 | Data Engineering Agent | Design dependable data systems. |
| AGENT-076 | ETL/Pipeline Agent | Implement data transformation pipelines. |
| AGENT-077 | Data Cleaning Agent | Clean data transparently. |
| AGENT-078 | Visualization Agent | Visualize data clearly. |
| AGENT-079 | RAG Agent | Build grounded retrieval-augmented answers. |
| AGENT-080 | Vector Retrieval Agent | Retrieve semantically relevant vectors. |
| AGENT-081 | Knowledge-Base Agent | Maintain a usable knowledge base. |
| AGENT-082 | Structured-Extraction Agent | Extract structured information. |
| AGENT-419 | Event Streaming Engineering Agent | Build reliable event-driven data flows. |

### cybersecurity

**Cybersecurity / Safety** (18)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-083 | Security Orchestrator | Coordinate an authorized security review. |
| AGENT-084 | Threat-Modeling Agent | Model threats to an existing system. |
| AGENT-085 | Attack-Surface Mapper | Map a system's attack surface. |
| AGENT-086 | Secure-Code Review Agent | Review code for security defects. |
| AGENT-087 | Vulnerability Discovery Agent | Discover potential vulnerabilities. |
| AGENT-088 | Vulnerability Validation Agent | Validate individual vulnerability candidates. |
| AGENT-089 | Dependency/Supply-Chain Security Agent | Assess dependency and supply-chain security. |
| AGENT-090 | Secrets Detection Agent | Detect accidentally committed secrets. |
| AGENT-091 | SAST Agent | Run static security analysis. |
| AGENT-092 | Fuzzing Agent | Fuzz software in a controlled harness. |
| AGENT-093 | Security Patch Agent | Remediate a confirmed security defect. |
| AGENT-094 | Security Verification Agent | Verify security remediation. |
| AGENT-095 | Prompt-Injection Detector | Detect direct instruction attacks against agents. |
| AGENT-096 | Agent Permission Controller | Control agent permission requests. |
| AGENT-097 | Sandbox/Containment Agent | Design containment for risky execution. |
| AGENT-098 | SOC/Incident Analysis Agent | Analyze a security incident. |
| AGENT-099 | Threat-Intelligence Agent | Assess strategic threat intelligence. |
| AGENT-100 | Security Report Agent | Report security assessment results. |

**Reconnaissance / Attack Surface** (30)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-201 | Recon Orchestrator | Coordinate authorized reconnaissance. |
| AGENT-202 | Scope/Authorization Agent | Verify assessment authorization and scope. |
| AGENT-203 | Passive Recon Agent | Collect passive reconnaissance evidence. |
| AGENT-204 | Asset Discovery Agent | Discover assets within authorized scope. |
| AGENT-205 | Domain Recon Agent | Map domain-related infrastructure. |
| AGENT-206 | DNS Analysis Agent | Analyze DNS exposure and configuration. |
| AGENT-207 | Subdomain Inventory Agent | Maintain an authorized subdomain inventory. |
| AGENT-208 | Certificate/TLS Recon Agent | Inventory certificate and TLS exposure. |
| AGENT-209 | IP/Network Inventory Agent | Inventory IP addresses and networks. |
| AGENT-210 | ASN/Infrastructure Agent | Analyze ASN and infrastructure relationships. |
| AGENT-211 | Cloud Asset Recon Agent | Inventory authorized cloud assets. |
| AGENT-212 | Web Recon Agent | Map a web application's visible surface. |
| AGENT-213 | API Recon Agent | Inventory an API surface. |
| AGENT-214 | Technology Fingerprinting Agent | Identify deployed technologies cautiously. |
| AGENT-215 | Endpoint Inventory Agent | Maintain endpoint inventory. |
| AGENT-216 | OS Recon Agent | Identify host operating-system exposure. |
| AGENT-217 | Service Inventory Agent | Inventory exposed services. |
| AGENT-218 | Port/Protocol Assessment Agent | Assess permitted ports and protocols. |
| AGENT-219 | Authentication Surface Agent | Map authentication entry points. |
| AGENT-220 | Identity Surface Agent | Map identity-related exposure. |
| AGENT-221 | Email Security Recon Agent | Assess email security configuration. |
| AGENT-222 | Repository Exposure Agent | Find repository exposure. |
| AGENT-223 | Secret Exposure Agent | Investigate exposed secret candidates. |
| AGENT-224 | Metadata Exposure Agent | Assess metadata leakage. |
| AGENT-225 | Dependency Exposure Agent | Map exposed dependency information. |
| AGENT-226 | Supply-Chain Surface Agent | Map supply-chain trust boundaries. |
| AGENT-227 | Mobile Surface Agent | Map mobile application exposure. |
| AGENT-228 | IoT/Embedded Surface Agent | Map embedded and IoT exposure. |
| AGENT-229 | External Attack-Surface Mapper | Consolidate external attack-surface findings. |
| AGENT-230 | Recon Evidence/Report Agent | Document reconnaissance evidence. |

**Vulnerability Assessment** (30)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-231 | Web Security Assessment | Assess web application security. |
| AGENT-232 | API Security Assessment | Assess API security controls. |
| AGENT-233 | Authentication Assessment | Assess authentication controls. |
| AGENT-234 | Authorization/Access-Control Assessment | Assess authorization boundaries. |
| AGENT-235 | Session Security Assessment | Assess session management. |
| AGENT-236 | Input-Validation Assessment | Assess input validation boundaries. |
| AGENT-237 | Injection Detection | Detect injection weaknesses safely. |
| AGENT-238 | XSS Analysis | Analyze script injection risk. |
| AGENT-239 | SSRF Analysis | Analyze server-side request exposure. |
| AGENT-240 | File/Path Security Assessment | Assess file and path controls. |
| AGENT-241 | Upload Security Assessment | Assess file-upload security. |
| AGENT-242 | Cryptographic Configuration Assessment | Assess cryptographic configuration. |
| AGENT-243 | TLS Assessment | Assess TLS deployment. |
| AGENT-244 | Network Configuration Assessment | Assess network security configuration. |
| AGENT-245 | OS Vulnerability Assessment | Assess OS vulnerability exposure. |
| AGENT-246 | Service Misconfiguration Assessment | Assess service misconfiguration. |
| AGENT-247 | Container Security Assessment | Assess container security. |
| AGENT-248 | Kubernetes Security Assessment | Assess Kubernetes security. |
| AGENT-249 | Cloud Configuration Assessment | Assess cloud configuration security. |
| AGENT-250 | IAM Assessment | Assess identity and access management. |
| AGENT-251 | Database Security Assessment | Assess database security. |
| AGENT-252 | Dependency/CVE Assessment | Assess dependency vulnerability applicability. |
| AGENT-253 | Supply-Chain Assessment | Assess supply-chain assurance. |
| AGENT-254 | Secrets Assessment | Assess secrets handling. |
| AGENT-255 | Source-Code SAST Agent | Perform source-level static security triage. |
| AGENT-256 | Infrastructure-as-Code Security Agent | Assess infrastructure-as-code security. |
| AGENT-257 | Mobile Security Assessment | Assess mobile application security. |
| AGENT-258 | Firmware/Embedded Assessment | Assess firmware and embedded security. |
| AGENT-259 | Vulnerability Correlation Agent | Correlate vulnerability findings. |
| AGENT-260 | Vulnerability Validation Agent | Validate correlated assessment findings. |

**Defensive Security Operations** (20)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-261 | SOC Orchestrator | Coordinate security operations. |
| AGENT-262 | Security Telemetry Agent | Assess security telemetry coverage. |
| AGENT-263 | Log Analysis Agent | Analyze security logs. |
| AGENT-264 | SIEM Analysis Agent | Investigate SIEM detections. |
| AGENT-265 | Alert Triage Agent | Triage security alerts. |
| AGENT-266 | Detection Engineering Agent | Engineer detection rules. |
| AGENT-267 | Threat Hunting Agent | Conduct hypothesis-driven threat hunting. |
| AGENT-268 | Threat Intelligence Agent | Operationalize threat intelligence for detection. |
| AGENT-269 | IOC Analysis Agent | Analyze indicators of compromise. |
| AGENT-270 | Malware Analysis Agent | Analyze suspicious software safely. |
| AGENT-271 | Behavioral Analysis Agent | Analyze suspicious behavior sequences. |
| AGENT-272 | Endpoint Detection Agent | Investigate endpoint detections. |
| AGENT-273 | Network Detection Agent | Investigate network detections. |
| AGENT-274 | Cloud Detection Agent | Investigate cloud security events. |
| AGENT-275 | Identity Threat Detection Agent | Detect identity-based threats. |
| AGENT-276 | Incident Triage Agent | Triage a suspected incident. |
| AGENT-277 | Incident Response Agent | Coordinate authorized incident response. |
| AGENT-278 | Forensics Agent | Analyze forensic evidence. |
| AGENT-279 | Containment/Recovery Agent | Contain and recover compromised systems. |
| AGENT-280 | Post-Incident Analysis Agent | Analyze an incident after resolution. |

**Security Engineering** (15)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-281 | Security Architecture Agent | Design secure system architecture. |
| AGENT-282 | Threat Modeling Agent | Threat-model a proposed design. |
| AGENT-283 | Secure Design Reviewer | Review a design for security weaknesses. |
| AGENT-284 | Secure Code Reviewer | Review security-sensitive code changes. |
| AGENT-285 | Security Requirements Agent | Specify security requirements. |
| AGENT-286 | Security Test Designer | Design security verification tests. |
| AGENT-287 | Security Regression Agent | Prevent recurrence of security defects. |
| AGENT-288 | Patch Generation Agent | Generate a security remediation patch. |
| AGENT-289 | Patch Verification Agent | Independently verify a security patch. |
| AGENT-290 | Hardening Agent | Harden application and service deployments. |
| AGENT-291 | Secrets Management Agent | Design secure secrets management. |
| AGENT-292 | PKI/Cryptography Configuration Agent | Configure PKI and cryptographic lifecycle. |
| AGENT-293 | Zero-Trust Architecture Agent | Design least-trust access architecture. |
| AGENT-294 | Security Documentation Agent | Write maintainable security documentation. |
| AGENT-295 | Security Assurance Agent | Assess security assurance evidence. |

**Agent / LLM Security** (15)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-296 | Prompt-Injection Detector | Detect prompt injection across agent workflows. |
| AGENT-297 | Indirect Prompt-Injection Detector | Detect injection embedded in external content. |
| AGENT-298 | Tool-Output Sanitization Agent | Sanitize tool output for safe consumption. |
| AGENT-299 | Untrusted-Content Classifier | Classify content trust and origin. |
| AGENT-300 | Tool Permission Agent | Evaluate tool-specific permission requests. |
| AGENT-301 | Least-Privilege Agent | Reduce excessive capability grants. |
| AGENT-302 | Agent Identity/Authentication Agent | Design agent identity and authentication. |
| AGENT-303 | Inter-Agent Trust Agent | Evaluate inter-agent trust boundaries. |
| AGENT-304 | Memory-Poisoning Detector | Detect attempts to poison persistent memory. |
| AGENT-305 | RAG-Poisoning Detector | Detect retrieval corpus poisoning. |
| AGENT-306 | Data-Exfiltration Prevention Agent | Prevent unauthorized data disclosure. |
| AGENT-307 | Secret-Leak Prevention Agent | Detect secret leakage in outputs. |
| AGENT-308 | Agent Behavior Monitor | Monitor agent behavior for policy deviations. |
| AGENT-309 | Agent Sandbox Agent | Specify agent runtime isolation. |
| AGENT-310 | AI Security Red-Team/Evaluation Agent | Evaluate AI security in an authorized test environment. |

**Cyber Governance** (1)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-311 | Cyber Engagement Controller | Control a cyber engagement's lifecycle. |

### verification-recovery

**Verification / Quality** (12)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-111 | General Verifier | Independently verify a result. |
| AGENT-112 | Fact Checker | Check factual assertions. |
| AGENT-113 | Source/Citation Verifier | Verify sources and citations. |
| AGENT-114 | Logical Consistency Checker | Check internal logical consistency. |
| AGENT-115 | Requirement-Satisfaction Judge | Judge requirement satisfaction. |
| AGENT-116 | Critic Agent | Critique the quality of a result. |
| AGENT-117 | Adversarial Critic | Challenge a proposed solution adversarially. |
| AGENT-118 | Hallucination/Grounding Checker | Detect unsupported generated claims. |
| AGENT-119 | Result Comparator | Compare candidate results fairly. |
| AGENT-120 | Final QA Agent | Perform final delivery quality assurance. |
| AGENT-425 | Artifact Integrity and Provenance Agent | Verify artifacts across creation and handoffs. |
| AGENT-431 | Tool Communication Verifier | Verify that requests and responses between brain, model and tools follow the contract. |

**Recovery / Self-Correction** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-121 | Failure Detector | Detect task failures promptly. |
| AGENT-122 | Root-Cause Analyzer | Identify underlying failure causes. |
| AGENT-123 | Retry Controller | Manage bounded retries. |
| AGENT-124 | Alternative-Strategy Generator | Find viable alternative strategies. |
| AGENT-125 | Replanning Agent | Recover a failed workflow through replanning. |
| AGENT-126 | Tool-Failure Recovery Agent | Recover from tool failures. |
| AGENT-127 | Model-Fallback Agent | Select a model fallback. |
| AGENT-128 | Context-Recovery Agent | Recover lost task context. |
| AGENT-129 | Checkpoint/Rollback Agent | Manage task checkpoints and rollback. |
| AGENT-130 | Deadlock/Loop Detector | Detect deadlocks and repeated loops. |

**Assumption / Gap Hunters** (8)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-159 | Assumption Hunter | Find hidden assumptions. |
| AGENT-160 | Unknown-Unknown Hunter | Explore overlooked risk categories. |
| AGENT-161 | Requirement Gap Agent | Find gaps between requirements and implementation. |
| AGENT-162 | Environment Gap Agent | Find environmental prerequisites that are missing. |
| AGENT-163 | Contradiction Hunter | Find contradictions across artifacts. |
| AGENT-164 | Missing Requirement Agent | Identify necessary but unstated requirements. |
| AGENT-165 | Boundary-Condition Hunter | Find boundary-condition failures. |
| AGENT-166 | Counterexample Generator | Construct counterexamples to claims. |

**Reality / Evidence** (6)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-167 | Reality Verification Agent | Verify claims against actual system state. |
| AGENT-168 | Evidence Collector | Collect evidence for task conclusions. |
| AGENT-169 | Claim-to-Evidence Mapper | Map claims to evidence. |
| AGENT-170 | Deployment Reality Agent | Verify deployment in its real target. |
| AGENT-171 | User-Intent Confirmation Agent | Confirm alignment with user intent. |
| AGENT-172 | False-Success Detector | Detect misleading success signals. |

**Failure Intelligence** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-386 | Failure Taxonomy Agent | Classify failures consistently. |
| AGENT-387 | Failure Fingerprinting Agent | Fingerprint recurring failures. |
| AGENT-388 | Repeated-Failure Detector | Detect repeated failed attempts. |
| AGENT-389 | Root-Cause Knowledge Agent | Maintain root-cause knowledge. |
| AGENT-390 | Failure-to-Eval Agent | Turn failures into evaluation cases. |
| AGENT-391 | Failure-to-Skill Agent | Turn recurring failures into skill improvements. |
| AGENT-392 | Failure-to-Test Agent | Turn defects into regression tests. |
| AGENT-393 | Failure-to-Guardrail Agent | Turn failures into protective controls. |
| AGENT-394 | Failure-to-Documentation Agent | Turn incidents into useful documentation. |
| AGENT-395 | Failure Prevention Agent | Prevent known failure classes. |

### infrastructure

**Infrastructure / Operations** (15)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-131 | Observability Agent | Define system observability. |
| AGENT-132 | Logging Agent | Design useful application logging. |
| AGENT-133 | Trace Analyzer | Analyze distributed execution traces. |
| AGENT-134 | Cost Monitor | Monitor operational cost. |
| AGENT-135 | Latency Optimizer | Reduce workflow latency. |
| AGENT-136 | Model Selector | Choose an appropriate model. |
| AGENT-137 | Tool Selector | Choose the best available tool. |
| AGENT-138 | Resource Allocator | Allocate infrastructure resources. |
| AGENT-139 | Health Monitor | Monitor service health. |
| AGENT-140 | Evaluation/Benchmark Agent | Evaluate system performance and quality. |
| AGENT-413 | MLOps and Model Lifecycle Agent | Operate versioned machine-learning lifecycles. |
| AGENT-414 | Model Inference and Serving Agent | Serve model predictions within quality and resource limits. |
| AGENT-415 | GPU and Accelerator Computing Agent | Optimize accelerator workloads. |
| AGENT-423 | Backup and Restore Engineering Agent | Design and verify usable backups. |
| AGENT-424 | Disaster Recovery Engineering Agent | Plan service recovery after major disruption. |

**Environment / Setup** (21)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-312 | Environment Bootstrap Agent | Bootstrap a working environment. |
| AGENT-313 | Prerequisite Inspector | Inspect setup prerequisites. |
| AGENT-314 | Runtime Setup Agent | Set up an application runtime. |
| AGENT-315 | Dependency Resolver | Resolve environment dependencies. |
| AGENT-316 | Environment Reproducer | Reproduce a reported environment. |
| AGENT-317 | Configuration Agent | Manage application configuration. |
| AGENT-318 | Secrets Setup Agent | Set up secure secret references. |
| AGENT-319 | Permission Setup Agent | Set up required permissions. |
| AGENT-320 | Sandbox Provisioner | Provision an isolated execution workspace. |
| AGENT-321 | Workspace Agent | Prepare and manage task workspaces. |
| AGENT-322 | Scaffolding Agent | Create a project scaffold. |
| AGENT-323 | Installation Agent | Install software safely. |
| AGENT-324 | Setup Verification Agent | Verify completed setup. |
| AGENT-325 | Environment Repair Agent | Repair a broken environment. |
| AGENT-326 | Environment Drift Detector | Detect environment drift. |
| AGENT-327 | Migration Agent | Migrate data or environment state. |
| AGENT-328 | Upgrade Agent | Upgrade a system component. |
| AGENT-329 | Rollback Agent | Roll back a failed environment change. |
| AGENT-330 | Compatibility Agent | Evaluate component compatibility. |
| AGENT-331 | Reproducibility Agent | Make infrastructure setup reproducible. |
| AGENT-332 | Bootstrap Optimizer | Optimize bootstrap time and reliability. |

**Workflow / Lifecycle** (15)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-351 | Prototype Agent | Build a focused prototype. |
| AGENT-352 | Build Agent | Produce a release build. |
| AGENT-353 | Evaluation Designer | Design an evaluation program. |
| AGENT-354 | Dataset/Eval Generator | Generate evaluation datasets. |
| AGENT-355 | Benchmark Runner | Run benchmarks reproducibly. |
| AGENT-356 | Regression Detector | Detect quality regressions. |
| AGENT-357 | Deployment Readiness Agent | Judge deployment readiness. |
| AGENT-358 | Release Agent | Prepare and execute an authorized release. |
| AGENT-359 | Canary Agent | Evaluate a canary release. |
| AGENT-360 | Production Validation Agent | Validate production behavior. |
| AGENT-361 | Observability Setup Agent | Install observability instrumentation. |
| AGENT-362 | Production Drift Agent | Detect production behavior drift. |
| AGENT-363 | Incident Rollback Agent | Roll back a production incident. |
| AGENT-364 | Postmortem Agent | Write a blameless operational postmortem. |
| AGENT-365 | Continuous Improvement Agent | Drive continuous operational improvement. |

**Economy / Efficiency** (10)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-396 | Token Accountant | Account for token consumption. |
| AGENT-397 | Compute Accountant | Account for compute resources. |
| AGENT-398 | Tool-Call Accountant | Account for tool-call usage. |
| AGENT-399 | Latency Accountant | Account for end-to-end latency. |
| AGENT-400 | Cache Manager | Manage reusable cached results. |
| AGENT-401 | Result Reuse Agent | Reuse previous results safely. |
| AGENT-402 | Duplicate-Work Detector | Detect duplicated work. |
| AGENT-403 | Parallelization Judge | Judge whether work should run in parallel. |
| AGENT-404 | Model Escalation Agent | Escalate model capability when justified. |
| AGENT-405 | Cost/Quality Optimizer | Optimize cost against output quality. |

### os-systems

**OS / Systems Engineering** (22)

| ID | Agent | What it does |
| --- | --- | --- |
| AGENT-181 | OS Orchestrator | Coordinate operating-system administration. |
| AGENT-182 | Linux Expert | Diagnose and administer Linux systems. |
| AGENT-183 | Windows Expert | Diagnose and administer Windows systems. |
| AGENT-184 | macOS Expert | Diagnose and administer macOS systems. |
| AGENT-185 | Kernel Analysis Agent | Analyze kernel-level behavior. |
| AGENT-186 | Process Analyzer | Analyze operating-system processes. |
| AGENT-187 | Service/Daemon Agent | Manage services and daemons. |
| AGENT-188 | Filesystem Agent | Diagnose filesystem behavior. |
| AGENT-189 | Storage Agent | Analyze storage capacity and reliability. |
| AGENT-190 | Memory/CPU Profiler | Profile CPU and memory pressure. |
| AGENT-191 | Network Configuration Agent | Configure host networking. |
| AGENT-192 | Package Manager Agent | Manage operating-system packages. |
| AGENT-193 | Shell Automation Agent | Automate shell workflows. |
| AGENT-194 | Environment/Runtime Agent | Resolve runtime environment problems. |
| AGENT-195 | Container Agent | Build and operate containers. |
| AGENT-196 | VM/Hypervisor Agent | Manage virtual-machine environments. |
| AGENT-197 | OS Hardening Agent | Harden operating-system configuration. |
| AGENT-198 | OS Troubleshooter | Troubleshoot cross-component OS failures. |
| AGENT-199 | OS Performance Agent | Optimize operating-system performance. |
| AGENT-200 | OS Recovery Agent | Recover an operating system. |
| AGENT-416 | Robotics and Physical AI Agent | Design and evaluate embodied control workflows. |
| AGENT-417 | Real-Time and Embedded Engineering Agent | Implement time-bounded embedded behavior. |
<!-- AGENTS:END -->

## Quality, testing and limits

- **Automated tests** (`python -m unittest discover -s tests -v`; results recorded in `evals/BRAIN-TEST-RESULTS.json`) cover the controller,
  the adapter against local mock servers that imitate Anthropic, OpenAI-compatible servers, Ollama and a SearXNG endpoint (including weak-model
  behavior), host web tools, the CLI, the Claude Code pack, strict plan and skill handling, routing quality, and the content of every prompt,
  expertise pack and skill. Every agent is also round-tripped through the adapter on the smallest and the full profile.
- **Routing** is lexical with stemming, a small synonym list and curated aliases. On 30 requests that were never used to tune it, it sent
  a third to the right agent automatically, about one in six to a different agent and half to a candidate list, with a suitable agent in the
  top three 24 times in 30; every agent resolves from its own name and mission and unrelated requests are not forced. Numbers and method:
  `docs/ROUTING.md`. For important work name the agent.
- **Not tested here:** a real model of any kind (none was available in the build environment), a real browser, Claude Code loading the pack, and
  how any agent performs on real tasks. The 1,302 evaluation specifications in `evals/agent-cases.json` have not been run against a model. A
  small model's answers will be weaker than a large model's; the design keeps its output checkable and fails closed rather than making it smarter.
  Run `check-live` against your own model first.
- The prompts encode expert practice, but nothing here proves an agent is an expert. Treat output as a skilled draft that still needs the
  verification the agent's completion gate asks for.

## Safety

- Cybersecurity agents are for owned systems, labs, exercises and explicitly authorized assessments, non-destructive by default. AGENT-311
  checks authorization and scope before cyber activity; no authorization means no action.
- Page text, documents, search results and tool output are data. They cannot change an agent's authority or permissions.
- A manifest or prompt does not enforce isolation. The host enforces permissions, tool allowlists, credentials and sandboxing.
- Web fetches resolve the host before connecting; a hostile DNS server could in theory rebind it. For sensitive environments run web-enabled
  tasks in a network-isolated sandbox.
- Do not commit keys. The adapter reads them from the environment only.

## Troubleshooting

`check-live` and failed calls name the failure:

| Failure | Meaning and fix |
| --- | --- |
| `network_error` | Server not reachable. For a local model, start it (`ollama serve`) and check `--base-url` |
| `timeout` | The model did not answer in time. Raise `LLM_TIMEOUT`, use a smaller profile or a faster model |
| `missing_model` | No model set or several installed. Set `LLM_MODEL` (the message lists the choices) |
| `missing_key` / `auth_rejected` | Set `ANTHROPIC_API_KEY`, `LLM_API_KEY` or `OPENAI_API_KEY`; check the key |
| `rate_limited` / `server_error` | Provider side. Retry later |
| `model_or_endpoint_not_found` | Wrong model name or base URL |
| `malformed_reply` | The endpoint returned something that was not JSON |
| `bad_config` / `command_failed` | `LLM_PROVIDER` unknown, or `LLM_COMMAND` is not a JSON array or the program failed |
| `invalid_plan` | The model's plan failed validation (reason included). Write the plan by hand or use a stronger model |
| `Declared skill module is missing` | A manifest lists a skill file that is not present. Restore it or fix `skill_modules` |
| `needs_selection` | Several agents fit. Pick one from the list, or call it by ID |
| Task `blocked`: Model temporarily unavailable | The provider timed out or rate-limited. Run again with `--resume`; finished work is kept |

## Repository layout

```
LICENSE, assets/                       logo.svg (full logo), logo-mark.svg (icon); LICENSE is Apache 2.0
agents/<category>/AGENT-NNN/   system-prompt.md (generated) and manifest.json (source)
skills/<name>/SKILL.md         skills
.claude/                       generated Claude Code pack (agents, skills)
registry/                      expertise.json (source), agents.json, agents.csv, prompt-index.json, role-contracts.txt (generated),
                               routing-aliases.json, synonyms.json, agent-manifest.schema.json, browser and MCP connection data
brain/                         runtime.py (controller) and design notes
.agentic/                      created at run time: saved runs, journals, briefs and sessions (git-ignored)
scripts/                       agent_cli.py, build_all.py, build_prompts.py, build_catalog.py, add_agent.py, claude_code_pack.py
tools/                         webtools.py (fetch, search, crawl for any model)
examples/                      llm_adapter.py, runtime configs, sample plan
browser/, mcp/, workflows/, policies/, memory/   connection profiles, workflow notes and policies
evals/                         evaluation specifications and test records
docs/                          AGENTS.md, ROUTING.md, COVERAGE.md, COUNTS.md, BRAIN-RUNTIME.md, TASK-CONTRACT.md
tests/                         automated tests
```

## Publishing notes

This project is licensed under the [Apache License 2.0](LICENSE). `.github/workflows/tests.yml` runs the tests and the drift checks on every push.
