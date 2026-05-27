"""Quota Circuit Breaker for Aegis-Mind multi-agent pipeline.

Provides dynamic API quota management and circuit-breaking capabilities
to prevent API fatigue and cost overruns during automated investigations.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.CircuitBreaker")


class QuotaCircuitBreaker:
    """Dynamic API quota manager and circuit breaker for Aegis-Mind.

    Prevents API fatigue and runaway costs by:
    1. Tracking the number of calls made to the Splunk MCP server during an investigation.
    2. Tripping the circuit when the maximum per-incident call quota is reached.
    3. Preemptively blocking expensive pipeline stages when the initial triage
       determines the alert is an obvious false positive (high confidence score).
    """

    def __init__(self, max_requests: int = 50, fp_confidence_threshold: float = 0.85):
        """Initialize the circuit breaker.

        Args:
            max_requests: Maximum number of allowed Splunk MCP requests per incident.
            fp_confidence_threshold: Minimum confidence score (0.0–1.0) to trip
                the circuit on a false-positive triage result.
        """
        self.max_requests = max_requests
        self.fp_confidence_threshold = fp_confidence_threshold
        self.request_count = 0
        self.tripped = False
        self.trip_reason = ""

    def increment_and_check(self) -> bool:
        """Increment the request counter and check whether the quota is exceeded.

        Returns:
            True if the circuit is open (tripped/blocked), False otherwise.
        """
        if self.tripped:
            return True

        self.request_count += 1
        if self.request_count > self.max_requests:
            self.tripped = True
            self.trip_reason = f"Maximum Splunk MCP request quota reached ({self.max_requests})."
            logger.warning(f"[CIRCUIT BREAKER] {self.trip_reason}")
            return True

        return False

    def evaluate_triage(self, is_false_positive: bool, confidence_score: float) -> bool:
        """Evaluate the initial triage report and trip the circuit for false positives.

        If the triage agent classifies the alert as a false positive with
        sufficiently high confidence, the circuit is tripped to save quota.

        Args:
            is_false_positive: True if the triage considers the alert a false positive.
            confidence_score: Confidence score associated with the assessment (0.0–1.0).

        Returns:
            True if the circuit is open (tripped to save quota), False otherwise.
        """
        if self.tripped:
            return True

        if is_false_positive and confidence_score >= self.fp_confidence_threshold:
            self.tripped = True
            self.trip_reason = (
                f"False positive identified with {confidence_score * 100:.1f}% confidence "
                f"(trip threshold: {self.fp_confidence_threshold * 100:.1f}%). "
                f"Multi-agent pipeline halted to preserve quotas."
            )
            logger.info(f"[CIRCUIT BREAKER] {self.trip_reason}")
            return True

        return False

    def reset(self):
        """Reset the request counter and circuit breaker state."""
        self.request_count = 0
        self.tripped = False
        self.trip_reason = ""
        logger.info("[CIRCUIT BREAKER] Reset.")
