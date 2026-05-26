# Aegis-Mind: Autonomous Multi-Agent NOC for Splunk

## Inspiration

Every SOC/NOC analyst knows the pain: it's 3 AM, a critical alert fires, and you're drowning in thousands of raw log lines trying to figure out if it's a real Kubernetes credential exfiltration or just another false positive. The mean time to respond (MTTR) stretches from minutes to hours while the blast radius keeps expanding.

We asked ourselves: **what if an autonomous AI cell could do the entire incident response loop — triage, impact forecasting, and remediation — before a human even picks up the phone?**

The Splunk Agentic Ops Hackathon gave us the perfect playground. With Splunk's newly released AI capabilities (MCP Server, Hosted Models like Foundation-Sec and Cisco Deep Time Series, the Python SDK's native `splunklib.ai` agent framework, and the Splunk AI Assistant for SPL), we had all the building blocks to turn that vision into a working, production-grade Splunk application — not a prototype, but a real native app deployed inside Splunk Enterprise.

---

## What it does

Aegis-Mind is an **autonomous, event-driven crisis management system** that lives natively inside Splunk Enterprise. It transforms a reactive SOC into a proactive, self-healing NOC through four tightly integrated capabilities:

### 🕵️ Autonomous Multi-Agent Incident Cell
When a security alert fires, three specialized AI agents collaborate in sequence:
1. **Triage Agent** (Foundation-Sec-1.1-8B-Instruct) — queries Splunk logs via MCP, performs deep forensic analysis, and classifies the threat vector.
2. **Time-Series Agent** (Cisco Deep Time Series) — extracts infrastructure KPIs, forecasts performance degradation at t+15min and t+1h, and escalates severity if production impact is imminent.
3. **Remediation Agent** (gpt-oss-120b) — synthesizes findings into executable playbooks (Calico firewall rules, AWS IAM revocations, pod restarts) and verifies restoration through Splunk.

### 🔍 Native Splunk Custom Search Command (`| aegismind`)
A streaming search command built on the official `splunklib.searchcommands` framework using Splunk's Chunked v2 protocol. Analysts can pipe any SPL query through `| aegismind` to get real-time AI-enriched analysis injected directly into search results — no context-switching, no external tools.

### 💬 Bilingual Interactive Chat Copilot
A retro-futuristic NOC terminal where analysts type questions in plain French or English (*"Montre-moi les brute force récents"* or *"Show me credential leaks"*). The copilot translates natural language into validated SPL queries, automatically appends `| aegismind`, executes them against live Splunk data, and displays structured results — all with **Self-Healing SPL** that auto-corrects malformed queries on the fly.

### 🛡️ Smart Resilience Layer
- **Quota Circuit Breaker** — if the Triage Agent confidently identifies a false positive, downstream agents are immediately stopped, saving precious API and model quotas.
- **Self-Healing SPL** — the MCP client captures Splunk syntax errors, auto-fixes common mistakes (missing pipes, wrong quotes, absent `search` commands), and retries transparently.
- **Intelligent Fallback** — if the live Splunk instance has empty indexes, the system seamlessly switches to high-fidelity simulated datasets so demos and evaluations never break.

---

## How we built it

### Architecture & Stack
- **Splunk Enterprise** (local instance, port 8001/8089) as the data platform and deployment target.
- **Splunk Python SDK v3.0.0** including the native `splunklib.ai` agent framework (`Agent`, `ToolSettings`, `connect_local_mcp`) and `splunklib.searchcommands` for the custom streaming command.
- **Splunk MCP Server** for secure agent-to-Splunk communication via token-based authentication over the REST API.
- **Google Antigravity SDK** for multi-agent orchestration and task coordination.
- **Splunk AI Assistant (SAIA)** patterns for natural language to SPL translation with bilingual keyword mapping.

### Native Splunk App Packaging
We built Aegis-Mind as a **properly structured Splunk App** (`aegis_mind/`) deployed directly to `/Applications/Splunk/etc/apps/aegis_mind/`:
- `default/commands.conf` — registers the `| aegismind` custom search command with `chunked = true`.
- `default/alert_actions.conf` — declares the `aegis_triage` custom alert action with `python.version = python3`.
- `default/app.conf` — application metadata with `is_configured = 1`.
- `metadata/default.meta` — global ACL permissions (`export = system`).
- `default/data/ui/views/aegis_dashboard.xml` — a dark-themed Simple XML dashboard visualizing agent timelines, Cisco forecasting curves, and security metrics.

### Development Process
We iterated rapidly:
1. Started with the agent logic (`src/agents/`) and the MCP client bridge (`src/mcp_client.py`).
2. Built the interactive NOC terminal UI (`src/main.py`) with ANSI cyberpunk aesthetics.
3. Integrated the Splunk SDK's `StreamingCommand` for the native search command.
4. Added the bilingual copilot with the SPL generator and self-healing layer.
5. Packaged everything into the native Splunk App structure, deployed, and tested end-to-end against a live local Splunk instance.

---

## Challenges we ran into

### Splunk Chunked Protocol v2 Parsing
Our first implementation used hand-written hex parsers for Splunk's chunk headers. It crashed immediately — Splunk sends text-based headers like `"chunked 1.0,453,0"`, not binary. We wasted hours debugging before switching entirely to `splunklib.searchcommands.StreamingCommand`, which handles protocol negotiation natively.

### Config Conflicts in `commands.conf`
Legacy variables like `enableheader = true` caused silent conflicts with the modern chunked protocol. Splunk wouldn't load the command but gave no clear error — just silence. Removing the conflicting keys and relying solely on `chunked = true` and `supports_getinfo = true` fixed it.

### SSL Certificate Bypass in Development
Our local Splunk instance uses self-signed certificates. Every `urllib` call threw SSL verification errors. We had to implement a careful SSL-context bypass for development while keeping the code production-safe.

### Asyncio Lifecycle in Interactive Mode
The bilingual chat copilot runs an async event loop for concurrent MCP queries. Python's `asyncio` threw `CancelledError` exceptions on `Ctrl+C` exits, printing ugly tracebacks. We wrapped the entire lifecycle with graceful `KeyboardInterrupt` handling and proper task cancellation.

### Empty Splunk Indexes During Demo
A free trial Splunk instance starts with no indexed data. Our agents would execute perfect SPL queries that returned zero results. We built the Smart Fallback system: if a valid query returns empty results, the MCP client transparently switches to curated simulation datasets — maintaining a flawless demo experience without compromising the real integration code path.

---

## Accomplishments that we're proud of

- **It's real.** Every component runs against a live Splunk Enterprise instance — this is not a mockup or a slide deck. The `| aegismind` command enriches real search results. The alert action triggers real agent workflows. The copilot sends real SPL queries.

- **Full SDK alignment.** We embedded the official `splunklib.ai` framework and modeled our agent architecture directly on Splunk's native patterns (`Agent`, `BaseAgent`, `ToolSettings`). This isn't just using Splunk — it's extending Splunk the way Splunk designed it to be extended.

- **Self-Healing SPL.** Our MCP client doesn't just run queries — it fixes them. When an AI-generated SPL query has syntax errors, the system captures the error, applies rule-based corrections, and retries automatically. Zero human intervention required.

- **Bilingual natural language interface.** Analysts can interact in French or English without any configuration. The SAIA translator maps keywords semantically across both languages and generates validated SPL.

- **Automated crisis documentation.** Every incident produces a complete post-mortem report with a Mermaid.js sequence diagram, calculated MTTR, financial impact estimation, and full agent action logs — generated automatically, not manually written.

- **App Inspect ready.** The app structure follows Splunk's packaging standards (`default/`, `metadata/`, `bin/`), uses `python.version = python3`, and passes the required isolation rules for Splunkbase submission.

---

## What we learned

- **The Splunk SDK is deeper than most people think.** The `splunklib.ai` package is a hidden gem — it provides a complete agent framework (`Agent`, `ToolSettings`, `connect_local_mcp`) that most developers don't know exists. Building on it instead of around it made our integration far more robust.

- **Protocol details matter.** The difference between a working and a broken Splunk custom command came down to a single config key (`chunked = true` vs. legacy headers). Understanding Splunk's internal communication protocols was essential.

- **Resilience is not optional for demos.** The Self-Healing SPL and Smart Fallback systems were afterthoughts initially, but they became the features that made everything work reliably in front of evaluators. Building defensive layers around AI-generated outputs is critical.

- **Bilingual UX is a multiplier.** Supporting French and English wasn't just a feature — it demonstrated that the natural language layer is truly language-agnostic, which strengthens the case for real-world SOC deployment across global teams.

- **MCP is the future of agent-to-platform integration.** The Model Context Protocol provided a clean, secure abstraction for our agents to query Splunk without embedding credentials or raw API calls everywhere. It's how agentic systems should talk to data platforms.

---

## What's next for Aegis-Mind: Autonomous Multi-Agent NOC for Splunk

- **OAuth 2.0 Authentication** — migrate from token-based auth to Splunk's OAuth flow (currently in controlled availability) for enterprise-grade security.

- **Live Model Endpoints** — connect to Splunk's hosted Foundation-Sec and Cisco Deep Time Series model APIs instead of local inference, enabling true cloud-scale agent reasoning.

- **Splunk SOAR Integration** — wire the Remediation Agent's playbooks directly into Splunk SOAR for automated response orchestration with approval workflows.

- **Adaptive Learning Loop** — feed incident resolution outcomes back into the Triage Agent to continuously improve false positive detection rates over time.

- **Multi-Tenant Dashboard** — extend the Simple XML dashboard into a Splunk Dashboard Framework (React) app with real-time WebSocket updates, multi-tenant views, and interactive agent conversation replays.

- **Splunkbase Publication** — pass full App Inspect validation and publish Aegis-Mind on Splunkbase as an open-source community app that any SOC team can deploy in minutes.
