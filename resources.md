# Development Resources: Splunk Agentic Ops Hackathon

This document compiles all developer portal links, official documentation, and support resources utilized during the design and development of Aegis-Mind.

---

## 🔑 Obtaining Splunk Developer Credentials

1.  **Create a Free Splunk Account:**
    *   Register at [splunk.com/en_us/form/sign-up.html](https://www.splunk.com/en_us/form/sign-up.html).
2.  **Download Splunk Enterprise (Trial Installer):**
    *   Access the installer at [splunk.com/en_us/download/splunk-enterprise.html](https://www.splunk.com/en_us/download/splunk-enterprise.html) (valid for 60 days).
3.  **Request a Free Developer License:**
    *   Register under the Splunk Developer Program at [dev.splunk.com](https://dev.splunk.com/) to obtain a free developer license (valid for 6 months).
    *   *Note:* If you already have an existing Splunk Enterprise or Splunk Cloud instance, you can simply request this Developer License and apply it directly to your running instance.

---

## 🛠️ Splunk AI Technologies & Ecosystem

We leverage and integrate several core components from the Splunk AI developer ecosystem:

### 1. AI for Splunk Apps (Python SDK)
Enables building intelligent, agent-driven operations inside custom Splunk apps using the Python SDK.
*   [SDK Repository & Configuration Guide (README)](#)
*   [AI Custom Alert App Implementation Patterns](#)
*   [AI Custom Search App Implementation Patterns](#)
*   [AI Modular Input App Architecture Patterns](#)

### 2. Splunk MCP Server
Provides a secure Model Context Protocol gateway to interface LLM agents with indexed Splunk Enterprise data.
*   **Authentication Requirements:** OAuth 2.0 integration is currently under Controlled Availability (CA). For hackathon development, using **Token-based Authentication (Bearer Tokens)** via the REST API is recommended.
*   [Overview of Splunk MCP Server Integration](https://docs.splunk.com)
*   [Splunk MCP Server Configuration Guide](https://docs.splunk.com)
*   [Securing the MCP Server Gateway with Splunk MCP TA](https://docs.splunk.com)
*   [Splunkbase Download: Splunk MCP Server (App ID: 7931)](https://splunkbase.splunk.com/app/7931)

### 3. Splunk AI Assistant (SAIA)
An intelligent assistant designed to compile and optimize complex Splunk Search Processing Language (SPL) queries from natural language requests.
*   [General Overview: Splunk AI Assistant for SPL](https://docs.splunk.com)
*   [Splunkbase Download: Splunk AI Assistant for SPL](https://splunkbase.splunk.com)
*   [Activating the Enterprise AI Assistant for SPL](https://docs.splunk.com)
*   [Integrating Splunk AI Assistant with Observability Cloud](https://docs.splunk.com)

### 4. Splunk AI Toolkit (AITK)
Allows developers to build, train, and test custom machine learning models to extract predictions and operational insights from custom datasets.
*   [Overview of Splunk AI Toolkit Features](https://docs.splunk.com)
*   [Splunkbase Download: Splunk AI Toolkit App](https://splunkbase.splunk.com)
*   [Implementing AI-Driven Workflows in Splunk Enterprise](https://docs.splunk.com)

### 5. Splunk Hosted Models
Access to pre-trained, enterprise-ready machine learning models:
*   **Foundation AI Security Model (Foundation-Sec-1.1-8B-Instruct):** Tailored specifically for cybersecurity investigation and forensic analysis. [Hugging Face Model Page](https://huggingface.co/Splunk/Foundation-Sec-1.1-8B-Instruct).
*   **Cisco Deep Time Series Model:** Optimized for observability metrics and industrial system performance forecasting.
*   **Other Splunk Open Source Models:** High-parameter models such as `gpt-oss-120b` and `gpt-oss-20b` available on Hugging Face.

---

## 💬 Community Support & Communication

For collaboration and developer assistance during the hackathon:
*   **Dedicated Slack Channel:** `#splunk-ai-hackathon` on the official Splunk Community Slack organization.
*   **Joining Steps:**
    1.  Navigate to the Splunk Slack community login page.
    2.  Sign in using your Splunk developer credentials (or register a free account).
    3.  Search for and join the `#splunk-ai-hackathon` workspace channel.
