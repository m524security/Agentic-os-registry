---
name: continuous-learning-pattern
description: "Turn a repeated observation into a confidence-weighted candidate skill, and promote it to a reusable skill only after it is evaluated, not on first occurrence."
---

# Continuous Learning Pattern

Turn a repeated observation into a confidence-weighted candidate skill, and promote it to a reusable
skill only after it is evaluated, not on first occurrence.

## When to apply
When the same workaround, fix, or judgment call recurs across tasks or sessions and looks like it would
generalize.

## How to apply
1. Observation: log the specific situation and what worked, with enough detail to reproduce it.
2. Repetition: do not promote from a single instance; require the pattern to recur across distinct tasks.
3. Confidence weighting: track how often the candidate pattern held versus failed before trusting it.
4. Evaluation: test the candidate explicitly (a held-out case, a dry run) before it becomes a skill.
5. Promotion: only an evaluated, passing candidate becomes a cross-session skill; everything else stays a
   logged candidate.

## Anti-patterns
- Promoting a one-off fix to a general rule after a single success.
- Treating a failed candidate as a tried-and-rejected idea instead of recording the failure for next time.

## Output expectation
A dated, evidenced skill candidate with its pass/fail history attached, not an unverified claim.
