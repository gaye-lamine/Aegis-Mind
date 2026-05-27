#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom Splunk alert action for Aegis-Mind autonomous triage.

Entry point invoked by Splunkd when a configured alert fires. Orchestrates
the full multi-agent investigation pipeline — triage, time-series impact
analysis, and auto-remediation — then writes a post-mortem report.
"""

import asyncio
import os
import sys
import json
import logging
import time

# Add the bin directory to sys.path for clean local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import SplunkMCPClient
from utils.circuit_breaker import QuotaCircuitBreaker
from agents.triage_agent import TriageAgent
from agents.time_series_agent import TimeSeriesAgent
from agents.remediation_agent import RemediationAgent

# Configure logging for Splunkd (custom alert script output goes to $SPLUNK_HOME/var/log/splunk/splunkd.log)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AegisMind.CustomAlertAction")


async def run_agentic_triage(alert_name: str, payload: dict) -> dict:
    """Orchestrate the Aegis-Mind autonomous multi-agent cell on a Splunk alert.

    Runs the full investigation pipeline: forensic triage → time-series impact
    analysis → automated remediation. The circuit breaker may halt the pipeline
    early if a false positive is detected or the request quota is exceeded.

    Args:
        alert_name: Name of the triggered Splunk alert.
        payload: JSON payload containing the alert's matching events.

    Returns:
        Investigation result dict with triage, time-series, and remediation data.
    """
    logger.info(f"Starting Aegis-Mind crisis cell for alert: {alert_name}")

    # 1. Initialize MCP client, circuit breaker, and agent instances
    # Note: Connection credentials (token, etc.) are loaded automatically by the client via .env
    mcp_client = SplunkMCPClient()
    mcp_client.connect()

    cb = QuotaCircuitBreaker(max_requests=5, fp_confidence_threshold=0.85)

    t_agent = TriageAgent(mcp_client)
    ts_agent = TimeSeriesAgent(mcp_client)
    rem_agent = RemediationAgent(mcp_client)

    # 2. Initial Forensic Triage
    triage_res = await t_agent.run_investigation(alert_name, payload, cb)
    logger.info(f"Cyber triage completed. False Positive: {triage_res.get('is_false_positive')}")

    if cb.tripped:
        logger.warning(f"Circuit breaker tripped: {cb.trip_reason}")
        return {
            "status": "SUPPRESSED",
            "reason": cb.trip_reason,
            "triage": triage_res
        }

    # 3. Temporal Impact Analysis
    ts_res = await ts_agent.analyze_impact(triage_res, cb)
    logger.info(f"Temporal analysis completed. Severity: {ts_res.get('severity_adjustment')}")

    # 4. Auto-Remediation & Playbook Execution
    rem_res = await rem_agent.execute_remediation(triage_res, ts_res, cb)
    logger.info(f"Remediation playbook applied successfully. Final status: {rem_res.get('status')}")

    # 5. Save post-mortem report under var/run/splunk for Splunk access
    splunk_run_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_file = os.path.join(splunk_run_dir, "aegis_post_mortem.md")

    # Write the local incident report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Aegis-Mind Incident Report\n\nIncident resolved successfully.\nAction: {rem_res.get('mitigation_action')}\n")

    logger.info(f"Incident report saved to {report_file}")

    return {
        "status": "SUCCESS",
        "triage": triage_res,
        "time_series": ts_res,
        "remediation": rem_res
    }


def main():
    """Standard entry point executed by Splunkd when an alert fires."""
    logger.info("Aegis-Mind Alert Action started by Splunkd.")

    # Splunk passes the incident JSON payload (containing matching events) via stdin
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        try:
            # Read the payload from stdin
            payload_str = sys.stdin.read()
            if not payload_str:
                logger.error("No payload received from Splunkd via stdin.")
                sys.exit(1)

            payload = json.loads(payload_str)

            # Extract alert metadata
            alert_name = payload.get("search_name", "Kubernetes Suspicious Event")
            result_events = payload.get("result", {})  # The event that triggered the alert

            # Run the agentic investigation asynchronously
            loop = asyncio.get_event_loop()
            res = loop.run_until_complete(run_agentic_triage(alert_name, result_events))

            # Splunkd expects exit code 0 to confirm successful action execution
            print(json.dumps({"status": "SUCCESS", "details": res}))
            sys.exit(0)

        except Exception as e:
            logger.critical(f"Fatal error during Aegis-Mind alert execution: {e}", exc_info=True)
            sys.exit(2)
    else:
        logger.error("Invalid usage. Must be called with '--execute'.")
        sys.exit(1)


if __name__ == "__main__":
    main()
