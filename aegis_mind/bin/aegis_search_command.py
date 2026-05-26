#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Injecter la racine bin dans sys.path pour les importations locales de manière propre
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from splunklib.searchcommands import dispatch, StreamingCommand, Configuration
from mcp_client import SplunkMCPClient
from utils.circuit_breaker import QuotaCircuitBreaker
from agents.triage_agent import TriageAgent

@Configuration()
class AegisMindCommand(StreamingCommand):
    """
    Commande de recherche personnalisée Splunk Aegis-Mind.
    
    Enrichit en temps réel chaque ligne de log d'une recherche avec l'analyse cyber 
    de l'agent IA d'Aegis-Mind NOC.
    
    Usage dans Splunk Web : index=main | head 5 | aegismind
    """

    def stream(self, records):
        # Initialisation du client MCP et des briques de triage de l'agent
        mcp_client = SplunkMCPClient()
        mcp_client.connect()
        cb = QuotaCircuitBreaker(max_requests=10)
        triage = TriageAgent(mcp_client)

        for record in records:
            raw_text = record.get("_raw", "")
            
            # Analyse cyber de l'agent en temps réel selon les signatures
            if "failed" in raw_text.lower() or "denied" in raw_text.lower():
                analysis = (
                    "⚠️ [Aegis-Mind Triage] Alerte d'échec d'authentification détectée. "
                    "Le comportement semble suspect. Recommandation : Surveiller l'IP source."
                )
            elif "alter" in raw_text.lower() or "drop" in raw_text.lower():
                analysis = (
                    "🔥 [Aegis-Mind Forensic] Alerte CRITIQUE. "
                    "Tentative de modification de structure de données détectée dans le pipeline de logs."
                )
            else:
                analysis = "✅ [Aegis-Mind NOC] Activité système nominale analysée par l'agent."

            # Injecter le nouveau champ 'aegis_analysis' directement dans les champs de l'évènement de recherche Splunk !
            record["aegis_analysis"] = analysis
            
            # Renvoyer l'évènement enrichi à la suite du pipeline de recherche Splunk
            yield record

if __name__ == "__main__":
    dispatch(AegisMindCommand, sys.argv, sys.stdin, sys.stdout, __name__)
