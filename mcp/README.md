# MCP Connection Plane

Supported connection patterns in this architecture:
- local STDIO
- Streamable HTTP / localhost HTTP
- browser CDP bridge
- browser WebSocket/Playwright endpoint
- browser-extension bridge
- containerized/sandboxed MCP
- remote managed MCP
- MCP gateway/proxy
- ephemeral per-task MCP sessions

Every server registration must declare provenance, transport, executable/URL, requested tools, filesystem scope, network scope, secret scope, data classification, auth method, timeout, health check, audit policy, and trust status.
