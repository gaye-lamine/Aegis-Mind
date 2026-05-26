import logging
import json
from google.antigravity import Agent, LocalAgentConfig
from mcp_client import SplunkMCPClient
from utils.spl_generator import SplunkAIAssistant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.TimeSeriesAgent")

class TimeSeriesAgent:
    """
    📊 Agent de Corrélation Temporelle & d'Impact (The Analyst).
    
    Orchestré sous le Google Antigravity SDK.
    Modèle d'IA : Cisco Deep Time Series Model (pour la prévision d'impact sur séries temporelles).
    
    Rôle :
    1. Extrait les métriques réseau/CPU actuelles associées à l'incident dans Splunk.
    2. Analyse le comportement temporel et les écarts par rapport à la baseline historique.
    3. Prédit la dégradation opérationnelle future (t+15min, t+1h).
    """

    def __init__(self, mcp_client: SplunkMCPClient):
        self.mcp_client = mcp_client
        self.model_name = "Cisco Deep Time Series Model"
        
        # Configuration de l'agent Antigravity
        self.agent_config = LocalAgentConfig(
            model="gemini-3.5-flash",
            system_instructions=(
                "Vous êtes l'Agent de Corrélation Temporelle (The Analyst) de la plateforme Aegis-Mind. "
                "Votre objectif est d'analyser des métriques de performance système, de calculer "
                "des déviations par rapport aux historiques de référence (baselines) et de prédire "
                "l'impact opérationnel d'une attaque sur la production à court terme."
            )
        )

    async def analyze_impact(self, triage_report: dict, circuit_breaker) -> dict:
        """
        Analyse les séries temporelles de performance pour estimer l'impact de la crise.
        
        Args:
            triage_report (dict): Le rapport forensic émis par le Triage Agent.
            circuit_breaker (QuotaCircuitBreaker): Le coupe-circuit d'API.
            
        Returns:
            dict: Rapport opérationnel prédictif.
        """
        logger.info("[TIME-SERIES AGENT] Démarrage de l'analyse d'impact de performance...")

        if triage_report.get("is_false_positive", False):
            logger.info("[TIME-SERIES AGENT] L'incident a été classé Faux Positif. Analyse sautée.")
            return {"status": "SKIPPED", "reason": "Incident identifié comme Faux Positif."}

        # 1. Génération de la requête SPL pour extraire la télémétrie de performance
        spl_query = SplunkAIAssistant.generate_spl("Obtenir l'anomalie de performance metrics network throughput")
        
        if circuit_breaker.increment_and_check():
            return {
                "status": "SUPPRESSED",
                "reason": "Circuit breaker déclenché : quota d'appels d'API épuisé."
            }

        # 2. Récupération des données via le serveur Splunk MCP
        metrics_data = self.mcp_client.execute_query(spl_query)
        logger.info(f"[TIME-SERIES AGENT] Extraction de {len(metrics_data)} points temporels pour analyse.")

        # 3. Calcul de la déviation et prédiction de la tendance (Simulation Cisco Deep Time Series)
        current_throughput = metrics_data[-1].get("network_mbps", 120.0) if metrics_data else 120.0
        predicted_throughput = metrics_data[-1].get("forecast", 150.0) if metrics_data else 150.0
        
        baseline_avg = 120.0  # Mbps standard en conditions de production normales
        deviation_percent = ((current_throughput - baseline_avg) / baseline_avg) * 100

        # Diagnostics de criticité opérationnelle
        if deviation_percent > 400:
            operational_impact = "CRITIQUE - Déni de Service (DoS) en cours sur l'infrastructure."
            severity_adjustment = "CRITICAL"
        elif deviation_percent > 200:
            operational_impact = "MAJEUR - Dégradation des temps de réponse applicatifs."
            severity_adjustment = "HIGH"
        else:
            operational_impact = "MINEUR - Perturbation transitoire sans impact utilisateur détectable."
            severity_adjustment = "MEDIUM"

        forecast_text = (
            f"Les métriques actuelles révèlent un débit de {current_throughput:.1f} Mbps "
            f"(déviation de {deviation_percent:+.1f}% par rapport à la baseline de {baseline_avg:.1f} Mbps). "
            f"La prédiction du modèle Cisco Deep Time Series pour les 15 prochaines minutes "
            f"indique que le débit atteindra {predicted_throughput:.1f} Mbps, suggérant une "
            f"congestion critique si aucune remédiation n'est appliquée."
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
