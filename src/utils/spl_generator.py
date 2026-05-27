"""Splunk AI Assistant (SAIA) SPL query generator for Aegis-Mind.

Translates natural-language investigation requests into valid SPL
(Splunk Processing Language) queries using pattern-matching rules,
and validates query syntax before execution.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.SplunkAIAssistant")


class SplunkAIAssistant:
    """Interface for interacting with the Splunk AI Assistant (SAIA).

    Translates natural-language requests into SPL queries that follow
    Splunk best practices, and validates query syntax before execution.
    """

    @staticmethod
    def generate_spl(natural_language_request: str, index: str = "main") -> str:
        """Translate a natural-language request into an SPL query via SAIA.

        Args:
            natural_language_request: Log search request in natural language.
            index: Target Splunk index.

        Returns:
            Final SPL query string ready for execution.
        """
        request_lower = natural_language_request.lower()
        spl_query = ""

        # Bilingual rule dictionary (French / English) for specific threat scenarios
        if any(term in request_lower for term in ["brute force", "failed login", "authentification", "connexion", "login"]):
            spl_query = (
                f'search index={index} sourcetype="auth_logs" action="failed"\n'
                f'| stats count by src_ip, user\n'
                f'| where count > 10\n'
                f'| sort - count'
            )
        elif any(term in request_lower for term in ["credential", "iam", "exfiltration", "fuite", "clés", "role"]):
            spl_query = (
                f'search index={index} sourcetype="aws:cloudtrail" eventName="AssumeRole" errorCode="AccessDenied"\n'
                f'| stats count values(arn) by userIdentity.sessionContext.sessionIssuer.arn, src_ip\n'
                f'| rename userIdentity.sessionContext.sessionIssuer.arn as RoleArn'
            )
        elif any(term in request_lower for term in ["tampering", "database", "sql", "base de données", "sabotage", "injection"]):
            spl_query = (
                f'search index={index} sourcetype="db_logs" (statement="DROP*" OR statement="ALTER*" OR statement="DELETE*")\n'
                f'| stats count values(statement) by user, src_ip'
            )
        elif any(term in request_lower for term in ["anomalie", "performance", "throughput", "débit", "bande passante", "prédiction"]):
            spl_query = (
                f'search index={index} sourcetype="kube:metrics" metric_name="network_throughput"\n'
                f'| timechart span=1m avg(value) as network_mbps\n'
                f'| predict network_mbps as forecast algorithm="CiscoDeepTimeSeries" future_timespan=15'
            )
        elif any(term in request_lower for term in ["toolkit", "aitk", "generative", "ai prompt"]):
            spl_query = (
                f'search index={index} log_level=ERROR\n'
                f'| head 5\n'
                f'| ai prompt="Analyse cette erreur système Splunk et propose une correction : {{_raw}}" model="gpt-oss-120b"'
            )
        else:
            # Generic fallback SPL query
            spl_query = (
                f'search index={index} "{natural_language_request}"\n'
                f'| head 100\n'
                f'| stats count by sourcetype, host'
            )

        # Append the Aegis-Mind enrichment command unless already present
        # or the query ends with a time-series prediction command
        if "aegismind" not in spl_query.lower() and "predict" not in spl_query.lower():
            spl_query = spl_query.strip() + "\n| aegismind"

        logger.info(f"[SAIA] Translation successful.\nRequest: '{natural_language_request}'\nGenerated SPL:\n{spl_query}")
        return spl_query

    @staticmethod
    def validate_spl(spl_query: str) -> dict:
        """Validate the syntax of an SPL query (App Inspect / SAIA engine).

        Args:
            spl_query: SPL query string to validate.

        Returns:
            Validation result dict: ``{"valid": bool, "error": str | None}``.
        """
        # Basic check: query must start with 'search' or a pipe '|'
        if not spl_query.strip().startswith("search") and not spl_query.strip().startswith("|"):
            return {"valid": False, "error": "An SPL query must start with the 'search' keyword or a pipe '|'."}

        # Security check: block dangerous data-modification commands
        dangerous_commands = ["| delete", "| outputcsv", "| outputlookup"]
        for cmd in dangerous_commands:
            if cmd in spl_query.lower():
                return {"valid": False, "error": f"The data-modification command '{cmd}' is forbidden for security reasons."}

        return {"valid": True, "error": None}
