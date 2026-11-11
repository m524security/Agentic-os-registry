---
name: data-analysis-rigor
description: "Produce numbers that survive scrutiny: check grain and joins, reconcile totals, state definitions and uncertainty, and chart honestly."
---

# Data Analysis Rigor

## When to apply
Any analysis, metric, report or visualization that someone will use to decide something.

## How to apply
1. Write the question and the metric definition (numerator, denominator, population, period, exclusions) before querying.
2. Profile the data: grain, keys, duplicates, nulls, ranges, units and time zones. Fix or flag problems with documented rules and keep the raw copy.
3. Check every join for cardinality: row counts before and after must match expectations. Many wrong numbers are fan-out or dropped rows.
4. Reconcile totals to an independent source after each transformation step.
5. Report effect sizes with uncertainty (intervals, sample sizes), and avoid claiming a trend from a few points or a difference inside the noise.
6. Choose the chart for the comparison; start bars at zero, label units and avoid dual axes that manufacture correlation.
7. List assumptions, exclusions and what the data cannot answer.

## Anti-patterns
- Averaging averages or percentages of different bases.
- Dropping outliers without saying so.
- Comparing groups that differ in more than the factor of interest, then claiming cause.

## Output expectation
The answer, the definition behind it, the reconciliation that supports it, the uncertainty and the caveats.
