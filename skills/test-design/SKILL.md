---
name: test-design
description: "Design tests that fail when the behavior is wrong: behavior first, boundaries, determinism, and a check that each test can actually fail."
---

# Test Design

## When to apply
Writing or reviewing unit, integration or end-to-end tests, or deciding what to test for a change.

## How to apply
1. List the behaviors and the contract: inputs, outputs, side effects, errors. Test those, not private structure.
2. Cover the happy path, then boundaries (empty, one, many, maximum, negative, duplicate, malformed, concurrent) and each documented error.
3. Keep tests independent, deterministic and fast: control time, randomness, network and ordering; use real collaborators at integration boundaries and fakes only where the real thing is slow or unsafe.
4. Name each test after the behavior and make the failure message tell the reader what broke.
5. Prove the test can fail: break the code (or run mutation checks) and confirm the test goes red. A test that never fails protects nothing.
6. Keep a small number of end-to-end tests for critical journeys and push detail down to faster levels.
7. Fix flaky tests at the cause (shared state, timing, order); never retry them into green.

## Anti-patterns
- Asserting on implementation details so refactors break tests.
- Tests that mirror the code under test line by line.
- Coverage numbers treated as quality.

## Output expectation
A test set mapped to behaviors and boundaries, each shown to fail on a seeded defect, with the commands to run it.
