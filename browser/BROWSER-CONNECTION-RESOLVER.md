# Browser Connection Resolver

Decision:
- `debug/performance/network` -> Chrome DevTools MCP
- `structured automation/cross-browser` -> Playwright MCP
- `existing SSO/2FA/tab` -> extension mode (sensitive)
- `already-running Chromium` -> CDP
- `remote browser service` -> WebSocket/remote endpoint
- `CI/untrusted task` -> isolated/headless sandbox

Never attach to a personal authenticated profile unless the task requires it and policy permits it.
