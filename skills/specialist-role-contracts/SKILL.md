---
name: specialist-role-contracts
description: "Every specialist agent commits to a role-specific contract: the expertise it claims, the process it follows, the deliverable shape it produces, and the quality bar that gates completion."
---

# Specialist Role Contracts

Every specialist agent commits to a role-specific contract: the expertise it claims, the process it
follows, the deliverable shape it produces, and the quality bar that gates completion.

## When to apply
Before an agent is activated, and again before its output is accepted, so the contract — not vibes —
decides whether the work is done.

## How to apply
1. Read the agent's `mission`, `spawn_when`, and `verification` fields as the contract, not just color text.
2. Confirm the deliverable matches the manifest's `output_contract.required` fields exactly.
3. Reject outputs with status `completed` that lack the evidence their own `verification` entries require.
4. Route disputed or borderline outputs to that department's verifier agent rather than resolving in place.

## Anti-patterns
- Treating `mission` as a suggestion once an agent starts improvising outside its declared scope.
- Accepting "it works" without the evidence the manifest's verification entries name.

## Output expectation
A pass/fail against the contract, not a subjective quality opinion.
