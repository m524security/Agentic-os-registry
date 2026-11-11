# Browser/MCP Security Policy
- Treat browser-control MCP as privileged: it may see page content, cookies, forms, console/network data, and authenticated sessions.
- Prefer isolated profiles for untrusted pages.
- Existing-profile/extension/CDP access requires explicit need and tighter permission scope.
- Never expose unauthenticated CDP or MCP endpoints publicly.
- Remote MCP/browser endpoints require authenticated encrypted transport.
- Community MCP servers are sandboxed and audited before trust promotion.
- Apply host allowlists and deny local/private-network access unless required.
- Separate read/inspect permissions from write/click/form-submit/download/upload permissions.
- Log consequential browser actions and tool calls.
