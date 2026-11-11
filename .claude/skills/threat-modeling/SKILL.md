---
name: threat-modeling
description: "Model threats before choosing controls: assets, trust boundaries, entry points and attacker goals, ranked by realistic impact with mitigations and residual risk."
---

# Threat Modeling

## When to apply
Designing or reviewing a system, feature or integration that handles sensitive data, authority or external input.

## How to apply
1. Describe the system: components, data flows, data stores and who or what crosses each boundary.
2. List assets worth protecting (data, access, availability, reputation) and the attacker goals against them.
3. Mark trust boundaries. Each flow that crosses one is a place to ask: who is this, what may they do, and what happens on malformed input?
4. For every element and flow, enumerate threats by category (spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege).
5. Rank by likelihood and impact in this environment. A threat that needs a capability the attacker lacks ranks low.
6. For the high ones choose a mitigation that breaks the attack path (remove the exposure, authenticate, authorize, validate, isolate, log) and say how to verify it.
7. Record accepted risks with an owner, and revisit the model when the design changes.

## Anti-patterns
- A flat list of every conceivable threat with no ranking.
- Controls chosen first, threats justified afterward.
- A diagram that omits the third-party and administrative paths.

## Output expectation
A short data-flow description, ranked threats with mitigations and verification steps, accepted risks with owners, and the assumptions the model depends on.
