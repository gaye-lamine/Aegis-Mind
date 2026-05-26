#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import json
import logging
import time

# Injecter la racine bin dans sys.path pour résoudre nos importations locales de manière propre
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_client import SplunkMCPClient
from utils.circuit_breaker import QuotaCircuitBreaker
from agents.triage_agent import TriageAgent
from agents.time_series_agent import TimeSeriesAgent
from agents.remediation_agent import RemediationAgent

# Configurer le logging pour Splunkd (les sorties de script custom d'alertes vont dans $SPLUNK_HOME/var/log/splunk/splunkd.log)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AegisMind.CustomAlertAction")

async def run_agentic_triage(alert_name: str, payload: dict) -> dict:
    """Orchestre la cellule multi-agent autonome d'Aegis-Mind sur l'alerte Splunk."""
    logger.info(f"Démarrage de la cellule de crise Aegis-Mind pour l'alerte : {alert_name}")
    
    # 1. Initialisation des briques MCP, Sécurité et Agents
    # Remarque : Les informations de connexion (jeton, etc.) sont chargées automatiquement par le client via le fichier .env
    mcp_client = SplunkMCPClient()
    mcp_client.connect()
    
    cb = QuotaCircuitBreaker(max_requests=5, fp_confidence_threshold=0.85)
    
    t_agent = TriageAgent(mcp_client)
    ts_agent = TimeSeriesAgent(mcp_client)
    rem_agent = RemediationAgent(mcp_client)

    # 2. Triage Forensic Initial
    triage_res = await t_agent.run_investigation(alert_name, payload, cb)
    logger.info(f"Triage cyber complété. Faux Positif : {triage_res.get('is_false_positive')}")

    if cb.tripped:
        logger.warning(f"Pipeline coupe-circuit déclenché : {cb.trip_reason}")
        return {
            "status": "SUPPRESSED",
            "reason": cb.trip_reason,
            "triage": triage_res
        }

    # 3. Analyse Temporelle d'Impact
    ts_res = await ts_agent.analyze_impact(triage_res, cb)
    logger.info(f"Analyse temporelle complétée. Gravité : {ts_res.get('severity_adjustment')}")

    # 4. Auto-Remédiation & Playbook
    rem_res = await rem_agent.execute_remediation(triage_res, ts_res, cb)
    logger.info(f"Playbook de remédiation appliqué avec succès. Statut final : {rem_res.get('status')}")

    # 5. Enregistrer le rapport post-mortem dans le dossier var/run/splunk pour que Splunk y accède
    splunk_run_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_file = os.path.join(splunk_run_dir, "aegis_post_mortem.md")
    
    # Écriture du rapport local
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Aegis-Mind Incident Report\n\nIncident résolu avec succès.\nAction : {rem_res.get('mitigation_action')}\n")
        
    logger.info(f"Rapport d'incident enregistré dans {report_file}")
    
    return {
        "status": "SUCCESS",
        "triage": triage_res,
        "time_series": ts_res,
        "remediation": rem_res
    }

def main():
    """Point d'entrée standard exécuté par Splunkd lors d'un déclenchement d'alerte."""
    logger.info("Aegis-Mind Alert Action démarrée par Splunkd.")
    
    # Splunk passe le payload JSON de l'incident contenant les évènements correspondants via stdin
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        try:
            # Lire le payload depuis stdin
            payload_str = sys.stdin.read()
            if not payload_str:
                logger.error("Aucun payload reçu de Splunkd via stdin.")
                sys.exit(1)

            payload = json.loads(payload_str)
            
            # Récupérer les métadonnées de l'alerte
            alert_name = payload.get("search_name", "Kubernetes Suspicious Event")
            result_events = payload.get("result", {}) # L'évènement qui a déclenché l'alerte
            
            # Exécuter l'investigation agentique de manière asynchrone
            loop = asyncio.get_event_loop()
            res = loop.run_until_complete(run_agentic_triage(alert_name, result_events))
            
            # Splunkd attend 0 en sortie pour confirmer le bon déclenchement de l'action
            print(json.dumps({"status": "SUCCESS", "details": res}))
            sys.exit(0)

        except Exception as e:
            logger.critical(f"Erreur fatale lors de l'exécution de l'alerte Aegis-Mind : {e}", exc_info=True)
            sys.exit(2)
    else:
        logger.error("Usage invalide. Doit être appelé avec '--execute'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
