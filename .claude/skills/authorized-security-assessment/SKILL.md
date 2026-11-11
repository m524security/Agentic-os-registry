---
name: authorized-security-assessment
description: "Run security assessment inside written authorization: confirm scope and rules first, use non-destructive validation, and report only validated findings."
---

# Authorized Security Assessment

## When to apply
Any reconnaissance, scanning, testing or exploitation-adjacent activity, including labs and exercises.

## How to apply
1. Obtain or confirm the authorization: owner, assets in scope, techniques allowed, time window, contacts and stop conditions. No authorization, no activity.
2. Turn the scope into an allow list and check every action against it. When a finding points outside scope, record it and stop; do not follow it.
3. Prefer passive and public sources, then the lowest-impact active checks, rate-limited and logged.
4. Validate each candidate with the least intrusive proof; never damage data or availability, and never exfiltrate real data to prove a point.
5. Handle discovered secrets and personal data minimally: mask in reports, do not use, and notify the owner promptly for critical exposure.
6. Report each finding with asset, evidence, impact, likelihood, confidence and a fix with a verification step; separate confirmed, probable and theoretical.
7. State what was not tested and why.

## Anti-patterns
- Treating a vague request as permission.
- Scanner output reported as findings.
- Proof of concept that exceeds what is needed to show the issue.

## Output expectation
A scope statement, the actions performed against it, validated findings with fixes, and an explicit list of limits and exclusions.
