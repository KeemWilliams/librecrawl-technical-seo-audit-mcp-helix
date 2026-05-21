# LibreCrawl MCP

**Self-hosted SEO site crawler for Claude — 1-click install, 500+ pages, zero API cost.**

Wrap [LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) as a Claude MCP server. Give Claude the ability to crawl any website, detect SEO issues, and export structured audit data — all running on your own server with no rate limits or per-crawl fees.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Claude-MCP-orange)](https://modelcontextprotocol.io)
[![LibreCrawl](https://img.shields.io/badge/Powered%20by-LibreCrawl-green)](https://github.com/PhialsBasement/LibreCrawl)

---

## What it does

Claude gets 5 tools:

| Tool | What it does |
|------|-------------|
| `librecrawl_start_crawl` | Start a full-site crawl, returns `crawl_id` |
| `librecrawl_get_status` | Poll progress — crawled, queued, issues count |
| `librecrawl_export_results` | Export full audit JSON by `crawl_id` |
| `librecrawl_list_crawls` | List all past crawls |
| `librecrawl_stop_crawl` | Stop a running crawl |

**What Claude can audit:**
- Missing / duplicate title tags and meta descriptions
- Missing H1s, thin content pages
- Broken links (4xx/5xx)
- Canonical URL mismatches
- Page depth and crawlability
- Word count per page
- Site-wide SEO issues (1,600+ issue types)

---

## Install (1 command)

```bash
curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-mcp/main/install.sh | bash
```

**Requires:** Docker, Python 3.9+, Node.js (for PM2), Git

The installer:
1. Clones LibreCrawl and builds the Docker image (~5–8 min first run)
2. Applies the session persistence patch (fixes crawl results not saving to DB)
3. Installs the Python MCP server in an isolated venv
4. Registers both services with PM2 (`restart: always`)

### Custom install directory

```bash
INSTALL_DIR=/opt/librecrawl-mcp bash <(curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-mcp/main/install.sh)
```

### Custom ports

```bash
LIBRECRAWL_PORT=5080 MCP_PORT=5081 bash install.sh
```

---

## Add to Claude

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "librecrawl": {
      "type": "http",
      "url": "http://127.0.0.1:5081/mcp"
    }
  }
}
```

**Claude Code** (`settings.json`):

```json
{
  "mcpServers": {
    "librecrawl": {
      "type": "http",
      "url": "http://127.0.0.1:5081/mcp"
    }
  }
}
```

**Remote access** (via mcp-remote + Nginx):

```json
{
  "mcpServers": {
    "librecrawl": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://your-domain.com/librecrawl/mcp"]
    }
  }
}
```

---

## Remote deployment (VPS / Hetzner)

For a remote server, add an Nginx location block:

```nginx
location /librecrawl/ {
    proxy_pass          http://127.0.0.1:5081/;
    proxy_http_version  1.1;
    proxy_set_header    Host $host;
    proxy_read_timeout  600s;
    proxy_buffering     off;
    proxy_cache         off;
    chunked_transfer_encoding on;
}
```

Then point Claude at `https://your-domain.com/librecrawl/mcp`.

---

## Usage example

Once connected, just ask Claude:

> *"Crawl uichemy.com and give me a full SEO audit"*

Claude will:
1. Call `librecrawl_start_crawl("https://uichemy.com")`
2. Poll `librecrawl_get_status()` until complete
3. Call `librecrawl_export_results(crawl_id)` 
4. Analyze results and report issues

Example output from a real 500-page crawl:

```
500 pages crawled | 1,667 issues detected

Critical:
- 384 blog pages with titles >60 chars
- 30 template pages missing meta descriptions  
- 3 broken internal links (404)
- 2 URL pairs competing on same keyword (need 301s)
- 56 pages with >3s response time
```

---

## Architecture

```
Claude
  │  MCP (streamable-http)
  ▼
Python MCP server (port 5081)
  │  HTTP API
  ▼
LibreCrawl Flask app (port 5080, Docker)
  │  Headless crawl
  ▼
Target website
```

**Stack:**
- LibreCrawl — open-source Python SEO crawler with SQLite persistence
- FastMCP (Python SDK 1.x) — MCP server framework
- httpx — persistent session client (cookie jar across tool calls)
- PM2 — process manager (auto-restart, survives reboots)
- Docker — LibreCrawl isolation

---

## What the session patch fixes

LibreCrawl has a bug where `session_id` is read before `get_or_create_crawler()` creates it, so `crawl_id` is always `null` and crawl results never save to the database. The installer patches `main.py` automatically:

```python
# Before (broken): session_id is read before it's created
session_id = session.get('session_id')   # → always None
crawler = get_or_create_crawler()        # ← creates session_id here

# After (fixed): read AFTER creation
crawler = get_or_create_crawler()        # creates session_id
session_id = session.get('session_id')  # → correct value, DB persistence works
```

---

## Manage services

```bash
# Check status
pm2 status librecrawl-mcp
docker ps | grep librecrawl

# View logs
pm2 logs librecrawl-mcp
docker logs librecrawl --tail 50

# Restart
pm2 restart librecrawl-mcp
docker restart librecrawl

# Stop everything
pm2 stop librecrawl-mcp
docker stop librecrawl
```

---

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `INSTALL_DIR` | `~/librecrawl-mcp` | Where to install |
| `LIBRECRAWL_PORT` | `5080` | LibreCrawl internal port |
| `MCP_PORT` | `5081` | MCP server port |

---

## Related

- [LibreCrawl](https://github.com/PhialsBasement/LibreCrawl) — the crawler this wraps
- [youtube-channel-mcp](https://github.com/adityaarsharma/youtube-channel-mcp) — YouTube analytics MCP server
- [Model Context Protocol](https://modelcontextprotocol.io) — MCP spec

---

## License

MIT — use freely, attribution appreciated.

Built by [Aditya Sharma](https://adityaarsharma.com)
