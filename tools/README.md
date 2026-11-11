# Host tools

`webtools.py` gives any model (cloud or local) web access through the host: `fetch(url)`, `search(query)` (needs `SEARCH_URL`
pointing at a SearXNG-style JSON endpoint), and `crawl(seed, max_pages, max_depth)` (robots rules, visited set, delays, hard limits).
`examples/llm_adapter.py` calls these when a task's `required_capabilities` include `web_fetch`, `web_search` or `crawl_runtime`
and injects the result as untrusted retrieved context. Private and loopback addresses are refused unless `WEB_ALLOW_PRIVATE=1`.
Browser automation is not provided here; it needs a host with a browser tool (see the top-level README).
