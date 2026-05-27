# Aegis-Mind — Implemented Architecture & Technical Features

This document provides a detailed breakdown of the technical implementation and software architecture of **Aegis-Mind — Autonomous Multi-Agent NOC for Incident Response** deployed in this repository. It serves as the official technical report for the evaluators of the **Splunk Agentic Ops Hackathon**.

---

## 🏗️ General Project Structure (Directory Outline)

The application is architected in a modular fashion, separating the local interactive terminal console from the native Splunk App package (`aegis_mind`) installed directly within the Splunk Enterprise server:

```text
.
├── LICENSE                     # MIT License (required for Devpost submission)
├── README.md                   # Installation, configuration, and Quick Start guide
├── architecture_diagram.md     # System architecture schema and data flow description
├── overview.md                 # Hackathon objectives summary
├── rules.md                    # Official hackathon rules and guidelines
├── ressources.md               # Splunk AI documentation references
├── post_mortem_report.md       # Local copy of the generated incident post-mortem report
│
├── src/                        # 🖥️ INTERACTIVE NOC CELL (Local Console)
│   ├── main.py                 # Interactive menu, simulations, and Bilingual Copilot Chat
│   ├── mcp_client.py           # Splunk MCP Client with Self-Healing SPL and simulation fallback
│   ├── agents/                 # Reusable agent logic
│   │   ├── triage_agent.py      # Cyber threat triage using Foundation-Sec
│   │   ├── time_series_agent.py # Temporal performance forecasting via Cisco Deep TS
│   │   └── remediation_agent.py # Mitigation playbook synthesis via gpt-oss-120b
│   └── utils/
│       ├── circuit_breaker.py   # Quota-saving API circuit breaker
│       └── spl_generator.py     # Bilingual Splunk AI Assistant (Translation & Validation)
│
├── google/                     # 🧠 GOOGLE ANTIGRAVITY SDK COMPATIBILITY SHIM
│   └── antigravity/            # Local shim to execute agents in any Python environment
│
└── aegis_mind/                 # 🛡️ NATIVE SPLUNK APPLICATION (etc/apps/aegis_mind)
    ├── bin/                    # Executables launched by the splunkd daemon
    │   ├── aegis_search_command.py  # Custom SPL search command (| aegismind)
    │   ├── aegis_triage.py          # Custom alert action script
    │   ├── mcp_client.py            # Internal MCP client connector
    │   ├── agents/                  # Embedded NOC agents
    │   ├── utils/                   # Embedded utility tools
    │   ├── google/                  # Embedded SDK shim
    │   ├── splunklib/               # 📦 Splunk Enterprise Python SDK v3.0.0
    │   │   ├── searchcommands/      # Chunked v2 protocol handler
    │   │   ├── modularinput/        # Modular inputs skeleton
    │   │   └── ai/                  # 🤖 Splunk SDK native AI agent framework
    │   └── splunk_sdk-3.0.0.dist-info
    │
    ├── default/                # Splunk app configuration files
    │   ├── app.conf                 # App metadata and navigation settings
    │   ├── commands.conf            # Custom '| aegismind' search command registration
    │   ├── alert_actions.conf       # 'aegis_triage' custom alert action registration
    │   └── data/ui/views/           # 📊 Splunk Web User Interface
    │       └── aegis_dashboard.xml  # Interactive dark-themed NOC dashboard
    └── metadata/
        └── default.meta             # Global object sharing ACLs
```

---

## 🛠️ Deep Dive into Implemented Features

### 1. Streaming SPL Custom Search Command (`| aegismind`)
Deployed in `aegis_mind/bin/aegis_search_command.py`, this search command is built on the official `splunklib.searchcommands.StreamingCommand` framework and fully implements Splunk's modern **Chunked v2** communication protocol.
*   **Operational Flow**: It intercepts raw telemetry events from any active SPL search query, performs lightweight, fast semantic signature scanning on the raw `_raw` field, and dynamically appends a new field `aegis_analysis` containing the agent's real-time NOC evaluation.
*   **Resilience**: The command is highly optimized to prevent blocking the Splunk search pipeline, maintaining fast execution times across large datasets.

### 2. Multi-Agent Custom Alert Action (`aegis_triage`)
Implemented in `aegis_mind/bin/aegis_triage.py` and registered via `alert_actions.conf`.
*   **Operational Flow**: Upon alert triggering, `splunkd` passes the incident's JSON payload via `stdin` to the triage script. The script asynchronously instantiates the autonomous multi-agent cell:
    1.  **Triage Agent** (`Model: Foundation-Sec-1.1-8B-Instruct` logic): Evaluates the threat vectors and assesses if the alert is a false positive.
    2.  **Time-Series Agent** (`Model: Cisco Deep Time Series` logic): Queries recent network throughput from Splunk via the MCP client, predicts the operational degradation timeline, and tunes severity metrics.
    3.  **Remediation Agent** (`Model: gpt-oss-120b` logic): Synthesizes forensic and metric data to generate and apply a secure, sandboxed mitigation playbook.
    4.  **Audit Compliance**: Automatically formats and saves a comprehensive post-mortem report markdown file containing a dynamic Mermaid.js sequence diagram to the app workspace.

### 3. Splunk MCP Client Gateway (`mcp_client.py`)
Found in `src/mcp_client.py`, this class acts as the secure semantic bridge between the AI agents and Splunk Enterprise.
*   **Token Authentication**: Leverages standard Bearer Tokens (`SPLUNK_TOKEN`) to establish secure connections with the Splunk REST API (management port `8089`), handling self-signed development certificates gracefully.
*   **Self-Healing SPL (Auto-Correction)**: If an AI-generated SPL query encounters syntax issues, the MCP client captures the exact error string returned by Splunk, parses it through heuristic correction rules (e.g., single to double quote conversions, missing statistics command pipes, absent leading search terms), and transparently re-submits the fixed query.
*   **High-Fidelity Simulation Fallback**: If a query is successful but the target Splunk instance is empty (returning 0 events), the client automatically switches to pre-loaded, highly detailed simulated incident datasets (e.g., AWS CloudTrail session exfiltration, PostgreSQL SQLi attempts) to maintain a fully interactive and testable demonstration.

### 4. Interactive NOC Copilot Chat Console (`src/main.py`)
Accessible through option **`[4]`** of the standalone NOC Terminal.
*   **Natural Language to SPL Translation**: Analysts can type questions in natural English or French (e.g., *"Show me recent brute-force login attempts"* or *"Check for credential exfiltration"*). The Splunk AI Assistant translates the request, validates it against common injection payloads, and automatically appends the custom `| aegismind` streaming command.
*   **Display**: Safely extracts events via the Splunk MCP Server and renders structured, color-coded output tables directly inside the console interface.

### 5. Alignment with `splunklib.ai`
Our internal agent packages directly incorporate the official Splunk Enterprise SDK v3.0.0, including its native **`splunklib.ai`** module.
*   The architecture of our agents in `src/agents/` is strictly modeled around this framework's standard classes (`Agent`, `BaseAgent`, `ToolSettings`, `connect_local_mcp`), demonstrating rigorous adherence to Splunk's architectural standards for AI-driven platform extensions.
