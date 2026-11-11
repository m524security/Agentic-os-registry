---
name: secure-code-review
description: "Review code for security defects by tracing untrusted input to sensitive sinks and checking authorization, secrets, cryptography and error handling on every path."
---

# Secure Code Review

## When to apply
Reviewing a change or a codebase area that parses input, authenticates, authorizes, stores secrets, calls other systems or runs commands.

## How to apply
1. Find the entry points (requests, files, messages, environment, database content) and the sensitive sinks (queries, commands, file paths, templates, deserializers, redirects, outbound requests).
2. Trace each source to each sink and check for validation by allow-list, correct escaping for the sink's context, and parameterization. Filtering on the way in rarely substitutes for encoding on the way out.
3. Check authorization at the object and function level on every route, not only authentication; look for direct object references and missing ownership checks.
4. Check secrets (in code, logs, errors, URLs), cryptography (standard libraries, modes, randomness, key handling) and session handling.
5. Check failure behavior: errors that leak internals, fail-open defaults, races between check and use.
6. Confirm each suspected issue with the minimal reasoning or test that shows it is reachable. Drop what is not.
7. Report file and line, the path from input to sink, the impact, the smallest root-cause fix and the regression test.

## Anti-patterns
- Pattern-matching on function names without following the data.
- Treating framework use as proof of safety.
- Reporting every scanner hit, or a fix that blocks one payload but not the flaw.

## Output expectation
Confirmed findings with location, data path, impact, fix and test; a short list of areas not reviewed.
