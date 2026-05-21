#!/usr/bin/env python3
"""
LibreCrawl MCP Server
Wraps LibreCrawl REST API as Claude MCP tools for full-site SEO auditing.
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
