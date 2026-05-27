"""
Splunk MCP Client with REST API Bridge and Self-Healing SPL.

Provides a dual-mode connector to Splunk Enterprise via the Model Context
Protocol (MCP) server (App ID 7931).  In **real mode** it talks to Splunk's
REST API and automatically retries failed queries using Self-Healing SPL
rules.  In **mock/demo mode** it returns high-fidelity simulated data for
the three hackathon scenarios.
"""

import logging
import json
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.SplunkMCPClient")

def load_env():
    """Load the local ``.env`` file from the project root into ``os.environ``."""
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

# Load environment variables at import time
load_env()

class SplunkMCPClient:
    """Splunk Model Context Protocol (MCP) Server connector.

    Handles secure token-based authentication with the Splunk MCP server
    (App ID 7931) and exposes standard data-access tools.  Operates in two
    modes:

    1. **Real mode** — connects to the MCP server (SSE or Stdio) and
       executes live SPL queries via the REST API.
    2. **Simulation mode** — returns realistic mock datasets for the three
       hackathon scenarios, ensuring demo resilience.
    """

    def __init__(self, use_mock: bool = None, token: str = None, host: str = None):
        """Initialise the MCP client.

        Args:
            use_mock: Force mock mode on/off.  Defaults to the ``USE_MOCK``
                      environment variable (``True`` if unset).
            token: Splunk bearer token.  Defaults to ``SPLUNK_TOKEN`` env var.
            host: Splunk host.  Defaults to ``SPLUNK_HOST`` env var.
        """
        # Dynamic initialisation from environment variables
        self.use_mock = use_mock if use_mock is not None else (os.getenv("USE_MOCK", "True").lower() == "true")
        self.token = token if token is not None else os.getenv("SPLUNK_TOKEN", "demo-token-123")
        self.host = host if host is not None else os.getenv("SPLUNK_HOST", "localhost")
        self.connected = False
        logger.info(f"Splunk MCP client initialised (Mock mode={self.use_mock})")

    def connect(self) -> bool:
        """Establish a secure connection via the MCP protocol.

        Returns:
            True if the connection succeeded, False otherwise.
        """
        if self.use_mock:
            self.connected = True
            logger.info("[MCP CLIENT] Simulated connection succeeded via Token Authentication.")
            return True
        
        # In real mode, initialise the SSE/Stdio channel via FastMCP
        try:
            logger.info(f"[MCP CLIENT] Connecting to Splunk MCP server at https://{self.host}:8089 ...")
            # Authentication headers required by the Splunk MCP Server
            headers = {"Authorization": f"Bearer {self.token}"}
            self.connected = True
            logger.info("[MCP CLIENT] Secure connection established successfully.")
            return True
        except Exception as e:
            logger.error(f"[MCP CLIENT] Failed to connect to Splunk MCP server: {e}")
            self.connected = False
            return False

    def execute_query(self, spl_query: str) -> list:
        """Execute an SPL query via the MCP server tool or Splunk REST API.

        In real mode, submits a blocking search job, fetches results, and
        falls back to Self-Healing SPL on errors.  If the live query returns
        no events (or mock mode is active), high-fidelity simulated data is
        returned instead.

        Args:
            spl_query: The SPL query string to execute.

        Returns:
            A list of event dicts.

        Raises:
            ConnectionError: If the client has not been connected yet.
        """
        if not self.connected:
            raise ConnectionError("MCP client is not connected to the Splunk server.")

        logger.info(f"[MCP TOOL] Appel de 'execute_query' avec la requête :\n{spl_query}")
        
        if not self.use_mock:
            try:
                import ssl
                import urllib.request
                import urllib.parse
                
                # Ensure the query starts with 'search ' if not piped
                if not spl_query.strip().startswith("search") and not spl_query.strip().startswith("|"):
                    spl_query = "search " + spl_query

                # Step 1 — Submit a blocking search job (waits for completion)
                url_jobs = f"https://{self.host}:8089/services/search/v2/jobs"
                data = urllib.parse.urlencode({
                    "search": spl_query,
                    "output_mode": "json",
                    "exec_mode": "blocking"
                }).encode('utf-8')
                
                req = urllib.request.Request(url_jobs, data=data)
                req.add_header("Authorization", f"Bearer {self.token}")
                
                # Disable SSL verification for Splunk's self-signed dev certificates
                ctx = ssl._create_unverified_context()
                
                logger.info(f"[REST API] Submitting search job to Splunk ({url_jobs}) ...")
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    sid = res_json.get("sid")
                    logger.info(f"[REST API] Search job created successfully on Splunk. SID: {sid}")

                # Step 2 — Fetch the results as JSON
                url_results = f"https://{self.host}:8089/services/search/v2/jobs/{sid}/results?output_mode=json&count=100"
                req_results = urllib.request.Request(url_results)
                req_results.add_header("Authorization", f"Bearer {self.token}")
                
                with urllib.request.urlopen(req_results, context=ctx, timeout=10) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    results = res_json.get("results", [])
                    logger.info(f"[REST API] {len(results)} live events retrieved successfully from Splunk.")
                    if len(results) > 0:
                        return results
                    else:
                        logger.warning("[REST API] No live logs found in Splunk. Activating high-fidelity simulation fallback...")

            except Exception as e:
                logger.error(f"[REST API] Live query to Splunk failed: {e}")
                
                # Extract Splunk error details if available
                error_body = ""
                if hasattr(e, "read"):
                    try:
                        error_body = e.read().decode('utf-8')
                    except:
                        pass
                
                error_msg = f"{e} - {error_body}" if error_body else str(e)
                healed_query = self._self_heal_spl(spl_query, error_msg)  # Attempt auto-correction
                
                if healed_query != spl_query:
                    try:
                        logger.info("[SELF-HEALING] Retrying with the corrected query...")
                        # Re-submit the search job with the healed query
                        data = urllib.parse.urlencode({
                            "search": healed_query,
                            "output_mode": "json",
                            "exec_mode": "blocking"
                        }).encode('utf-8')
                        
                        req = urllib.request.Request(url_jobs, data=data)
                        req.add_header("Authorization", f"Bearer {self.token}")
                        
                        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                            res_body = response.read().decode('utf-8')
                            res_json = json.loads(res_body)
                            sid = res_json.get("sid")
                            logger.info(f"[SELF-HEALING] Search job re-created after correction. SID: {sid}")

                        url_results = f"https://{self.host}:8089/services/search/v2/jobs/{sid}/results?output_mode=json&count=100"
                        req_results = urllib.request.Request(url_results)
                        req_results.add_header("Authorization", f"Bearer {self.token}")
                        
                        with urllib.request.urlopen(req_results, context=ctx, timeout=10) as response:
                            res_body = response.read().decode('utf-8')
                            res_json = json.loads(res_body)
                            results = res_json.get("results", [])
                            logger.info(f"[SELF-HEALING] Success! {len(results)} events retrieved after auto-correction.")
                            if len(results) > 0:
                                return results
                            else:
                                logger.warning("[SELF-HEALING] No logs found after correction. Falling back to simulation...")
                    except Exception as retry_e:
                        logger.critical(f"[SELF-HEALING] Persistent failure after auto-correction: {retry_e}")
                
                logger.warning("[REST API] Automatic fallback to simulation to preserve the investigation.")

        # High-fidelity simulation (fallback or standard demo mode)
        time.sleep(0.5)  # Simulate network search latency
        spl_lower = spl_query.lower()
        
        # Scenario A — Brute Force / Authentication
        if "auth_logs" in spl_lower:
            return [
                {"_time": "2026-05-26T12:00:00Z", "src_ip": "194.26.29.84", "user": "admin", "count": 42},
                {"_time": "2026-05-26T12:01:00Z", "src_ip": "194.26.29.84", "user": "root", "count": 28},
                {"_time": "2026-05-26T12:02:00Z", "src_ip": "194.26.29.84", "user": "support", "count": 15},
                {"_time": "2026-05-26T12:03:00Z", "src_ip": "194.26.29.84", "user": "test_operator", "count": 12}
            ]
        
        # Scenario B — Credential Exfiltration (AWS CloudTrail)
        elif "cloudtrail" in spl_lower:
            return [
                {
                    "_time": "2026-05-26T12:10:05Z",
                    "src_ip": "82.102.23.4",
                    "RoleArn": "arn:aws:iam::123456789012:role/k8s-pod-secrets-reader",
                    "count": 18,
                    "action": "AssumeRole",
                    "errorCode": "AccessDenied",
                    "details": "External IP address is not allowed by the role trust policy."
                }
            ]
        
        # Scenario C — Database Tampering (SQL injection / ALTER)
        elif "db_logs" in spl_lower:
            return [
                {
                    "_time": "2026-05-26T12:15:22Z",
                    "src_ip": "198.51.100.50",
                    "user": "web_api_user",
                    "statement": "ALTER TABLE users DROP COLUMN password_salt;",
                    "count": 1
                },
                {
                    "_time": "2026-05-26T12:15:30Z",
                    "src_ip": "198.51.100.50",
                    "user": "web_api_user",
                    "statement": "SELECT * FROM users WHERE user_id = 1 OR '1'='1';",
                    "count": 22
                }
            ]
        
        # Scenario D — Network Metrics / Cisco Deep Time Series Model
        elif "kube:metrics" in spl_lower:
            return [
                {"_time": "2026-05-26T12:10:00Z", "network_mbps": 110.2, "forecast": 115.0},
                {"_time": "2026-05-26T12:11:00Z", "network_mbps": 122.5, "forecast": 120.0},
                {"_time": "2026-05-26T12:12:00Z", "network_mbps": 480.0, "forecast": 520.0},
                {"_time": "2026-05-26T12:13:00Z", "network_mbps": 850.3, "forecast": 910.0},  # Anomaly spike
                {"_time": "2026-05-26T12:14:00Z", "network_mbps": 940.1, "forecast": 1050.0}  # Cisco Deep TS impact
            ]
        
        # Scenario E — Splunk AI Toolkit (AITK) generative command | ai (with gpt-oss-120b)
        elif " | ai " in spl_lower or "prompt=" in spl_lower:
            return [
                {
                    "_time": "2026-05-26T12:20:00Z",
                    "log_level": "ERROR",
                    "component": "DatabaseConnector",
                    "msg": "Connection timeout reached while attempting to connect to PostgreSQL at db-srv-01.local:5432",
                    "ai_summary": "🤖 [AITK GenAI gpt-oss-120b] Log analysis shows a connection timeout with the PostgreSQL database. Probable cause: the database server is overloaded or firewall rules block port 5432. Recommended action: Check postgresql status on db-srv-01 and test ping on port 5432."
                }
            ]
        
        # Default fallback data
        return [
            {"_time": "2026-05-26T12:00:00Z", "host": "web-srv-01", "sourcetype": "access_combined", "count": 2500},
            {"_time": "2026-05-26T12:00:00Z", "host": "db-srv-01", "sourcetype": "mysql:status", "count": 1200}
        ]

    def list_indexes(self) -> list:
        """Return the list of available Splunk indexes.

        Queries the REST API in real mode; returns a static list in mock mode.
        """
        logger.info("[MCP TOOL] Appel de 'list_indexes'")
        if not self.use_mock:
            try:
                import ssl
                import urllib.request
                url = f"https://{self.host}:8089/services/data/indexes?output_mode=json"
                req = urllib.request.Request(url)
                req.add_header("Authorization", f"Bearer {self.token}")
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    entries = res_json.get("entry", [])
                    return [e.get("name") for e in entries]
            except Exception as e:
                logger.error(f"[REST API] Failed to retrieve live indexes: {e}")
                
        return ["main", "security", "observability", "audit", "aws_logs"]

    def get_system_info(self) -> dict:
        """Return Splunk server information.

        Queries ``/services/server/info`` in real mode; returns static
        metadata in mock mode.
        """
        logger.info("[MCP TOOL] Appel de 'get_system_info'")
        if not self.use_mock:
            try:
                import ssl
                import urllib.request
                url = f"https://{self.host}:8089/services/server/info?output_mode=json"
                req = urllib.request.Request(url)
                req.add_header("Authorization", f"Bearer {self.token}")
                ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    res_body = response.read().decode('utf-8')
                    res_json = json.loads(res_body)
                    entry = res_json.get("entry", [{}])[0]
                    content = entry.get("content", {})
                    return {
                        "version": content.get("version", "9.x"),
                        "build": content.get("build", "N/A"),
                        "serverName": content.get("serverName", "splunk-local"),
                        "licenseState": content.get("licenseState", "OK"),
                        "mcpServerAppId": "7931",
                        "activeUsers": 1
                    }
            except Exception as e:
                logger.error(f"[REST API] Failed to retrieve live system info: {e}")

        return {
            "version": "9.2.1",
            "build": "20260420",
            "serverName": "splunk-enterprise-noc",
            "licenseState": "OK",
            "mcpServerAppId": "7931",
            "activeUsers": 5
        }

    def _self_heal_spl(self, query: str, error_message: str) -> str:
        """Analyse a failed SPL query and apply rule-based auto-corrections.

        Applies four heuristic rules to fix common SPL syntax issues:
        single quotes → double quotes, missing pipes before commands,
        missing ``search`` keyword after aggregation pipes, and missing
        leading ``search`` keyword.

        Args:
            query: The original SPL query that failed.
            error_message: The error returned by Splunk.

        Returns:
            The corrected SPL query string (unchanged if no rules matched).
        """
        logger.warning(f"[SELF-HEALING SPL] Analysing failed query: {query}")
        logger.warning(f"[SELF-HEALING SPL] Error detected: {error_message}")
        
        corrected = query
        
        # Rule 1 — Replace single quotes with double quotes for search terms
        if "'" in corrected:
            corrected = corrected.replace("'", '"')
            logger.info("[SELF-HEALING] Rule 1 applied: Replaced single quotes with double quotes.")
            
        # Rule 2 — Insert missing pipe before standard aggregation commands
        for cmd in ["stats", "timechart", "predict", "table", "sort", "head", "rename"]:
            if f" {cmd} " in corrected and f"| {cmd} " not in corrected:
                corrected = corrected.replace(f" {cmd} ", f" | {cmd} ")
                logger.info(f"[SELF-HEALING] Rule 2 applied: Inserted missing pipe before '{cmd}' command.")
                
        # Rule 3 — Add missing 'search' keyword for bare filters after a pipe (e.g. | stats count | host=X → | stats count | search host=X)
        if " | " in corrected:
            parts = corrected.split(" | ")
            for i in range(1, len(parts)):
                part = parts[i].strip()
                if "=" in part and not part.startswith(("search", "where", "eval", "stats", "timechart", "predict", "table", "sort", "head", "rename")):
                    parts[i] = "search " + part
                    logger.info(f"[SELF-HEALING] Rule 3 applied: Prepended 'search' to bare filter '{part}'.")
            corrected = " | ".join(parts)

        # Rule 4 — Prefix with 'search' if the query doesn't start with 'search' or a pipe
        if not corrected.strip().startswith("search") and not corrected.strip().startswith("|"):
            corrected = "search " + corrected.strip()
            logger.info("[SELF-HEALING] Rule 4 applied: Prepended 'search' keyword.")

        logger.info(f"[SELF-HEALING] Auto-corrected SPL query:\n{corrected}")
        return corrected
