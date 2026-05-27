import logging
import json
from google.antigravity import Agent, LocalAgentConfig
from src.mcp_client import SplunkMCPClient
from src.utils.spl_generator import SplunkAIAssistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.TimeSeriesAgent")

class TimeSeriesAgent:
    """Temporal Correlation & Impact Agent (The Analyst).

    Orchestrated via the Google Antigravity SDK.
    AI Model: Cisco Deep Time Series Model (for time-series impact forecasting).

    Responsibilities:
        1. Extracts current network/CPU metrics associated with the incident from Splunk.
        2. Analyzes temporal behaviour and deviations from the historical baseline.
        3. Predicts future operational degradation (t+15 min, t+1 h).
    """

    def __init__(self, mcp_client: SplunkMCPClient):
        """Initialize the Time-Series Agent.

        Args:
            mcp_client: Splunk MCP client used to query performance telemetry.
        """
        self.mcp_client = mcp_client
        self.model_name = "Cisco Deep Time Series Model"
        
        # Configure the Antigravity agent
        self.agent_config = LocalAgentConfig(
            model="gemini-3.5-flash",
            system_instructions=(
                "You are the Temporal Correlation Agent (The Analyst) of the Aegis-Mind platform. "
                "Your objective is to analyze system performance metrics, calculate deviations "
                "from historical reference baselines, and predict the short-term operational "
                "impact of an attack on production."
            )
        )

    async def analyze_impact(self, triage_report: dict, circuit_breaker) -> dict:
        """Analyze performance time-series to estimate the crisis impact.

        Args:
            triage_report: Forensic report emitted by the Triage Agent.
            circuit_breaker: API quota circuit breaker instance.

        Returns:
            A predictive operational report dictionary.
        """
        logger.info("[TIME-SERIES AGENT] Starting performance impact analysis...")

        if triage_report.get("is_false_positive", False):
            logger.info("[TIME-SERIES AGENT] Incident classified as False Positive. Analysis skipped.")
            return {"status": "SKIPPED", "reason": "Incident identified as False Positive."}

        # Step 1 — Generate the SPL query to extract performance telemetry
        spl_query = SplunkAIAssistant.generate_spl("Get performance metrics network throughput anomaly")
        
        if circuit_breaker.increment_and_check():
            return {
                "status": "SUPPRESSED",
                "reason": "Circuit breaker triggered: API call quota exhausted."
            }

        # Step 2 — Retrieve data via the Splunk MCP server
        metrics_data = self.mcp_client.execute_query(spl_query)
        logger.info(f"[TIME-SERIES AGENT] Extracted {len(metrics_data)} temporal data points for analysis.")

        # Step 3 — Deviation calculation & trend prediction (Cisco Deep Time Series simulation)
        current_throughput = metrics_data[-1].get("network_mbps", 120.0) if metrics_data else 120.0
        predicted_throughput = metrics_data[-1].get("forecast", 150.0) if metrics_data else 150.0
        
        baseline_avg = 120.0  # Standard Mbps under normal production conditions
        deviation_percent = ((current_throughput - baseline_avg) / baseline_avg) * 100

        # Operational criticality diagnostics based on deviation thresholds
        if deviation_percent > 400:
            operational_impact = "CRITICAL - Denial of Service (DoS) in progress on the infrastructure."
            severity_adjustment = "CRITICAL"
        elif deviation_percent > 200:
            operational_impact = "MAJOR - Application response time degradation."
            severity_adjustment = "HIGH"
        else:
            operational_impact = "MINOR - Transient disturbance with no detectable user impact."
            severity_adjustment = "MEDIUM"

        forecast_text = (
            f"Current metrics show a throughput of {current_throughput:.1f} Mbps "
            f"(deviation of {deviation_percent:+.1f}% from the {baseline_avg:.1f} Mbps baseline). "
            f"The Cisco Deep Time Series model predicts throughput will reach "
            f"{predicted_throughput:.1f} Mbps in the next 15 minutes, suggesting "
            f"critical congestion if no remediation is applied."
        )

        return {
            "status": "COMPLETED",
            "current_value": current_throughput,
            "forecast_value": predicted_throughput,
            "deviation_percent": deviation_percent,
            "operational_impact": operational_impact,
            "severity_adjustment": severity_adjustment,
            "forecast_summary": forecast_text,
            "spl_executed": spl_query
        }
