---
name: evidence-first-verification
description: "Every material claim of success must map to a test, a build artifact, a log, a measurement, or another independently inspectable source — never to the claim itself."
---

# Evidence-First Verification

Every material claim of success must map to a test, a build artifact, a log, a measurement, or another
independently inspectable source — never to the claim itself.

## When to apply
Before marking any task `completed`, and whenever reviewing or accepting another agent's output.

## How to apply
1. Name the exact evidence a claim rests on (test name, log line, artifact path, measured value).
2. If no evidence exists yet, the status is `partial` or `blocked`, not `completed`, regardless of
   confidence.
3. Re-run or re-inspect evidence rather than trusting a prior agent's summary of it.
4. Record assumptions and limitations explicitly alongside the evidence, per the manifest's
   `output_contract`.

## Anti-patterns
- "It should work" standing in for a test result.
- Citing evidence that does not actually test the claim being made (e.g. a build succeeding as proof a
  bug is fixed).

## Output expectation
A claim-to-evidence mapping a third party could check without re-doing the work.
