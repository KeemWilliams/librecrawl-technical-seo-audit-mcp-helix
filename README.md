<div align="center">

# 🕷️ librecrawl-mcp

### **The free, self-hosted Screaming Frog for AI agents.**

Run a full technical SEO audit on any website — **straight from Claude, Cursor, Codex, or any MCP client**. Unlimited pages. 50+ checks. PDF + CSVs ready to hand a client. MIT-licensed.

**Stop paying $999/mo for Ahrefs Site Audit. Stop paying £199/yr for Screaming Frog. Run it from your AI assistant. Free forever.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-orange?style=for-the-badge&logo=anthropic)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Latest Release](https://img.shields.io/github/v/release/adityaarsharma/librecrawl-mcp?style=for-the-badge&color=brightgreen)](https://github.com/adityaarsharma/librecrawl-mcp/releases)
[![GitHub stars](https://img.shields.io/github/stars/adityaarsharma/librecrawl-mcp?style=for-the-badge&color=yellow)](https://github.com/adityaarsharma/librecrawl-mcp/stargazers)

[![Works With](https://img.shields.io/badge/Claude%20Code-supported-D97757?style=flat-square)](https://docs.anthropic.com/claude-code)
[![Works With](https://img.shields.io/badge/Claude%20Desktop-supported-D97757?style=flat-square)](https://claude.ai/download)
[![Works With](https://img.shields.io/badge/Cursor-supported-000000?style=flat-square)](https://cursor.com)
[![Works With](https://img.shields.io/badge/OpenAI%20Codex-supported-10A37F?style=flat-square)](https://github.com/openai/codex)
[![Works With](https://img.shields.io/badge/Windsurf-supported-00C2A8?style=flat-square)](https://codeium.com/windsurf)
[![Works With](https://img.shields.io/badge/Continue.dev-supported-7C3AED?style=flat-square)](https://continue.dev)

**[⚡ Install in 60s](#-install-in-60-seconds) · [💰 What you save](#-what-this-saves-you) · [🆚 vs Screaming Frog & Ahrefs](#-vs-the-paid-tools) · [🚀 50+ checks](#-50-checks-every-audit) · [📖 Quick start](#-your-first-audit)**

</div>

---

## 💰 What this saves you

| If you currently pay... | Per year | librecrawl-mcp |
|---|---:|---|
| Screaming Frog SEO Spider | £199 | **£0** |
| Sitebulb Standard | £420 | **£0** |
| Sitebulb Pro | £1,680 | **£0** |
| Ahrefs Site Audit (Lite) | $1,188 | **£0** |
| Ahrefs Site Audit (Advanced) | $5,388 | **£0** |
| Ahrefs Site Audit (Enterprise) | $11,988 | **£0** |
| Semrush Site Audit (Guru) | $2,998 | **£0** |

> Self-hosted. No seat licenses. No URL caps. No "upgrade to crawl more". Drop it on a $5 VPS and crawl 10 client sites at 10,000 pages each — the price stays £0.

---

## 🪄 The whole pitch in 4 lines

```
You:   Audit https://acme.com — full site, no caps, give me the zip
Agent: → librecrawl_start_chunked_audit · polls until done · saves zip locally
You:   Show me broken pages + broken external links + hreflang errors
Agent: → reads CSVs, prints filtered tables. Server already forgot the audit.
```

That's the product. **Your AI agent runs Screaming Frog for you.** You get a PDF + 7 CSVs covering 50+ technical SEO checks, ready to hand a client. The server wipes everything the moment you download.

---

## 🔥 Why this beats paid SEO crawlers

### ⚡ It runs **inside your AI assistant**

No GUI app to babysit, no SaaS dashboard to log into, no CSV exports to upload to ChatGPT. Your agent calls 37 MCP tools, drives the audit, parses the CSVs, and gives you answers in chat. **Screaming Frog can't do this. Sitebulb can't do this. Ahrefs can't do this.**

### 🚀 Chunked-progressive crawler that **never times out**

Every other SEO MCP server (SiteAudit MCP, AgentAEO, SE Ranking MCP) runs synchronously and disconnects on sites over a few hundred pages. librecrawl-mcp runs the crawl in a **background worker thread**, persists progress to SQLite WAL, and returns a `session_id` in **under 2 seconds**. Your agent polls a tiny status tool until done. **10,000-page enterprise sites work the same as 50-page blogs.** Survives PM2 / MCP-client restarts mid-crawl.

### 🛡️ Catches WAF challenges other crawlers **silently misreport**

Cloudflare, Akamai, DataDome, Imperva, PerimeterX challenge pages are served as `200 OK` but contain a JavaScript challenge instead of your actual content. **Every other open-source crawler reports these as "page OK, all good".** We fingerprint the challenge in the response body and flag `bot_block_challenge_detected`. You see what's actually broken.

### 🤖 An **AIMD controller** tunes crawl delay live

Additive-Increase / Multiplicative-Decrease — same algorithm TCP congestion control uses. Error rate > 10% → halve chunk size, double delay. p95 latency > 1.5× target → 1.5× delay. Clean signals → additive decrease. **Polite by construction. No rate-limit blow-ups. No manual tuning.** Respects `robots.txt` `Crawl-Delay` floor.

### 🧹 **Ephemeral by design** — the agency-safe default

Once you download the zip, the server deletes the session row, every artifact file on disk, AND the upstream LibreCrawl crawl record. **Per-audit server footprint after cleanup: 0 bytes, 0 rows.** Auditing 50 client sites? Zero data persists where another operator could see it. This is what agencies have been begging for.

### 📄 Branded **PDF reports** ready to hand a client

WeasyPrint, A4, page numbers, footer on every page. Open in any PDF viewer. No "powered by SaaS" watermark. Hand it to a client as your work.

---

## 🆚 vs the paid tools

| | Screaming Frog Free | Screaming Frog Paid | Sitebulb | Ahrefs Site Audit | **librecrawl-mcp** |
|---|:---:|:---:|:---:|:---:|:---:|
| **Pages** | 500 cap | Unlimited | Unlimited | 50K (Ahrefs sub) | **♾️ Unlimited** |
| **Price/yr** | £0 | £199 | £420 – £1,680 | $1,188 – $11,988 | **🆓 £0 (MIT)** |
| **Runs inside your AI assistant** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Chunked / background crawl (no timeout)** | ❌ | ❌ | ❌ | Cloud only | ✅ |
| **Auto-adaptive crawl delay (AIMD)** | ❌ | ❌ | Manual | Hidden | ✅ |
| **WAF / bot-block detection on 200-OK pages** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Sitemap-orphan fill (URLs not internally linked)** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Ephemeral by default (zero server footprint)** | N/A | N/A | N/A | N/A | ✅ |
| Broken links (4xx/5xx/timeout/DNS/SSL) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Redirect chains with destination | ✅ | ✅ | ✅ | ✅ | ✅ |
| Title / meta / H1 + duplicates | ✅ | ✅ | ✅ | ✅ | ✅ |
| Canonical full audit | ✅ | ✅ | ✅ | ✅ | ✅ |
| Hreflang full (incl. return-tag graph) | Partial | ✅ | ✅ | Partial | ✅ |
| Sitemap full cross-checks | Partial | ✅ | ✅ | Partial | ✅ |
| Schema.org validation (16 types + Rich Results) | Partial | ✅ | ✅ | Partial | ✅ |
| Soft-404 fingerprinting | ❌ | ✅ | ✅ | ✅ | ✅ |
| Mixed content (HTTPS → HTTP) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Security headers pack | Partial | ✅ | ✅ | Partial | ✅ |
| Image performance + CLS | Partial | ✅ | ✅ | ✅ | ✅ |
| Content quality (Flesch · AI-tells · boilerplate) | ❌ | ❌ | Partial | ❌ | ✅ |
| Crawl-budget traps (calendar · session-id · facets) | Manual | ✅ | ✅ | ✅ | ✅ |
| Branded PDF report | ❌ | ❌ | ✅ | ❌ | ✅ |
| GSC clicks/impressions merge | Paid add-on | Paid add-on | Paid add-on | Native | ✅ |

> **Everything you actually use in Screaming Frog and Sitebulb is here. Free. Driven by your AI agent.**

---

## ⚡ Install in 60 seconds

```bash
curl -fsSL https://raw.githubusercontent.com/adityaarsharma/librecrawl-mcp/main/install.sh | bash
```

The installer asks 3 questions (target client, optional Google PageSpeed API key, optional GSC integration) and produces a ready-to-use MCP entry in your Claude / Cursor / Codex / Windsurf config. **Done.**

<details>
<summary><strong>Manual install (Python 3.10+, Docker for LibreCrawl backend)</strong></summary>

```bash
git clone https://github.com/adityaarsharma/librecrawl-mcp.git
cd librecrawl-mcp
python3 -m venv venv && source venv/bin/activate
pip install httpx mcp weasyprint markdown fpdf2
# Start LibreCrawl backend on :5080 (see install.sh for Docker compose)
python server.py
```

Add to your client config (Claude Desktop example):

```json
{
  "mcpServers": {
    "librecrawl": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://127.0.0.1:5081/mcp"]
    }
  }
}
```

</details>

---

## 🚀 50+ checks every audit

<table>
<tr>
<td valign="top" width="50%">

#### 🔒 Security & headers
`missing_hsts` · `missing_csp` · `missing_x_frame_options` · `missing_x_content_type_options` · `missing_referrer_policy` · `x_robots_tag_vs_meta_mismatch` · `mixed_content`

#### 🛡️ WAF / bot-block detection
`bot_block_challenge_detected` — fingerprints **Cloudflare · Akamai · DataDome · Imperva · PerimeterX**

#### 🗺️ Sitemap & robots
`sitemap_url_noindex` · `sitemap_url_3xx` · `sitemap_url_disallowed_in_robots` · `sitemap_contains_canonicalized` · `sitemap_over_50k_urls` · `sitemap_over_50mb`

#### 🌍 Hreflang full audit
`missing_return_tag` · `missing_self_reference` · `missing_x_default` · `invalid_codes` · `to_noindex` · `to_broken` · `conflicts_lang_attr`

#### 🔗 Canonical health
`canonical_chain_depth` · `canonical_to_relative` · `canonical_to_redirect` · `canonical_outside_head` · `bad_canonical`

#### 🔁 Redirects (every flavour)
`redirect_chains` · `meta_refresh_redirect` · `js_redirect` · `http_refresh_redirect`

#### 🏷️ Schema.org (16 types)
Article · Product · Recipe · FAQPage · BreadcrumbList · Event · JobPosting · VideoObject · HowTo · Organization · LocalBusiness · Person · Review · AggregateRating · Course · NewsArticle — validates **schema.org spec** AND **Google Rich Results** required fields. Handles `@graph` (Yoast / RankMath / WPRM).

</td>
<td valign="top" width="50%">

#### 🔤 URL quality
`url_contains_space` · `url_multiple_slashes` · `url_non_ascii` · `url_underscores` · `url_repetitive_path` · `long_urls` · `uppercase_urls` · `url_params_heavy`

#### ⚓ Anchor text
`non_descriptive_anchor_text` · `empty_anchor_text` · `anchor_image_no_alt` · `broken_bookmarks`

#### 🕸️ Internal linking
`internal_nofollow_outlinks` · `nofollow_only_inbound` · `follow_and_nofollow_mixed` · `orphan_pages`

#### 🖼️ Image performance + CLS
`lazy_load_attr_missing` · `srcset_missing` · `image_dimensions_missing` · `next_gen_image_format` · `image_oversized_kb` · `missing_alt_pages` · `broken_img_pages`

#### 📐 HTML structure
`html_over_2mb` · `noscript_in_head` · `broken_or_invalid_html` · `dom_size_excessive` · `lorem_ipsum_detected`

#### ♿ Accessibility / metadata
`iframes_present` · `iframe_missing_title` · `missing_favicon` · `missing_html_lang` · `invalid_html_lang` · `missing_charset` · `missing_viewport`

#### 🪤 Crawl-budget killers
`spider_trap_calendar` · `url_session_id_high_entropy` · `faceted_url_explosion`

#### ✍️ Content quality
`low_readability` (Flesch) · `long_sentences` · `passive_voice_pct` · `missing_terminal_punctuation` · `boilerplate_ratio` · `ai_tell_tokens_found` (delve · unlock · seamlessly · leverage) · `has_lorem_ipsum`

#### 🚨 Dev leaks
`outlinks_to_localhost` (RFC1918 in production)

</td>
</tr>
</table>

**🔗 Every outbound URL HEAD/GET-validated** into 17 status classes — `ok` · `redirect` · `forbidden` · `not_found` · `timeout` · `dns_error` · `ssl_error` · `connection_refused` · etc. Per-target: final URL after redirects, source pages, anchor text, response time, server header.

**📈 GSC merge** — pull Search Console data, call `librecrawl_merge_gsc_data(crawl_id, gsc_data)`. URLs normalised before joining. Emits **4 extra CSVs**: `per-page-with-gsc` · `gsc-winners` · `gsc-losers` (high impr + CTR <2%) · `gsc-quick-wins` (position 11–20 + impr ≥100).

---

## 📊 What every audit produces

Single zip, 8 files:

| File | Use |
|---|---|
| `SUMMARY.txt` | One-page orientation |
| `<domain>-<ts>.pdf` | **Branded human-readable PDF** (open in any viewer) |
| `<domain>-<ts>.md` | Markdown source of the PDF (grep-friendly) |
| `per-page.csv` | 1 row per URL × 30 columns of check booleans + `failed_checks_list` |
| `sitemap-recon.csv` | Sitemap-vs-crawl diff |
| `external-links.csv` | Every outbound URL + status |
| `content-audit.csv` | Per-page readability + AI-tells |
| `extended-checks.csv` | 1 row per (URL × check × severity × detail) — all 50+ checks |

---

## 📖 Your first audit

```text
You:   Audit https://example.com — full site, no caps

Agent: → librecrawl_start_chunked_audit(url=..., total_max_pages=10000)
         returns session_id in <2s

       → polls librecrawl_audit_status every 25s
         status: crawling, pages_done: 47,  current_delay_ms: 250
         status: crawling, pages_done: 312, last chunk p95: 480ms, err_rate: 0%
         status: done,     pages_done: 534, artifacts_ready: true

       → librecrawl_audit_zip(session_id, auto_cleanup=True)
         returns base64 zip (8 files, 320 KB)
         SAVES LOCALLY as example.com-1780572742.zip
         Server wiped: session_rows=4, files=8, upstream_crawl=1

You:   Show me broken pages + broken external links

Agent: → unzips, reads per-page.csv (filters status_4xx OR status_5xx)
       → reads external-links.csv (filters not_found · forbidden · 5xx · timeout)
       → prints both tables
```

**Local zip is the only copy.** Server is back to zero state.

---

## 🛣️ Roadmap (what's next)

| | Status |
|---|:---:|
| **JavaScript rendering** (Playwright headless, DOM diff vs raw HTML) — catches SPA / React / Next.js apps | 🟡 Designed |
| **Core Web Vitals from CrUX** — real-user 28-day field data, not just lab PSI | 🟡 Designed |
| **axe-core accessibility audit** — contrast, ARIA, focus order, alt-text quality | 🟡 Planned |
| **White-label PDF theming** (`--brand-config` for agencies) | 🟡 Planned |
| **Diff mode** — audit A vs audit B, "what regressed since last week?" | 🟡 Planned |
| **Webhook on completion** (Slack / Discord) — ping when long crawls finish | 🟡 Planned |

> **Not planned:** keyword research, backlink analysis, SERP tracking. Those are different problems with different MCP servers (DataForSEO, Ahrefs MCP). This tool is laser-focused on **technical SEO crawling**.

[Open an issue](https://github.com/adityaarsharma/librecrawl-mcp/issues/new) to bump priorities or request a check.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  MCP client (Claude Code / Desktop / Cursor / Codex …)      │
└────────────────────────────┬────────────────────────────────┘
                             │  streamable HTTP or stdio
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  librecrawl-mcp wrapper  (server.py — FastMCP, 37 tools)    │
│  ┌─────────────────┐    ┌──────────────────────────────┐    │
│  │ runner.py       │    │ external_links / schema /    │    │
│  │ background      │    │ content_audit / extended_    │    │
│  │ worker thread   │    │ checks / sitemap_fill /      │    │
│  │ AIMD controller │    │ pdf_report                   │    │
│  └────────┬────────┘    └──────────────────────────────┘    │
│           │                                                  │
│  ┌────────▼────────┐    ┌──────────────────────────────┐    │
│  │ state.py        │    │ libreclient.py — typed       │    │
│  │ SQLite WAL      │    │ wrapper to upstream API      │    │
│  │ session state   │    └──────────────┬───────────────┘    │
│  └─────────────────┘                   │                    │
└─────────────────────────────────────────┼────────────────────┘
                                          │
                                          ▼
                          ┌──────────────────────────────┐
                          │  LibreCrawl Flask backend    │
                          │  :5080 — single-tenant       │
                          │  crawls + extracts SEO data  │
                          └──────────────────────────────┘
```

---

## ⚙️ Configuration

| Env var | Default | Purpose |
|---|---|---|
| `LIBRECRAWL_PORT` | `5080` | LibreCrawl backend port |
| `MCP_PORT` | `5081` | MCP wrapper port |
| `MCP_TRANSPORT` | `http` | `http` (streamable) or `stdio` |
| `REPORTS_DIR` | `~/librecrawl-reports` | Where audit artifacts land |
| `PAGESPEED_API_KEY` | unset | Optional — enables `librecrawl_pagespeed*` |
| `LIBRECRAWL_STATE_DB` | `~/librecrawl-state.db` | SQLite WAL state store |

---

## 🛠️ 37 MCP tools

<details>
<summary><strong>Expand the full tool reference</strong></summary>

**Chunked audit (95% of work):**
- `librecrawl_start_chunked_audit` · `librecrawl_audit_status` · `librecrawl_audit_zip`
- `librecrawl_audit_pause` · `librecrawl_audit_resume` · `librecrawl_audit_cancel` · `librecrawl_audit_force_advance`
- `librecrawl_audit_artifacts` · `librecrawl_audit_pdf` · `librecrawl_report_content`

**Specialist:**
- `librecrawl_external_links_audit` — re-run external-link validation on a specific crawl
- `librecrawl_schema_validate` · `librecrawl_schema_check` · `librecrawl_schema_audit` — schema inspection
- `librecrawl_merge_gsc_data` · `librecrawl_append_gsc_section` — fold in GSC clicks/impressions
- `librecrawl_pagespeed` · `librecrawl_pagespeed_audit` · `librecrawl_pagespeed_audit_all_crawl_pages` — PSI
- `librecrawl_site_check` — instant site-level check
- `librecrawl_internal_links_analysis` · `librecrawl_filter_issues` · `librecrawl_visualization_data`

**Maintenance:**
- `librecrawl_wipe_everything` — nuclear reset to zero
- `librecrawl_brain_purge_audit` — purge a single audit

**Legacy (kept for backwards compat, avoid for big sites):**
- `librecrawl_audit` · `librecrawl_full_audit_strict` · `librecrawl_generate_report` · `librecrawl_export_results` · `librecrawl_get_status` · `librecrawl_get_settings` · `librecrawl_list_crawls` · `librecrawl_start_crawl` · `librecrawl_stop_crawl` · `librecrawl_pause_crawl` · `librecrawl_resume_crawl` · `librecrawl_resume_from_crawl_id`

</details>

---

## 📜 License

**MIT.** Use it on client work, agency work, internal tools, SaaS, anything. No attribution required (but appreciated). See [LICENSE](LICENSE).

---

## 🙏 Credits

- **[LibreCrawl](https://github.com/PhialsBasement/LibreCrawl)** — upstream crawler we wrap. MIT. Go star them.
- **[Anthropic Model Context Protocol](https://modelcontextprotocol.io)** — the protocol this server speaks
- **[WeasyPrint](https://weasyprint.org/)** · **[FastMCP](https://github.com/jlowin/fastmcp)**

---

## ⭐ Star it if this saves you money

Every star moves librecrawl-mcp up GitHub's MCP-server search. The more devs and SEOs who find it, the fewer pay Ahrefs $999/mo for the same data. [**⭐ Star librecrawl-mcp**](https://github.com/adityaarsharma/librecrawl-mcp/stargazers).

[![Star History Chart](https://api.star-history.com/svg?repos=adityaarsharma/librecrawl-mcp&type=Date)](https://star-history.com/#adityaarsharma/librecrawl-mcp&Date)

---

<div align="center">

### Built by [Aditya Sharma](https://adityaarsharma.com) · MIT · No telemetry · No SaaS · No vendor lock-in

</div>

---

<sub>

**Discoverability keywords:** seo audit mcp server · screaming frog alternative open source · free screaming frog alternative · self-hosted seo crawler · sitebulb alternative free · ahrefs site audit alternative · semrush site audit alternative · claude code seo audit · cursor seo mcp · openai codex seo audit · windsurf seo crawler · continue.dev seo mcp · technical seo audit mcp · hreflang audit tool · canonical chain checker · broken link checker unlimited · core web vitals audit cli · structured data validator command line · schema.org rich results validator · sitemap audit tool · sitemap orphan detection · WAF detection crawler · cloudflare challenge detector · security headers checker · CSP HSTS audit · GSC integration crawler · soft 404 detection · chunked crawler no timeout MCP · technical SEO audit api · python seo crawler · self-hosted screaming frog · open source sitebulb · seo crawler for claude · seo crawler for cursor · model context protocol seo · ai assistant seo audit · ephemeral seo audit · agency-safe seo crawler · white-label seo report · pdf seo report generator · seo audit cli tool · mit-licensed seo crawler · free site audit tool · enterprise seo crawler free · seo agency tools open source

</sub>
