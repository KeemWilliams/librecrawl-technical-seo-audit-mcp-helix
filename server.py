#!/usr/bin/env python3
"""
LibreCrawl MCP Server
Wraps LibreCrawl REST API as Claude MCP tools for full-site SEO auditing.
Source: https://github.com/adityaarsharma/librecrawl-mcp
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("librecrawl-mcp")

BASE     = f"http://127.0.0.1:{os.getenv('LIBRECRAWL_PORT', '5080')}"
MCP_PORT = int(os.getenv('MCP_PORT', '5081'))
REPORTS_DIR = Path(os.getenv('REPORTS_DIR', Path.home() / 'librecrawl-reports'))

_client = None


# ── HTTP client ───────────────────────────────────────────────────────────────

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


# ── Report generator ──────────────────────────────────────────────────────────

def _build_report(pages: list, base_url: str, crawl_id: int) -> str:
    """Generate a structured Markdown SEO audit report from crawl export data."""

    domain = base_url.replace("https://", "").replace("http://", "").rstrip("/")
    now    = datetime.now().strftime("%Y-%m-%d %H:%M")
    total  = len(pages)

    # ── Categorise pages ──────────────────────────────────────────────────────
    status_buckets   = defaultdict(list)
    missing_title    = []
    missing_meta     = []
    missing_h1       = []
    long_title       = []
    short_title      = []
    long_meta        = []
    short_meta       = []
    thin_content     = []
    dup_titles       = defaultdict(list)
    dup_metas        = defaultdict(list)
    slow_pages       = []
    issues_by_page   = {}

    for p in pages:
        url    = p.get("url", "")
        status = p.get("status_code", 0)
        title  = (p.get("title") or "").strip()
        meta   = (p.get("meta_description") or "").strip()
        h1     = (p.get("h1") or "").strip()
        words  = p.get("word_count", 0) or 0
        rt     = p.get("response_time_ms", 0) or 0
        issues = p.get("issues_detected") or []

        status_buckets[str(status)[:1] + "xx"].append(url)

        if not title:             missing_title.append(url)
        if not meta:              missing_meta.append(url)
        if not h1:                missing_h1.append(url)
        if title and len(title) > 60:  long_title.append((url, title))
        if title and len(title) < 30:  short_title.append((url, title))
        if meta and len(meta) > 160:   long_meta.append((url, meta))
        if meta and 0 < len(meta) < 70: short_meta.append((url, meta))
        if 0 < words < 300:       thin_content.append((url, words))
        if rt > 3000:             slow_pages.append((url, rt))

        if title:  dup_titles[title].append(url)
        if meta:   dup_metas[meta].append(url)

        if issues:
            issues_by_page[url] = issues if isinstance(issues, list) else [issues]

    dup_titles = {t: urls for t, urls in dup_titles.items() if len(urls) > 1}
    dup_metas  = {m: urls for m, urls in dup_metas.items()  if len(urls) > 1}

    broken   = status_buckets.get("4xx", []) + status_buckets.get("5xx", [])
    redirect = status_buckets.get("3xx", [])
    ok       = status_buckets.get("2xx", [])

    total_issues = (len(missing_title) + len(missing_meta) + len(missing_h1) +
                    len(long_title) + len(short_title) + len(thin_content) +
                    len(dup_titles) + len(broken) + len(slow_pages))

    # ── Build Markdown ────────────────────────────────────────────────────────
    lines = []
    def h(level, text): lines.append(f"\n{'#' * level} {text}\n")
    def li(text):       lines.append(f"- {text}")
    def sep():          lines.append("\n---\n")

    # Header
    lines.append(f"# SEO Audit Report — {domain}")
    lines.append(f"**Generated:** {now}  |  **Crawl ID:** {crawl_id}  |  **Pages:** {total}\n")
    sep()

    # Summary scorecard
    h(2, "📊 Summary")
    lines.append(f"| Metric | Count | Status |")
    lines.append(f"|--------|-------|--------|")
    lines.append(f"| Pages crawled | {total} | |")
    lines.append(f"| 200 OK | {len(ok)} | {'✅' if len(ok) == total else '⚠️'} |")
    lines.append(f"| Broken (4xx/5xx) | {len(broken)} | {'✅' if not broken else '🔴'} |")
    lines.append(f"| Redirects (3xx) | {len(redirect)} | {'✅' if not redirect else '⚠️'} |")
    lines.append(f"| Missing title | {len(missing_title)} | {'✅' if not missing_title else '🔴'} |")
    lines.append(f"| Missing meta desc | {len(missing_meta)} | {'✅' if not missing_meta else '🔴'} |")
    lines.append(f"| Missing H1 | {len(missing_h1)} | {'✅' if not missing_h1 else '🔴'} |")
    lines.append(f"| Title too long (>60) | {len(long_title)} | {'✅' if not long_title else '⚠️'} |")
    lines.append(f"| Title too short (<30) | {len(short_title)} | {'✅' if not short_title else '⚠️'} |")
    lines.append(f"| Thin content (<300w) | {len(thin_content)} | {'✅' if not thin_content else '⚠️'} |")
    lines.append(f"| Duplicate titles | {len(dup_titles)} | {'✅' if not dup_titles else '🔴'} |")
    lines.append(f"| Slow pages (>3s) | {len(slow_pages)} | {'✅' if not slow_pages else '⚠️'} |")
    lines.append("")

    sep()

    # ── Critical Issues ───────────────────────────────────────────────────────
    h(2, "🔴 Critical — Fix First")

    # Broken links
    if broken:
        h(3, f"Broken Pages ({len(broken)})")
        lines.append("> **Fix:** 301 to the correct URL, or remove internal links pointing here.\n")
        lines.append("| URL | Status |")
        lines.append("|-----|--------|")
        for url in broken:
            s = next((p.get("status_code","?") for p in pages if p.get("url") == url), "?")
            lines.append(f"| `{url}` | {s} |")
        lines.append("")

    # Duplicate titles
    if dup_titles:
        h(3, f"Duplicate Titles ({len(dup_titles)} groups)")
        lines.append("> **Fix:** Give each page a unique title. Redirect duplicates if they're the same page.\n")
        for title, urls in list(dup_titles.items())[:10]:
            lines.append(f"**\"{title[:70]}\"**")
            for u in urls:
                li(f"`{u}`")
            lines.append("")

    # Missing titles
    if missing_title:
        h(3, f"Missing Title Tag ({len(missing_title)} pages)")
        lines.append("> **Fix:** Add a unique `<title>` tag (50–60 chars) to each page.\n")
        for url in missing_title[:20]:
            li(f"`{url}`")
        if len(missing_title) > 20:
            lines.append(f"… and {len(missing_title)-20} more")
        lines.append("")

    sep()

    # ── Warnings ──────────────────────────────────────────────────────────────
    h(2, "⚠️ Warnings — High Impact")

    # Missing meta descriptions
    if missing_meta:
        h(3, f"Missing Meta Description ({len(missing_meta)} pages)")
        lines.append("> **Fix:** Add a unique meta description (120–155 chars) to each page. Directly improves CTR.\n")
        for url in missing_meta[:30]:
            li(f"`{url}`")
        if len(missing_meta) > 30:
            lines.append(f"… and {len(missing_meta)-30} more")
        lines.append("")

    # Missing H1
    if missing_h1:
        h(3, f"Missing H1 ({len(missing_h1)} pages)")
        lines.append("> **Fix:** Add exactly one `<h1>` per page matching the primary keyword.\n")
        for url in missing_h1[:20]:
            li(f"`{url}`")
        if len(missing_h1) > 20:
            lines.append(f"… and {len(missing_h1)-20} more")
        lines.append("")

    # Long titles
    if long_title:
        h(3, f"Title Too Long — over 60 chars ({len(long_title)} pages)")
        lines.append("> **Fix:** Shorten to 50–60 chars. Google truncates anything longer.\n")
        lines.append("| URL | Title (truncated) | Length |")
        lines.append("|-----|-------------------|--------|")
        for url, title in long_title[:20]:
            lines.append(f"| `{url}` | {title[:60]}… | {len(title)} |")
        if len(long_title) > 20:
            lines.append(f"| … | {len(long_title)-20} more | |")
        lines.append("")

    # Short titles
    if short_title:
        h(3, f"Title Too Short — under 30 chars ({len(short_title)} pages)")
        lines.append("> **Fix:** Expand titles to 50–60 chars. Include target keyword.\n")
        lines.append("| URL | Title | Length |")
        lines.append("|-----|-------|--------|")
        for url, title in short_title[:15]:
            lines.append(f"| `{url}` | {title} | {len(title)} |")
        lines.append("")

    # Thin content
    if thin_content:
        h(3, f"Thin Content — under 300 words ({len(thin_content)} pages)")
        lines.append("> **Fix:** Expand with useful content, or add `noindex` if it's a utility page.\n")
        lines.append("| URL | Words |")
        lines.append("|-----|-------|")
        for url, words in sorted(thin_content, key=lambda x: x[1])[:20]:
            lines.append(f"| `{url}` | {words} |")
        lines.append("")

    # Slow pages
    if slow_pages:
        h(3, f"Slow Response Time — over 3s ({len(slow_pages)} pages)")
        lines.append("> **Fix:** Check server caching, image sizes, and plugin bloat. Target <1s TTFB.\n")
        lines.append("| URL | Response Time |")
        lines.append("|-----|--------------|")
        for url, rt in sorted(slow_pages, key=lambda x: -x[1])[:20]:
            lines.append(f"| `{url}` | {rt:,}ms |")
        lines.append("")

    sep()

    # ── Redirects ─────────────────────────────────────────────────────────────
    if redirect:
        h(2, f"↪️ Redirects ({len(redirect)} pages)")
        lines.append("> **Fix:** Update internal links to point to the final destination URL.\n")
        for url in redirect[:20]:
            li(f"`{url}`")
        if len(redirect) > 20:
            lines.append(f"… and {len(redirect)-20} more")
        lines.append("")
        sep()

    # ── All Pages ─────────────────────────────────────────────────────────────
    h(2, "📋 All Pages")
    lines.append("| Status | URL | Title | Words | Issues |")
    lines.append("|--------|-----|-------|-------|--------|")

    # Sort: broken first, then by depth
    sorted_pages = sorted(pages, key=lambda p: (
        0 if str(p.get("status_code","")).startswith("4") else
        1 if str(p.get("status_code","")).startswith("5") else
        2 if str(p.get("status_code","")).startswith("3") else 3,
        p.get("depth", 99)
    ))

    for p in sorted_pages[:300]:
        url    = p.get("url", "")
        status = p.get("status_code", "?")
        title  = (p.get("title") or "")[:50] or "—"
        words  = p.get("word_count", 0) or 0
        issue_list = p.get("issues_detected") or []
        issue_count = len(issue_list) if isinstance(issue_list, list) else (1 if issue_list else 0)
        status_icon = "🔴" if str(status).startswith(("4","5")) else "↪️" if str(status).startswith("3") else "✅"
        lines.append(f"| {status_icon} {status} | `{url}` | {title} | {words} | {issue_count} |")

    if len(pages) > 300:
        lines.append(f"| … | {len(pages)-300} more pages not shown | | | |")

    lines.append("")
    sep()

    # ── Fix Priority Checklist ────────────────────────────────────────────────
    h(2, "✅ Fix Priority Checklist")
    lines.append("Copy this into your task tracker:\n")

    priority = 1
    if broken:
        lines.append(f"- [ ] **P{priority}** Fix {len(broken)} broken pages (4xx/5xx)")
        priority += 1
    if dup_titles:
        lines.append(f"- [ ] **P{priority}** Resolve {len(dup_titles)} duplicate title groups")
        priority += 1
    if missing_title:
        lines.append(f"- [ ] **P{priority}** Add title tags to {len(missing_title)} pages")
        priority += 1
    if missing_meta:
        lines.append(f"- [ ] **P{priority}** Add meta descriptions to {len(missing_meta)} pages")
        priority += 1
    if missing_h1:
        lines.append(f"- [ ] **P{priority}** Add H1 to {len(missing_h1)} pages")
        priority += 1
    if long_title:
        lines.append(f"- [ ] **P{priority}** Shorten {len(long_title)} titles to ≤60 chars")
        priority += 1
    if short_title:
        lines.append(f"- [ ] **P{priority}** Expand {len(short_title)} short titles to 50–60 chars")
        priority += 1
    if thin_content:
        lines.append(f"- [ ] **P{priority}** Address {len(thin_content)} thin content pages")
        priority += 1
    if slow_pages:
        lines.append(f"- [ ] **P{priority}** Fix {len(slow_pages)} slow pages (>3s response time)")
        priority += 1
    if redirect:
        lines.append(f"- [ ] **P{priority}** Update internal links for {len(redirect)} redirects")
        priority += 1
    if dup_metas:
        lines.append(f"- [ ] **P{priority}** Fix {len(dup_metas)} duplicate meta descriptions")
        priority += 1

    lines.append("")
    lines.append(f"---\n*Generated by [librecrawl-mcp](https://github.com/adityaarsharma/librecrawl-mcp)*")

    return "\n".join(lines)


# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def librecrawl_audit(url: str, max_pages: int = 500) -> dict:
    """
    Full SEO audit in one call — crawls the site, waits for completion,
    exports results, and saves a Markdown report file.

    Use this for "audit X" requests. Returns the report file path + summary.
    For manual step-by-step control use librecrawl_start_crawl instead.

    Args:
        url: Full URL to crawl (e.g. https://example.com)
        max_pages: Max pages (default 500)
    """
    # Start
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

    if not result.get("success"):
        return {"success": False, "error": result.get("message", "Failed to start crawl")}

    # Poll until done (max 20 min)
    deadline = time.time() + 1200
    crawled  = 0
    while time.time() < deadline:
        time.sleep(8)
        d     = call("GET", "/api/crawl_status")
        stats = d.get("stats", {})
        crawled = stats.get("crawled", 0)
        if not d.get("is_running", True) and crawled > 0:
            break

    # Export
    if crawl_id is not None:
        call("POST", f"/api/crawls/{crawl_id}/load")

    r = get_client().post(f"{BASE}/api/export_data", json={
        "format": "json",
        "fields": ["url", "status_code", "title", "meta_description",
                   "h1", "word_count", "canonical_url", "depth",
                   "issues_detected", "response_time_ms"],
    }, timeout=120)
    r.raise_for_status()
    export = r.json()

    pages = export if isinstance(export, list) else export.get("urls", export.get("pages", []))

    if not pages:
        return {
            "success": False,
            "crawl_id": crawl_id,
            "crawled": crawled,
            "error": "Export returned no pages. Crawl may still be running — try librecrawl_generate_report(crawl_id) in 30s.",
        }

    # Generate and save MD report
    report_md  = _build_report(pages, url, crawl_id or 0)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    domain     = url.replace("https://", "").replace("http://", "").rstrip("/").split("/")[0]
    timestamp  = datetime.now().strftime("%Y%m%d-%H%M")
    report_path = REPORTS_DIR / f"{domain}-{timestamp}.md"
    report_path.write_text(report_md, encoding="utf-8")

    # Quick summary
    broken = sum(1 for p in pages if str(p.get("status_code","")).startswith(("4","5")))
    no_meta = sum(1 for p in pages if not (p.get("meta_description") or "").strip())
    no_h1   = sum(1 for p in pages if not (p.get("h1") or "").strip())

    return {
        "success": True,
        "crawl_id": crawl_id,
        "pages_crawled": len(pages),
        "report_file": str(report_path),
        "summary": {
            "broken_pages": broken,
            "missing_meta_description": no_meta,
            "missing_h1": no_h1,
        },
        "next": f"Open {report_path} to see the full report with fix checklist.",
    }


@mcp.tool()
def librecrawl_generate_report(crawl_id: int = None) -> dict:
    """
    Generate a Markdown SEO report from a completed crawl.
    Saves the report as a .md file and returns the path.

    Args:
        crawl_id: ID from librecrawl_start_crawl (optional — uses current crawl if omitted)
    """
    base_url = ""

    if crawl_id is not None:
        call("POST", f"/api/crawls/{crawl_id}/load")
        # Try to get base_url from status
        try:
            d = call("GET", "/api/crawl_status")
            base_url = d.get("stats", {}).get("baseUrl", "")
        except Exception:
            pass

    r = get_client().post(f"{BASE}/api/export_data", json={
        "format": "json",
        "fields": ["url", "status_code", "title", "meta_description",
                   "h1", "word_count", "canonical_url", "depth",
                   "issues_detected", "response_time_ms"],
    }, timeout=120)
    r.raise_for_status()
    export = r.json()

    pages = export if isinstance(export, list) else export.get("urls", export.get("pages", []))

    if not pages:
        return {"success": False, "error": "No pages found. Is the crawl complete?"}

    if not base_url and pages:
        from urllib.parse import urlparse
        parsed = urlparse(pages[0].get("url", ""))
        base_url = f"{parsed.scheme}://{parsed.netloc}"

    report_md  = _build_report(pages, base_url, crawl_id or 0)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    domain     = base_url.replace("https://","").replace("http://","").rstrip("/").split("/")[0]
    timestamp  = datetime.now().strftime("%Y%m%d-%H%M")
    report_path = REPORTS_DIR / f"{domain}-{timestamp}.md"
    report_path.write_text(report_md, encoding="utf-8")

    return {
        "success": True,
        "report_file": str(report_path),
        "pages": len(pages),
    }


@mcp.tool()
def librecrawl_start_crawl(url: str, max_pages: int = 500) -> dict:
    """
    Start a crawl manually. Returns crawl_id immediately — crawl runs async.
    Poll librecrawl_get_status() until done, then librecrawl_generate_report(crawl_id).

    Use librecrawl_audit() instead if you want a one-call full audit.

    Args:
        url: Full URL to crawl (e.g. https://example.com)
        max_pages: Max pages (default 500)
    """
    call("POST", "/api/save_settings", json={
        "enableJavaScript": False,
        "maxUrls": max_pages,
        "maxDepth": 5,
        "crawlDelay": 0.5,
        "followRedirects": True,
        "crawlExternalLinks": False,
    })
    result   = call("POST", "/api/start_crawl", json={"url": url})
    crawl_id = result.get("crawl_id")
    return {
        "success": result.get("success"),
        "crawl_id": crawl_id,
        "message": result.get("message"),
        "next": f"Poll librecrawl_get_status() until is_running=False, then librecrawl_generate_report({crawl_id})",
    }


@mcp.tool()
def librecrawl_get_status() -> dict:
    """
    Poll current crawl progress. Repeat until is_running=False.
    Returns: is_running, crawled, queued, issues, base_url
    """
    d     = call("GET", "/api/crawl_status")
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
    Export raw crawl JSON. For a formatted report use librecrawl_generate_report() instead.

    Args:
        crawl_id: ID from librecrawl_start_crawl (optional)
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
