#!/usr/bin/env bash
# =============================================================================
# LibreCrawl MCP — 1-click installer
# Self-hosted SEO crawler exposed as a Claude MCP server
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-mcp/main/install.sh | bash
#
# Or with a custom install dir:
#   INSTALL_DIR=/opt/librecrawl-mcp bash install.sh
#
# What this installs:
#   1. LibreCrawl (Docker container) — SEO crawler on port 5080
#   2. LibreCrawl MCP server (Python + PM2) — MCP endpoint on port 5081
#   3. Applies session persistence bugfix to LibreCrawl
#   4. (Optional) Nginx reverse proxy config
# =============================================================================

set -euo pipefail

# ── Config ───────────────────────────────────────────────────────────────────
LIBRECRAWL_PORT="${LIBRECRAWL_PORT:-5080}"
MCP_PORT="${MCP_PORT:-5081}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/librecrawl-mcp}"
PM2_NAME="librecrawl-mcp"
MCP_USERNAME="${MCP_USERNAME:-mcp-user}"

# ── Colors ───────────────────────────────────────────────────────────────────
if [[ -t 1 ]]; then
  GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
  BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BLUE=''; BOLD=''; NC=''
fi

log()  { echo -e "${GREEN}✓${NC} $*"; }
info() { echo -e "${BLUE}→${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "${RED}✗ ERROR:${NC} $*" >&2; exit 1; }
hr()   { echo -e "${BLUE}$(printf '─%.0s' {1..60})${NC}"; }

hr
echo -e "${BOLD}LibreCrawl MCP — Installer${NC}"
echo -e "  Install dir : ${INSTALL_DIR}"
echo -e "  LibreCrawl  : http://127.0.0.1:${LIBRECRAWL_PORT}"
echo -e "  MCP server  : http://127.0.0.1:${MCP_PORT}/mcp"
hr

# ── Step 0: Check dependencies ───────────────────────────────────────────────
info "Checking dependencies..."

command -v docker &>/dev/null   || err "Docker not found. Install: https://docs.docker.com/get-docker/"
command -v python3 &>/dev/null  || err "Python 3.9+ not found. Install: sudo apt install python3 python3-venv"
command -v git &>/dev/null      || err "Git not found. Install: sudo apt install git"

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info.minor)')
[[ "$PYTHON_VERSION" -ge 9 ]] || err "Python 3.9+ required (found 3.${PYTHON_VERSION})"

# Check docker compose (v2 plugin or standalone)
if docker compose version &>/dev/null 2>&1; then
  DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
  DOCKER_COMPOSE="docker-compose"
else
  err "Docker Compose not found. Install: https://docs.docker.com/compose/install/"
fi

# PM2 — install if missing
if ! command -v pm2 &>/dev/null; then
  warn "PM2 not found. Attempting install via npm..."
  command -v npm &>/dev/null || err "npm not found. Install Node.js: https://nodejs.org"
  npm install -g pm2 --quiet || err "PM2 install failed. Try: sudo npm install -g pm2"
fi

log "All dependencies satisfied"

# ── Step 1: Clone LibreCrawl ─────────────────────────────────────────────────
hr
info "Step 1/5 — Setting up LibreCrawl..."

mkdir -p "${INSTALL_DIR}"
LIBRECRAWL_DIR="${INSTALL_DIR}/librecrawl"

if [[ -d "${LIBRECRAWL_DIR}/.git" ]]; then
  info "LibreCrawl repo exists — pulling latest..."
  git -C "${LIBRECRAWL_DIR}" pull origin main --quiet
else
  info "Cloning LibreCrawl (github.com/PhialsBasement/LibreCrawl)..."
  git clone --quiet https://github.com/PhialsBasement/LibreCrawl.git "${LIBRECRAWL_DIR}"
fi

# ── Step 2: Apply session persistence patch ──────────────────────────────────
info "Step 2/5 — Applying session persistence patch..."

MAIN_PY="${LIBRECRAWL_DIR}/main.py"

# Patch: move session_id read to AFTER get_or_create_crawler() which creates it.
# Without this patch, crawl_id is always null and results are never saved to DB.
python3 - << 'PATCHEOF'
import sys

path = sys.argv[1]
content = open(path).read()

old = """    user_id = session.get('user_id')
    session_id = session.get('session_id')
    tier = session.get('tier', 'guest')"""

new = """    user_id = session.get('user_id')
    tier = session.get('tier', 'guest')"""

old2 = """    # Get or create crawler for this session
    crawler = get_or_create_crawler()"""

new2 = """    # Get or create crawler for this session (also initialises session_id)
    crawler = get_or_create_crawler()
    session_id = session.get('session_id')  # Must read AFTER get_or_create_crawler sets it"""

if old not in content:
    print("Patch 1 already applied or not needed — skipping")
else:
    content = content.replace(old, new, 1)
    content = content.replace(old2, new2, 1)
    open(path, 'w').write(content)
    print("Session persistence patch applied")
PATCHEOF "${MAIN_PY}"

# ── Step 3: Write Docker config + start LibreCrawl ───────────────────────────
info "Step 3/5 — Building and starting LibreCrawl Docker container..."
info "  (First build takes 5–8 min — Playwright + Chromium install)"

cat > "${LIBRECRAWL_DIR}/.env" << ENVEOF
HOST_BINDING=0.0.0.0
LOCAL_MODE=true
REGISTRATION_DISABLED=true
DEMO_MODE=false
DANGEROUSLY_SKIP_AUTH=true
ENVEOF

cat > "${LIBRECRAWL_DIR}/docker-compose.override.yml" << OVERRIDEEOF
services:
  librecrawl:
    ports:
      - "127.0.0.1:${LIBRECRAWL_PORT}:5000"
    restart: always
    shm_size: '2gb'
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 90s
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
    environment:
      - FLASK_APP=main.py
      - PYTHONUNBUFFERED=1
      - LOCAL_MODE=true
      - REGISTRATION_DISABLED=true
      - DEMO_MODE=false
      - DANGEROUSLY_SKIP_AUTH=true
OVERRIDEEOF

cd "${LIBRECRAWL_DIR}"
$DOCKER_COMPOSE build --quiet
$DOCKER_COMPOSE up -d
log "LibreCrawl container started on port ${LIBRECRAWL_PORT}"

# Wait for healthcheck
info "Waiting for LibreCrawl to be healthy (up to 90s)..."
for i in $(seq 1 18); do
  sleep 5
  STATUS=$(docker inspect --format='{{.State.Health.Status}}' librecrawl 2>/dev/null || echo "starting")
  if [[ "$STATUS" == "healthy" ]]; then
    log "LibreCrawl is healthy"
    break
  fi
  [[ $i -eq 18 ]] && warn "Health check timed out — container may still be starting"
done

# ── Step 4: MCP server ───────────────────────────────────────────────────────
info "Step 4/5 — Installing LibreCrawl MCP server..."

MCP_DIR="${INSTALL_DIR}/mcp-server"
mkdir -p "${MCP_DIR}"

# Write server.py
cat > "${MCP_DIR}/server.py" << 'PYEOF'
#!/usr/bin/env python3
"""
LibreCrawl MCP Server
Wraps LibreCrawl REST API as Claude MCP tools.
Source: https://github.com/adityaarsharma/librecrawl-mcp
"""

import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("librecrawl-mcp")

BASE = f"http://127.0.0.1:{os.getenv('LIBRECRAWL_PORT', '5080')}"
MCP_PORT = int(os.getenv('MCP_PORT', '5081'))
_client = None


def get_client():
    """Return authenticated httpx.Client. Re-auths automatically on 401."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.Client(timeout=30, follow_redirects=True)
        _client.post(f"{BASE}/api/login", json={"username": "mcp-user"}).raise_for_status()
    return _client


def call(method, path, **kwargs):
    global _client
    r = get_client().request(method, f"{BASE}{path}", **kwargs)
    if r.status_code == 401:
        _client = None
        r = get_client().request(method, f"{BASE}{path}", **kwargs)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def librecrawl_start_crawl(url: str, max_pages: int = 500) -> dict:
    """
    Start a full-site SEO crawl. Returns crawl_id — pass it to export when done.
    Crawl runs async. Poll librecrawl_get_status() until is_running=False,
    then call librecrawl_export_results(crawl_id).

    Args:
        url: Full URL to crawl (e.g. https://example.com)
        max_pages: Max pages to crawl (default 500)
    """
    call("POST", "/api/save_settings", json={
        "enableJavaScript": False,
        "maxUrls": max_pages,
        "maxDepth": 5,
        "crawlDelay": 0.5,
        "followRedirects": True,
        "crawlExternalLinks": False,
    })
    result = call("POST", "/api/start_crawl", json={"url": url})
    crawl_id = result.get("crawl_id")
    return {
        "success": result.get("success"),
        "crawl_id": crawl_id,
        "message": result.get("message"),
        "next": f"Poll librecrawl_get_status() until done, then librecrawl_export_results({crawl_id})",
    }


@mcp.tool()
def librecrawl_get_status() -> dict:
    """
    Poll current crawl progress. Repeat until is_running=False.
    Returns: is_running, crawled, queued, issues, base_url
    """
    d = call("GET", "/api/crawl_status")
    stats = d.get("stats", {})
    return {
        "is_running": d.get("is_running", False),
        "crawled":    stats.get("crawled", 0),
        "queued":     stats.get("queued", 0),
        "issues":     stats.get("issues", 0),
        "base_url":   stats.get("baseUrl", ""),
    }


@mcp.tool()
def librecrawl_export_results(crawl_id: int = None) -> dict:
    """
    Export crawl results as structured JSON.
    Pass crawl_id from librecrawl_start_crawl to retrieve a specific saved crawl.
    Call only after librecrawl_get_status() returns is_running=False.

    Args:
        crawl_id: ID returned by librecrawl_start_crawl (optional)
    """
    if crawl_id is not None:
        call("POST", f"/api/crawls/{crawl_id}/load")

    r = get_client().post(f"{BASE}/api/export_data", json={
        "format": "json",
        "fields": ["url", "status_code", "title", "meta_description",
                   "h1", "word_count", "canonical_url", "depth", "issues_detected"],
    }, timeout=120)
    r.raise_for_status()
    return r.json()


@mcp.tool()
def librecrawl_list_crawls() -> dict:
    """List all saved crawls with URL, crawl_id, and timestamp."""
    return call("GET", "/api/crawls/list")


@mcp.tool()
def librecrawl_stop_crawl() -> dict:
    """Stop the currently running crawl."""
    return call("POST", "/api/stop_crawl")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.streamable_http_app(), host="127.0.0.1", port=MCP_PORT, log_level="info")
PYEOF

# Create venv and install deps
info "Creating Python venv and installing dependencies..."
python3 -m venv "${MCP_DIR}/venv"
"${MCP_DIR}/venv/bin/pip" install --quiet --upgrade pip
"${MCP_DIR}/venv/bin/pip" install --quiet "mcp>=1.0.0" httpx uvicorn

log "Python dependencies installed"

# ── Step 5: Register with PM2 ────────────────────────────────────────────────
info "Step 5/5 — Registering with PM2..."

pm2 stop "${PM2_NAME}"   2>/dev/null || true
pm2 delete "${PM2_NAME}" 2>/dev/null || true

LIBRECRAWL_PORT="${LIBRECRAWL_PORT}" MCP_PORT="${MCP_PORT}" \
pm2 start "${MCP_DIR}/server.py" \
  --name "${PM2_NAME}" \
  --interpreter "${MCP_DIR}/venv/bin/python3" \
  --restart-delay 3000 \
  --max-restarts 10 \
  --env LIBRECRAWL_PORT="${LIBRECRAWL_PORT}" \
  --env MCP_PORT="${MCP_PORT}"

pm2 save
log "PM2 process registered and saved (survives reboots)"

# ── Nginx config hint ─────────────────────────────────────────────────────────
hr
echo ""
echo -e "${BOLD}Optional: Nginx reverse proxy${NC}"
echo "Add this location block to expose MCP over HTTPS:"
echo ""
cat << NGINX
location /librecrawl/ {
    proxy_pass          http://127.0.0.1:${MCP_PORT}/;
    proxy_http_version  1.1;
    proxy_set_header    Host \$host;
    proxy_read_timeout  600s;
    proxy_buffering     off;
    proxy_cache         off;
    chunked_transfer_encoding on;
}
NGINX

# ── Claude config ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Add to Claude claude_desktop_config.json or settings.json:${NC}"
echo ""
cat << JSON
{
  "mcpServers": {
    "librecrawl": {
      "type": "http",
      "url": "http://127.0.0.1:${MCP_PORT}/mcp"
    }
  }
}
JSON
echo ""
echo -e "Or via mcp-remote for remote access:"
echo '  "url": "https://your-domain.com/librecrawl/mcp"'

# ── Done ──────────────────────────────────────────────────────────────────────
hr
echo ""
echo -e "${BOLD}${GREEN}Install complete!${NC}"
echo ""
echo -e "  LibreCrawl UI : http://127.0.0.1:${LIBRECRAWL_PORT}"
echo -e "  MCP endpoint  : http://127.0.0.1:${MCP_PORT}/mcp"
echo ""
echo -e "  ${BOLD}5 tools available:${NC}"
echo -e "    librecrawl_start_crawl    — start a site crawl"
echo -e "    librecrawl_get_status     — poll progress"
echo -e "    librecrawl_export_results — get full results"
echo -e "    librecrawl_list_crawls    — list saved crawls"
echo -e "    librecrawl_stop_crawl     — stop current crawl"
echo ""
echo -e "  ${BOLD}Test it:${NC}"
echo -e "  pm2 status ${PM2_NAME}"
echo -e "  docker ps | grep librecrawl"
echo ""
