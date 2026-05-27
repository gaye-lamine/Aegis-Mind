# Aegis-Mind: Architecture Diagram

This document presents the detailed architectural blueprint of **Aegis-Mind — Autonomous Multi-Agent NOC for Incident Response**, showing how the core agents, external systems (Splunk), and user interfaces coordinate to manage infrastructure crises autonomously.

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

---

## 🔄 Execution & Data Flow

### Step 1: Detection & Triggering (AI Custom Alert)
*   **Telemetry Ingestion:** Infrastructure logs (Kubernetes auditing logs, AWS CloudTrail, system logs, firewalls, and database events) are continuously ingested and indexed inside **Splunk Enterprise**.
*   **Trigger Mechanism:** A custom automated alert query monitors the incoming data stream for indicators of compromise (IoCs) or operational anomalies.
*   **Action:** When a high-severity security incident is detected, the Splunk daemon executes the custom alert action, transmitting the incident metadata payload securely to the **Aegis-Mind Gateway**.

### Step 2: Cyber Triage & Forensic Analysis (Triage Agent)
*   **Orchestration:** The triage workflow is initialized under the control of the **Google Antigravity SDK** orchestrator.
*   **Assigned Model:** `Foundation-Sec-1.1-8B-Instruct`.
*   **System Interactions:**
    *   The agent connects to the local **Splunk MCP Server** using secure bearer Token Authentication.
    *   It communicates via natural language queries, which the MCP client translates into syntactically valid SPL queries.
    *   It extracts raw audit logs surrounding the suspicious entities (e.g., target user, container, source IP) from the past 2 hours to reconstruct the attack timeline.
    *   **Quota Circuit Breaker:** If the Triage Agent determines with high confidence that the alert is a False Positive, the circuit breaker immediately trips, halting downstream processing to conserve API tokens and computing resources.

### Step 3: Time-Series Forecasting & Operational Impact (Time-Series Agent)
*   **Assigned Mission:** Evaluate current system baselines and assess secondary production degradation risks.
*   **Assigned Model:** `Cisco Deep Time Series Model`.
*   **System Interactions:**
    *   The agent queries physical infrastructure performance counters (e.g., network throughput, queue latency, memory usage) via the Splunk MCP Server.
    *   It compares the active workload signatures against historical baseline statistics.
    *   It runs a forecasting algorithm to predict operational metrics at $t+15\text{m}$ and $t+1\text{h}$, automatically elevating the response level if severe degradation or service disruption is imminent.

### Step 4: Playbook Synthesis & Automated Mitigation (Remediation Agent)
*   **Assigned Mission:** Formulate, execute, and verify targeted remediation actions.
*   **Assigned Model:** `gpt-oss-120b`.
*   **System Interactions:**
    *   Synthesizing findings from the Triage (IoCs) and Time-Series (severity metrics) stages, the agent generates a precise, actionable remediation playbook (e.g., Calico network blocking rules, AWS IAM policy revocations, or Kubernetes pod restarts).
    *   It triggers the execution of the playbook in a secure, audited environment.
    *   Post-execution, the agent queries the Splunk MCP Server to verify that system metrics have returned to nominal ranges, confirming full service restoration.

### Step 5: Incident Closure & Post-Mortem Compilation (NOC Console)
*   **Visualization:** Throughout the lifecycle, the agent thoughts, generated SPL queries, metrics, and playbooks are displayed in real-time on the terminal-based **NOC Console**.
*   **Deliverables:** Upon resolution, the gateway automatically compiles a comprehensive incident post-mortem markdown report (`post_mortem_report.md`), including calculated MTTR, financial cost savings, and a dynamic **Mermaid.js sequence diagram** tracing the multi-agent orchestration lifecycle.
