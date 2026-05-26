# 🚀 Aegis-Mind: Autonomous Multi-Agent NOC for Incident Response

Aegis-Mind is an autonomous, event-driven crisis management and incident response system (SOC/NOC) designed to instantly mitigate high-priority security and operational threats. Built for the **Splunk Agentic Ops Hackathon**, it combines the **Google Antigravity SDK** with the **Splunk Model Context Protocol (MCP) Server** to automate incident triage, predict operational performance degradation, and execute secure remediation playbooks.

---

## 🎯 Core Features & "WOW" Factors

### 1. Autonomous Multi-Agent Cell (`src/agents/`)
Aegis-Mind deploys a collaborative triage cell of three specialized AI agents:
*   **🕵️‍♂️ Triage Agent:** Utilizing the Splunk hosted `Foundation-Sec-1.1-8B-Instruct` model logic. It queries Splunk logs via the **Splunk MCP Server** to run deep forensic triage, identifying the attack vector and malicious sources.
*   **📊 Time-Series Agent:** Simulating the `Cisco Deep Time Series Model`. It parses network throughput and CPU usage trends to predict production performance degradation at $t+15\text{m}$ and $t+1\text{h}$, automatically scaling critical incident response severity.
*   **⚡ Remediation Agent:** Powered by `gpt-oss-120b` logic. It synthesizes forensic telemetry to craft target playbooks (e.g. Calico firewall IP drops, AWS IAM trust policy revocations) and queries Splunk to verify restoration.

### 2. Quota Circuit Breaker (`src/utils/circuit_breaker.py`)
To prevent "alert fatigue" and save precious Splunk API and model resource quotas, the **Circuit Breaker** continuously counts API searches. If an alert is confidently classified as a False Positive by the Triage Agent, it immediately trips, stopping downstream execution.

### 3. Interactive NOC Terminal UX (`src/main.py`)
A gorgeous, standalone, retro-futuristic dark-themed command-line dashboard utilizing colorful ANSI formatting. It allows judges to select and inject pre-configured incident scenarios in real-time and observe the agents' step-by-step thinking processes.

### 4. Automated Post-Mortem Report Generator
At the completion of each incident, the orchestrator compiles and saves a comprehensive incident post-mortem markdown document (`post_mortem_report.md`) containing calculated MTTR, financial cost savings, detailed agent actions, and a dynamic **Mermaid.js sequence diagram** representing the entire crisis lifespan.

---

## 🏗️ System Architecture

```text
[ Infrastructure Télémétrie ]
             │
             ▼ (Ingestion continue)
┌───────────────────────────────────────────────┐
│              Splunk Enterprise                │◄────────┐
│             (Moteur de Recherche)             │         │
└───────────────────────┬───────────────────────┘         │
                        │                                 │
     Déclenchement      │ (Token Auth)                    │ Requêtes SPL /
    AI Custom Alert     ▼                                 │ Tool-Calling
┌───────────────────────────────────────────────┐         │ (Splunk MCP Server)
│             Aegis-Mind Gateway                │         │
└───────────────────────┬───────────────────────┘         │
                        │                                 │
                        ▼ (Orchestration des Tâches)      │
┌─────────────────────────────────────────────────────────┼────────┐
│                     AEGIS-MIND CORE                     │        │
│                                                         │        │
│    ┌─────────────────────────────────────────────┐      │        │
│    │  🕵️‍♂️ Agent d'Investigation (Triage)         ├──────►│        │
│    │  Modèle : Foundation-Sec-1.1-8B-Instruct     │      │        │
│    └──────────────────────┬──────────────────────┘      │        │
│                           │                             │        │
│    ┌──────────────────────▼──────────────────────┐      │        │
│    │  📊 Agent de Corrélation Temporelle         ├──────►│        │
│    │  Modèle : Cisco Deep Time Series Model      │      │        │
│    └──────────────────────┬──────────────────────┘      │        │
│                           │                             │        │
│    ┌──────────────────────▼──────────────────────┐      │        │
│    │  ⚡ Agent d'Auto-Remédiation (Playbook)      ├──────┘        │
│    │  Modèle : gpt-oss-120b                      │               │
│    └─────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

See [architecture_diagram.md](architecture_diagram.md) for full data flow descriptions.

---

## 🚀 Quick Start (Testing for Judges)

Aegis-Mind features an **interactive simulator mode** pre-loaded with high-impact incident datasets. Judges can run the entire agentic incident response loop locally with **zero external dependencies** and **zero configuration overhead**.

### 1. Prerequisites
Ensure you have **Python 3.8+** installed.

### 2. Installation
Clone the repository and navigate to the root directory:
```bash
git clone https://github.com/your-username/aegis-mind.git
cd aegis-mind
```

### 3. Run the NOC Interactive Terminal
Launch the orchestrator dashboard:
```bash
python3 src/main.py
```

### 4. Interactive Scenarios
When the NOC Shell opens, choose one of three pre-configured incident scenarios:
1.  `[1]` **Kubernetes Credential Exfiltration:** A critical cloud intrusion. Triggers full triage, time-series prediction, Calico firewall drops, AWS IAM token revocations, and generates the Mermaid post-mortem report.
2.  `[2]` **Brute-Force SSH attack (True Positive):** High-intensity brute-force triage, threshold analysis, blocklist mitigation.
3.  `[3]` **Brute-Force SSH attack (False Positive):** Demonstrates the **Circuit Breaker** tripping immediately to save API quotas upon low-intensity authentication failures.

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
Aegis-Mind is distributed under the open-source **MIT License**. Check [LICENSE](LICENSE) for full details.
