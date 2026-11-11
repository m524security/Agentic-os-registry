---
name: incident-response-method
description: "Handle an incident in order: triage, contain, preserve evidence, eradicate, recover and learn, with a single timeline and recorded decisions."
---

# Incident Response Method

## When to apply
A suspected or confirmed security or reliability incident: compromised account, malware, data exposure, outage or integrity failure.

## How to apply
1. Triage: is it real, what is affected, how bad, how fast is it spreading, and who must be told now?
2. Open one timeline and decision log. Record time (with time zone), source and confidence for every entry.
3. Preserve evidence before changing state: snapshots, logs, memory or disk images as appropriate, with hashes and handling notes.
4. Contain in proportion to confidence and blast radius (isolate hosts, revoke credentials, block indicators), choosing the least disruptive step that stops the spread.
5. Scope: find the initial access, what the actor did and what data or systems they touched, from independent sources.
6. Eradicate the cause and every persistence mechanism found, rebuild from known-good sources where trust is lost, and verify the access is actually gone.
7. Recover in stages with monitoring, then run a blameless review that produces owned, dated actions and new detections.

## Anti-patterns
- Wiping a system before collecting evidence.
- Declaring done when symptoms stop rather than when access is removed.
- Indicators shared without context, confidence or expiry.

## Output expectation
A timeline, scope and impact statement, actions taken with reasons, evidence handling notes, residual risk and follow-up actions.
