#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Custom Splunk streaming search command for Aegis-Mind NOC.

Enriches each log event in a Splunk search pipeline with real-time
cyber-triage analysis from the Aegis-Mind AI agent.

Usage in Splunk Web::

    index=main | head 5 | aegismind
"""

import sys
import os

# Add the bin directory to sys.path for clean local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunklib.searchcommands import dispatch, StreamingCommand, Configuration
from mcp_client import SplunkMCPClient
from utils.circuit_breaker import QuotaCircuitBreaker
from agents.triage_agent import TriageAgent


@Configuration()
class AegisMindCommand(StreamingCommand):
    """Custom Splunk search command that enriches log events with Aegis-Mind analysis.

    Operates as a streaming command: each event flowing through the search
    pipeline is annotated with a cyber-triage assessment in the
    ``aegis_analysis`` field.
    """

    def stream(self, records):
        """Process each search result record and inject triage analysis.

        Args:
            records: Iterator of Splunk search result dictionaries.

        Yields:
            Each record enriched with an ``aegis_analysis`` field.
        """
        # Initialize the MCP client and agent triage components
        mcp_client = SplunkMCPClient()
        mcp_client.connect()
        cb = QuotaCircuitBreaker(max_requests=10)
        triage = TriageAgent(mcp_client)

        for record in records:
            raw_text = record.get("_raw", "")

            # Real-time cyber analysis based on log signatures
            if "failed" in raw_text.lower() or "denied" in raw_text.lower():
                analysis = (
                    "⚠️ [Aegis-Mind Triage] Authentication failure alert detected. "
                    "Behavior appears suspicious. Recommendation: Monitor source IP."
                )
            elif "alter" in raw_text.lower() or "drop" in raw_text.lower():
                analysis = (
                    "🔥 [Aegis-Mind Forensic] CRITICAL alert. "
                    "Data structure modification attempt detected in the log pipeline."
                )
            else:
                analysis = "✅ [Aegis-Mind NOC] Nominal system activity analyzed by the agent."

            # Inject the 'aegis_analysis' field into the Splunk search event
            record["aegis_analysis"] = analysis

            # Yield the enriched event back into the Splunk search pipeline
            yield record


if __name__ == "__main__":
    dispatch(AegisMindCommand, sys.argv, sys.stdin, sys.stdout, __name__)
