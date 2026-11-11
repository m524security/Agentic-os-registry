---
name: small-model-operation
description: "Get dependable work from small or local models: short prompts, one decision per call, strict JSON, host-side retrieval, and fail-closed verification."
---

# Small Model Operation

## When to apply
The configured model is small (roughly 1-14 billion parameters), runs locally, has a short context window, or has shown malformed or invented output.

## How to apply
1. Keep the prompt short: role, mission, method, completion gate, and at most two or three skills. Drop everything else.
2. Ask for one decision or one deliverable per call. Split multi-step goals into 1-4 ordered tasks.
3. Demand one JSON object in a shown shape. Accept sloppy JSON (trailing commas, quotes) by repairing it, but never accept prose as a completed result.
4. Do not rely on native tool calling. Run search, fetch and crawl on the host and pass the retrieved text in as untrusted data.
5. Bound everything: reply tokens, context size, retrieved characters per page, number of pages, wall-clock time.
6. Retry an unparseable reply once with a shorter instruction; after that keep the raw text as a partial result with no evidence.
7. Verify by evidence the host can check (a test run, a file, a quoted source). A weak model's own "looks fine" is not verification; an unclear verdict means fail.
8. Use a larger model for planning and judgment when one is available; use the small model for narrow, checkable steps.

## Anti-patterns
- Sending the full agent prompt and every skill to a model with a 4k context.
- Trusting a status of completed that carries no evidence.
- Asking a small model to choose among hundreds of agents; shortlist first.

## Output expectation
Narrow tasks that finish with checkable evidence, or an honest partial/blocked result naming what a larger model or the host must supply.
