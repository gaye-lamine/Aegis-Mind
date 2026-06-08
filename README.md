# Aegis-Mind: Autonomous Multi-Agent NOC for Incident Response

Aegis-Mind is an autonomous, event-driven incident response and threat mitigation system (SOC/NOC) designed to analyze and remediate high-priority security and operational events. Built for the **Splunk Agentic Ops Hackathon**, it leverages the **Google Antigravity SDK** alongside the **Splunk Model Context Protocol (MCP) Server** to automate triage, predict performance impact, and execute secure, audited remediation playbooks.

---

## 🎯 Core System Capabilities

### 1. Autonomous Multi-Agent Cell (`src/agents/`)
Aegis-Mind orchestrates a collaborative, multi-agent cell composed of three specialized components:
*   **🕵️‍♂️ Triage Agent:** Integrates Splunk-hosted `Foundation-Sec-1.1-8B-Instruct` model logic. It queries raw telemetry via the **Splunk MCP Server** to perform forensic analysis, identify attack vectors, and trace source indicators of compromise (IoCs).
*   **📊 Time-Series Agent:** Emulates a `Cisco Deep Time Series` model. It analyzes operational trends (e.g., network throughput, CPU utilization) to forecast potential performance degradation at $t+15\text{m}$ and $t+1\text{h}$, dynamically adjusting incident severity based on predictive metrics.
*   **⚡ Remediation Agent:** Implements `gpt-oss-120b` reasoning. It synthesizes forensic data from the Triage and Time-Series agents to generate targeted playbooks (e.g., Calico network policy adjustments, AWS IAM policy revocations) and validates system restoration via Splunk queries.

### 2. Quota Circuit Breaker (`src/utils/circuit_breaker.py`)
To optimize Splunk API usage and manage LLM token consumption, a **Circuit Breaker** monitor tracks operational costs. If an anomalous event is determined to be a False Positive by the Triage Agent, the circuit breaker immediately trips, preventing unnecessary downstream agent invocation.

### 3. Interactive NOC Console (`src/main.py`)
A standalone terminal-based console utilizing ANSI formatting. It provides a visual interface for users to select, execute, and monitor built-in incident scenarios, exposing the underlying multi-agent reasoning trace.

### 4. Automated Post-Mortem Generation
Upon incident resolution, the orchestrator generates a comprehensive markdown post-mortem report (`post_mortem_report.md`). The report documents calculated Mean Time to Resolution (MTTR), quantified cost savings, and compiles an automated **Mermaid.js sequence diagram** tracing the chronological agent interactions.

---

## 🏗️ System Architecture

```text
[ Infrastructure Telemetry ]
             │
             ▼ (Continuous Ingestion)
┌───────────────────────────────────────────────┐
│              Splunk Enterprise                │◄────────┐
│               (Search Engine)                 │         │
│                                               │         │
└───────────────────────┬───────────────────────┘         │
                        │                                 │
     AI Custom Alert    │ (Token Auth)                    │ SPL Queries /
     Trigger            ▼                                 │ Tool-Calling
┌───────────────────────────────────────────────┐         │ (Splunk MCP Server)
│             Aegis-Mind Gateway                │         │
└───────────────────────┬───────────────────────┘         │
                        │                                 │
                        ▼ (Task Orchestration)            │
┌─────────────────────────────────────────────────────────┼────────┐
│                     AEGIS-MIND CORE                     │        │
│                                                         │        │
│    ┌─────────────────────────────────────────────┐      │        │
│    │  🕵️‍♂️ Triage Agent                            ├──────►│        │
│    │  Model: Foundation-Sec-1.1-8B-Instruct      │      │        │
│    └──────────────────────┬──────────────────────┘      │        │
│                           │                             │        │
│    ┌──────────────────────▼──────────────────────┐      │        │
│    │  📊 Time-Series Agent                       ├──────►│        │
│    │  Model: Cisco Deep Time Series Model        │      │        │
│    └──────────────────────┬──────────────────────┘      │        │
│                           │                             │        │
│    ┌──────────────────────▼──────────────────────┐      │        │
│    │  ⚡ Remediation Agent                       ├──────┘        │
│    │  Model: gpt-oss-120b                        │               │
│    └─────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

For detailed data flow documentation, see [architecture_diagram.md](architecture_diagram.md).

---

## 🚀 Getting Started & Evaluation Guide

Aegis-Mind features a high-fidelity simulation engine pre-loaded with representative incident datasets. Evaluators can execute the complete agentic incident response loop locally with **zero external dependencies** and **no prior API configuration**.

### 1. Prerequisites
Ensure you have **Python 3.8+** installed. The simulation engine uses **only the Python standard library** — no `pip install` required.

> See [`requirements.txt`](requirements.txt) for production dependency details.

### 2. Installation
Clone the repository and navigate to the project directory:
```bash
git clone https://github.com/gaye-lamine/Aegis-Mind.git
cd Aegis-Mind
```

### 3. Run the NOC Interactive Console
Execute the orchestrator:
```bash
python3 src/main.py
```

### 4. Incident Scenarios
When the NOC Console starts, select from the three available evaluation scenarios:
1.  `[1]` **Kubernetes Credential Exfiltration:** A critical cloud intrusion. Triggers triage, predictive performance analysis, Calico network blocking, AWS IAM token revocation, and generates the final markdown post-mortem report.
2.  `[2]` **SSH Brute-Force Attack (True Positive):** Triage analysis of malicious login attempts, time-series forecasting, and automated blocklist mitigation.
3.  `[3]` **SSH Brute-Force Attack (False Positive):** Demonstrates the **Quota Circuit Breaker** tripping early in the pipeline to conserve LLM tokens and API resources upon verifying a low-risk pattern.

---

## 🔒 Production Splunk Integration

To connect Aegis-Mind to a live production Splunk instance:

1.  **Configure Splunk MCP Server:** Install the Splunk MCP Server (App ID 7931) on your Splunk Enterprise instance.
2.  **Generate Developer Token:** Obtain a secure bearer Token from the Splunk Developer portal.
3.  **Update Config:** Update `src/mcp_client.py` initialization parameters to point to your live hostname:
    ```python
    client = SplunkMCPClient(use_mock=False, token="YOUR_SPLUNK_DEVELOPER_TOKEN", host="your-splunk-instance.com")
    ```

---

## 📋 Open Source Licensing
Aegis-Mind is distributed under the open-source **MIT License**. See [LICENSE](LICENSE) for full details.
