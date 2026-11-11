# Browser Connection Plane

The Brain does not hard-code one browser. The Browser Connection Resolver selects an adapter based on:
1. Need existing login/session?
2. Need DevTools/network/performance inspection?
3. Need cross-browser compatibility?
4. Need isolation for untrusted content?
5. Need visible/headed interaction?
6. Need remote execution?
7. Data sensitivity and allowed hosts.

## Default preference
- Untrusted/general automation: isolated Playwright/Chrome.
- Cross-browser tests: Playwright MCP.
- Chrome debugging/performance: Chrome DevTools MCP.
- Existing authenticated session: extension/CDP only with explicit session-data permission.
- Remote browsers: authenticated endpoint only.

See `registry/browser-connections.json`.
