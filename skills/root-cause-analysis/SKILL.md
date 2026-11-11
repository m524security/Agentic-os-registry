---
name: root-cause-analysis
description: "Find the cause of a failure, not its symptom: reproduce, build the timeline, test one hypothesis at a time, fix the cause and prove it with a regression check."
---

# Root Cause Analysis

## When to apply
A defect, outage, flaky test, wrong result or recurring failure whose cause is not yet known.

## How to apply
1. Define the failure precisely: expected versus observed, where, since when, how often, and for whom.
2. Reproduce it, then shrink the reproduction until removing anything makes it vanish.
3. Build the timeline of changes (code, config, data, load, dependencies, environment) around the first occurrence. The cause is usually the earliest change that, reverted, removes the failure.
4. List hypotheses, rank by likelihood and cost to test, and test one at a time with a prediction that can fail. Change one variable per experiment.
5. Distinguish cause (reverting it removes the failure), contributing factor (makes it likelier) and trigger (the event that exposed it).
6. Fix the cause, not the symptom, then add the check that would have caught it.
7. Verify on the original reproduction and on neighbors, and record the cause in one sentence.

## Anti-patterns
- Fixing where the symptom appears.
- Several changes at once, so nothing is learned.
- Declaring "five whys" complete at a person or a process word instead of a mechanism.
- Closing on a fix that cannot be shown to remove the original failure.

## Output expectation
The cause stated as a mechanism, the evidence tying it to the failure, the fix, the regression check, and any contributing factors left open.
