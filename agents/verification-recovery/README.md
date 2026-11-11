# verification-recovery

46 definitions in 5 groups. Each entry links to the exact system prompt.

## Verification / Quality

- [AGENT-111 — General Verifier](AGENT-111/system-prompt.md) — Independently verify a result.
- [AGENT-112 — Fact Checker](AGENT-112/system-prompt.md) — Check factual assertions.
- [AGENT-113 — Source/Citation Verifier](AGENT-113/system-prompt.md) — Verify sources and citations.
- [AGENT-114 — Logical Consistency Checker](AGENT-114/system-prompt.md) — Check internal logical consistency.
- [AGENT-115 — Requirement-Satisfaction Judge](AGENT-115/system-prompt.md) — Judge requirement satisfaction.
- [AGENT-116 — Critic Agent](AGENT-116/system-prompt.md) — Critique the quality of a result.
- [AGENT-117 — Adversarial Critic](AGENT-117/system-prompt.md) — Challenge a proposed solution adversarially.
- [AGENT-118 — Hallucination/Grounding Checker](AGENT-118/system-prompt.md) — Detect unsupported generated claims.
- [AGENT-119 — Result Comparator](AGENT-119/system-prompt.md) — Compare candidate results fairly.
- [AGENT-120 — Final QA Agent](AGENT-120/system-prompt.md) — Perform final delivery quality assurance.
- [AGENT-425 — Artifact Integrity and Provenance Agent](AGENT-425/system-prompt.md) — Verify artifacts across creation and handoffs.
- [AGENT-431 — Tool Communication Verifier](AGENT-431/system-prompt.md) — Verify that requests and responses between brain, model and tools follow the contract.

## Recovery / Self-Correction

- [AGENT-121 — Failure Detector](AGENT-121/system-prompt.md) — Detect task failures promptly.
- [AGENT-122 — Root-Cause Analyzer](AGENT-122/system-prompt.md) — Identify underlying failure causes.
- [AGENT-123 — Retry Controller](AGENT-123/system-prompt.md) — Manage bounded retries.
- [AGENT-124 — Alternative-Strategy Generator](AGENT-124/system-prompt.md) — Find viable alternative strategies.
- [AGENT-125 — Replanning Agent](AGENT-125/system-prompt.md) — Recover a failed workflow through replanning.
- [AGENT-126 — Tool-Failure Recovery Agent](AGENT-126/system-prompt.md) — Recover from tool failures.
- [AGENT-127 — Model-Fallback Agent](AGENT-127/system-prompt.md) — Select a model fallback.
- [AGENT-128 — Context-Recovery Agent](AGENT-128/system-prompt.md) — Recover lost task context.
- [AGENT-129 — Checkpoint/Rollback Agent](AGENT-129/system-prompt.md) — Manage task checkpoints and rollback.
- [AGENT-130 — Deadlock/Loop Detector](AGENT-130/system-prompt.md) — Detect deadlocks and repeated loops.

## Assumption / Gap Hunters

- [AGENT-159 — Assumption Hunter](AGENT-159/system-prompt.md) — Find hidden assumptions.
- [AGENT-160 — Unknown-Unknown Hunter](AGENT-160/system-prompt.md) — Explore overlooked risk categories.
- [AGENT-161 — Requirement Gap Agent](AGENT-161/system-prompt.md) — Find gaps between requirements and implementation.
- [AGENT-162 — Environment Gap Agent](AGENT-162/system-prompt.md) — Find environmental prerequisites that are missing.
- [AGENT-163 — Contradiction Hunter](AGENT-163/system-prompt.md) — Find contradictions across artifacts.
- [AGENT-164 — Missing Requirement Agent](AGENT-164/system-prompt.md) — Identify necessary but unstated requirements.
- [AGENT-165 — Boundary-Condition Hunter](AGENT-165/system-prompt.md) — Find boundary-condition failures.
- [AGENT-166 — Counterexample Generator](AGENT-166/system-prompt.md) — Construct counterexamples to claims.

## Reality / Evidence

- [AGENT-167 — Reality Verification Agent](AGENT-167/system-prompt.md) — Verify claims against actual system state.
- [AGENT-168 — Evidence Collector](AGENT-168/system-prompt.md) — Collect evidence for task conclusions.
- [AGENT-169 — Claim-to-Evidence Mapper](AGENT-169/system-prompt.md) — Map claims to evidence.
- [AGENT-170 — Deployment Reality Agent](AGENT-170/system-prompt.md) — Verify deployment in its real target.
- [AGENT-171 — User-Intent Confirmation Agent](AGENT-171/system-prompt.md) — Confirm alignment with user intent.
- [AGENT-172 — False-Success Detector](AGENT-172/system-prompt.md) — Detect misleading success signals.

## Failure Intelligence

- [AGENT-386 — Failure Taxonomy Agent](AGENT-386/system-prompt.md) — Classify failures consistently.
- [AGENT-387 — Failure Fingerprinting Agent](AGENT-387/system-prompt.md) — Fingerprint recurring failures.
- [AGENT-388 — Repeated-Failure Detector](AGENT-388/system-prompt.md) — Detect repeated failed attempts.
- [AGENT-389 — Root-Cause Knowledge Agent](AGENT-389/system-prompt.md) — Maintain root-cause knowledge.
- [AGENT-390 — Failure-to-Eval Agent](AGENT-390/system-prompt.md) — Turn failures into evaluation cases.
- [AGENT-391 — Failure-to-Skill Agent](AGENT-391/system-prompt.md) — Turn recurring failures into skill improvements.
- [AGENT-392 — Failure-to-Test Agent](AGENT-392/system-prompt.md) — Turn defects into regression tests.
- [AGENT-393 — Failure-to-Guardrail Agent](AGENT-393/system-prompt.md) — Turn failures into protective controls.
- [AGENT-394 — Failure-to-Documentation Agent](AGENT-394/system-prompt.md) — Turn incidents into useful documentation.
- [AGENT-395 — Failure Prevention Agent](AGENT-395/system-prompt.md) — Prevent known failure classes.
