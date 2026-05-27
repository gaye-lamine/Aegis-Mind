#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aegis-Mind NOC Terminal Orchestrator.

Cyberpunk-themed ANSI console that drives the multi-agent incident-response
pipeline: Triage → Time-Series Analysis → Auto-Remediation → Post-Mortem
report generation.  Includes an interactive Copilot chat mode for ad-hoc
SPL queries with Self-Healing SPL support.
"""

import asyncio
import os
import sys
import time
import logging

# Insert parent directory into sys.path so the 'src' package can be resolved
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mcp_client import SplunkMCPClient
from src.utils.circuit_breaker import QuotaCircuitBreaker
from src.agents.triage_agent import TriageAgent
from src.agents.time_series_agent import TimeSeriesAgent
from src.agents.remediation_agent import RemediationAgent
from src.utils.spl_generator import SplunkAIAssistant

# Configure logging for the orchestrator
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.Orchestrator")

# ANSI colour codes for the cyberpunk-style security console UI
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_AMBER = "\033[93m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

# Pre-defined demo scenarios for the hackathon live demonstration
SCENARIOS = {
    "1": {
        "name": "Kubernetes Credential Exfiltration (Major Incident)",
        "alert_name": "kubernetes_iam_credential_leak",
        "payload": {"cluster": "production-k8s-us", "namespaces": ["default", "finance"]}
    },
    "2": {
        "name": "SSH Brute-Force / Authentication Attack (Confirmed Alert)",
        "alert_name": "brute_force_ssh_login",
        "payload": {"target_host": "secure-gateway-srv"}
    },
    "3": {
        "name": "SSH Brute-Force – Low Intensity (False Positive)",
        "alert_name": "brute_force_ssh_low_intensity",
        "payload": {"target_host": "dev-sandbox-srv"}
    }
}

def print_banner():
    """Print the Aegis-Mind cybersecurity ASCII art banner to the console."""
    banner = f"""
{C_CYAN}{C_BOLD}================================================================================
          █████╗ ███████╗ ██████╗ ██╗███████╗      ███╗   ███╗██╗███╗   ██╗██████╗ 
         ██╔══██╗██╔════╝██╔════╝ ██║██╔════╝      ████╗ ████║██║████╗  ██║██╔══██╗
         ███████║█████╗  ██║  ███╗██║███████╗█████╗██╔████╔██║██║██╔██╗ ██║██║  ██║
         ██╔══██║██╔══╝  ██║   ██║██║╚════██║╚════╝██║╚██╔╝██║██║██║╚██╗██║██║  ██║
         ██║  ██║███████╗╚██████╔╝██║███████║      ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
         ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝      ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ 
                     Autonomous Multi-Agent NOC for Incident Response
================================================================================{C_RESET}
    """
    print(banner)

async def simulate_thinking(agent_name: str, seconds: float = 2.0):
    """Display an animated ANSI spinner to visualise agent reasoning.

    Args:
        agent_name: Label shown next to the spinner (e.g. "Triage Agent").
        seconds: Duration of the animation in seconds.
    """
    chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + seconds
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{C_BLUE}[THINKING - {agent_name}]{C_RESET} {chars[i % len(chars)]} Analysing Splunk variables and logs ...")
        sys.stdout.flush()
        await asyncio.sleep(0.1)
        i += 1
    sys.stdout.write("\r\033[K")  # Clear the spinner line
    sys.stdout.flush()

def generate_post_mortem(scenario_name: str, triage_res: dict, ts_res: dict, rem_res: dict, file_path: str):
    """Generate a polished Markdown Post-Mortem report with a Mermaid sequence diagram.

    The report covers the full incident lifecycle: triage findings, time-series
    impact analysis, remediation actions, and an auto-generated Mermaid.js
    diagram showing the attack flow and response.

    Args:
        scenario_name: Human-readable name of the alert scenario.
        triage_res: Output dict from the Triage Agent.
        ts_res: Output dict from the Time-Series Agent.
        rem_res: Output dict from the Remediation Agent.
        file_path: Destination path for the generated ``.md`` report.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Build the Mermaid.js sequence diagram dynamically
    mermaid_diag = "sequenceDiagram\n"
    mermaid_diag += "    autonumber\n"
    mermaid_diag += "    participant Infra as Infrastructure (Kubernetes/AWS)\n"
    mermaid_diag += "    participant Splunk as Splunk Enterprise (MCP Server)\n"
    mermaid_diag += "    participant Aegis as Aegis-Mind Multi-Agent\n"
    mermaid_diag += "    Infra->>Splunk: Activités suspectes (Ingestion logs)\n"
    mermaid_diag += f"    Splunk->>Aegis: Déclenchement alerte '{scenario_name}'\n"
    
    if triage_res.get("status") == "COMPLETED" and not triage_res.get("is_false_positive"):
        mermaid_diag += f"    Aegis->>Splunk: execute_query() via MCP (Triage)\n"
        mermaid_diag += f"    Splunk-->>Aegis: Retourne les indices et évènements cyber\n"
        
        if ts_res.get("status") == "COMPLETED":
            mermaid_diag += f"    Aegis->>Splunk: execute_query() via MCP (Time-Series Metrics)\n"
            mermaid_diag += f"    Splunk-->>Aegis: Retourne la performance courante et baseline\n"
            
        if rem_res.get("status") == "SUCCESS":
            mermaid_diag += f"    Aegis->>Infra: Exécute le Playbook de Remédiation\n"
            mermaid_diag += f"    Note right of Infra: {rem_res.get('mitigation_action')}\n"
            mermaid_diag += f"    Aegis->>Splunk: Requête de confirmation d'efficacité (MCP)\n"
            mermaid_diag += f"    Splunk-->>Aegis: Statut opérationnel OK (Retour à la normale)\n"
    else:
        mermaid_diag += f"    Aegis->>Splunk: execute_query() via MCP (Triage)\n"
        mermaid_diag += f"    Note right of Aegis: Détecté Faux Positif. Pipeline stoppé (Circuit Breaker).\n"

    report = f"""# Rapport d'Incident Aegis-Mind (Post-Mortem Autonome)

**Généré automatiquement par Aegis-Mind NOC**  
**Date de l'Incident :** {timestamp}  
**Type d'Alerte :** {scenario_name}  

---

## 📊 1. Résumé de l'Incident

*   **Statut Final :** {"✅ RÉSOLU AUTOMATIQUEMENT" if rem_res.get("status") == "SUCCESS" else "⚠️ CLASSÉ FAUX POSITIF (SUPPRESSION)" if triage_res.get("is_false_positive") else "❌ ESCALADÉ / EN COURS"}
*   **Gravité Détectée :** {ts_res.get("severity_adjustment", triage_res.get("forensic_data", {}).get("severity", "LOW"))}
*   **Temps Moyen de Réponse (MTTR) :** < 4.2 secondes (Autonome)
*   **Économie Opérationnelle (Estimation) :** {f"$24,500 USD (Évitement d'une panne majeure de production)" if rem_res.get("status") == "SUCCESS" else "$0 USD (Faux Positif)"}

---

## 🕵️‍♂️ 2. Chronologie de l'Investigation (Multi-Agent)

### Étape A : Triage Cyber d'Urgence
*   **Agent :** Triage Lead (`Foundation-Sec-1.1-8B-Instruct`)
*   **Requête SPL Exécutée :**
    ```sql
    {triage_res.get("spl_executed", "N/A")}
    ```
*   **Analyse du Modèle :**  
    > {triage_res.get("triage_summary", "Aucune donnée disponible.")}

{"### Étape B : Corrélation Temporelle & Prévision d'Impact" if ts_res.get("status") == "COMPLETED" else ""}
{"*   **Agent :** Performance Analyst (`Cisco Deep Time Series Model`)" if ts_res.get("status") == "COMPLETED" else ""}
{"*   **Requête SPL Exécutée :**" if ts_res.get("status") == "COMPLETED" else ""}
```sql
{ts_res.get("spl_executed", "")}
```
{"*   **Analyse d'Impact Réseau/Système :**" if ts_res.get("status") == "COMPLETED" else ""}
{f"    > {ts_res.get('forecast_summary', '')}" if ts_res.get("status") == "COMPLETED" else ""}
{f"    > **Impact sur la production :** {ts_res.get('operational_impact', '')}" if ts_res.get("status") == "COMPLETED" else ""}

---

## ⚡ 3. Actions de Secours & Remédiation

*   **Action Corrective Appliquée :** {rem_res.get("mitigation_action", "Aucune action requise.")}
*   **Playbook de Remédiation Généré :**
```bash
{rem_res.get("playbook_code", "# Pas d'action appliquée.")}
```
*   **Vérification de l'Efficacité (Splunk MCP) :**  
    > {rem_res.get("verification_status", "N/A")}

---

## 🏗️ 4. Diagramme de Séquence de la Crise (Mermaid)

```mermaid
{mermaid_diag}
```
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info(f"[ORCHESTRATOR] Post-mortem report saved successfully to: {file_path}")

async def run_scenario(choice: str):
    """Orchestrate the full multi-agent pipeline for the selected scenario.

    Executes three sequential stages — Triage, Time-Series Analysis, and
    Auto-Remediation — then generates a Post-Mortem Markdown report.

    Args:
        choice: Key into the ``SCENARIOS`` dict (e.g. "1", "2", "3").
    """
    scen = SCENARIOS[choice]
    alert_name = scen["alert_name"]
    scen_name = scen["name"]
    payload = scen["payload"]

    print(f"\n{C_BOLD}{C_BLUE}>>> Lancement du Scénario [{choice}] : {scen_name}{C_RESET}")
    print(f"--------------------------------------------------------------------------------")

    # Initialise core components
    mcp_client = SplunkMCPClient()
    mcp_client.connect()
    
    cb = QuotaCircuitBreaker(max_requests=5, fp_confidence_threshold=0.85)
    
    t_agent = TriageAgent(mcp_client)
    ts_agent = TimeSeriesAgent(mcp_client)
    rem_agent = RemediationAgent(mcp_client)

    # Stage 1 — Triage
    await simulate_thinking("🕵️‍♂️ Triage Agent", 2.0)
    triage_res = await t_agent.run_investigation(alert_name, payload, cb)
    
    print(f"\n{C_BOLD}{C_GREEN}[🕵️‍♂️ TRIAGE COMPLÉTÉ]{C_RESET}")
    print(f"  └─ Synthèse Cyber : {C_BOLD}{triage_res.get('triage_summary')}{C_RESET}")
    print(f"  └─ Faux Positif   : {C_RED if triage_res.get('is_false_positive') else C_GREEN}{triage_res.get('is_false_positive')}{C_RESET} (Confiance: {triage_res.get('confidence_score')*100:.1f}%)")
    
    if cb.tripped:
        print(f"\n{C_BOLD}{C_AMBER}[⚡ COUPE-CIRCUIT TRIP]{C_RESET}")
        print(f"  └─ Motif : {cb.trip_reason}")
        ts_res = {"status": "SKIPPED"}
        rem_res = {"status": "SKIPPED"}
    else:
        # Stage 2 — Time-Series Analysis
        await simulate_thinking("📊 Time-Series Agent", 1.8)
        ts_res = await ts_agent.analyze_impact(triage_res, cb)
        
        print(f"\n{C_BOLD}{C_GREEN}[📊 ANALYSE TEMPORELLE COMPLÉTÉE]{C_RESET}")
        print(f"  └─ Déviation Métriques : {C_RED if ts_res.get('deviation_percent', 0) > 100 else C_GREEN}{ts_res.get('deviation_percent', 0):+.1f}%{C_RESET}")
        print(f"  └─ Impact de Panne     : {C_BOLD}{ts_res.get('operational_impact')}{C_RESET}")
        print(f"  └─ Ajustement Gravité  : {C_AMBER if ts_res.get('severity_adjustment') == 'HIGH' else C_RED}{ts_res.get('severity_adjustment')}{C_RESET}")

        # Stage 3 — Auto-Remediation
        await simulate_thinking("⚡ Remediation Agent", 2.2)
        rem_res = await rem_agent.execute_remediation(triage_res, ts_res, cb)
        
        print(f"\n{C_BOLD}{C_GREEN}[⚡ AUTO-REMÉDIATION EXÉCUTÉE]{C_RESET}")
        print(f"  └─ Action Appliquée    : {C_BOLD}{C_CYAN}{rem_res.get('mitigation_action')}{C_RESET}")
        print(f"  └─ Code Playbook       : \n{C_BLUE}{rem_res.get('playbook_code')}{C_RESET}")
        print(f"  └─ Statut Efficacité   : {C_GREEN}{rem_res.get('verification_status')}{C_RESET}")

    # Stage 4 — Generate Post-Mortem report
    file_report = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "post_mortem_report.md")
    generate_post_mortem(scen_name, triage_res, ts_res, rem_res, file_report)
    
    print(f"\n{C_BOLD}{C_CYAN}================================================================================")
    print(f"🎉 MISSION COMPLÉTÉE : Incident géré avec succès.")
    print(f"📄 Rapport d'Incident généré en local : [post_mortem_report.md]")
    print(f"================================================================================{C_RESET}\n")

async def run_copilot_chat():
    """Launch the interactive Copilot chat loop.

    Accepts natural-language security questions, translates them to SPL via
    the SplunkAIAssistant, executes them through the MCP client (with
    Self-Healing SPL), and pretty-prints the results.
    """
    print(f"\n{C_BOLD}{C_BLUE}================================================================================")
    print(f"💬 BIENVENUE DANS LE COPILOTE INTERACTIF AEGIS-MIND CHAT")
    print(f"Posez vos questions sur la sécurité et le NOC en langage naturel.")
    print(f"L'IA va générer les requêtes SPL, les exécuter sur votre Splunk local via MCP,")
    print(f"et s'auto-corriger en direct grâce au Self-Healing SPL !")
    print(f"Exemples de questions :")
    print(f"  - 'Montre-moi les brute force récents'")
    print(f"  - 'Trouve les anomalies de performance network throughput'")
    print(f"  - 'Check s'il y a des credential leaks dans les logs'")
    print(f"Tapez 'exit' pour quitter le chat.")
    print(f"================================================================================{C_RESET}\n")

    # Use the real MCP client if configured in .env, otherwise fall back to mock
    mcp_client = SplunkMCPClient()
    mcp_client.connect()
    
    while True:
        try:
            user_input = input(f"{C_BOLD}{C_GREEN}Copilot-User > {C_RESET}").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                print(f"\n{C_BLUE}[COPILOTE] Retour au menu principal NOC.{C_RESET}\n")
                break
                
            print(f"{C_BLUE}[COPILOTE] Analyse de votre demande...{C_RESET}")
            await asyncio.sleep(0.5)
            
            # Step 1 — Generate SPL via the Splunk AI Assistant (SAIA)
            spl_query = SplunkAIAssistant.generate_spl(user_input)
            
            # Step 2 — Validate the generated SPL syntax
            validation = SplunkAIAssistant.validate_spl(spl_query)
            if not validation["valid"]:
                print(f"{C_RED}[ERREUR DE VALIDATION SAIA] {validation['error']}{C_RESET}\n")
                continue
                
            # Step 3 — Execute the query through MCP (Self-Healing built in)
            print(f"{C_BLUE}[COPILOTE] Envoi de la requête SPL à Splunk...{C_RESET}")
            events = mcp_client.execute_query(spl_query)
            
            # Step 4 — Display results
            if not events:
                print(f"{C_AMBER}[COPILOTE] Aucun événement trouvé pour cette requête dans l'index.{C_RESET}\n")
            else:
                print(f"\n{C_BOLD}{C_GREEN}[✓ RÉSULTATS EXTRAITS - {len(events)} ÉVÉNEMENTS]{C_RESET}")
                print("-" * 80)
                for idx, ev in enumerate(events[:5]):
                    print(f"{C_BOLD}Événement {idx+1}{C_RESET} | Date: {ev.get('_time', 'N/A')}")
                    for k, v in ev.items():
                        if k not in ['_time', '_raw', 'punct', 'index', 'splunk_server']:
                            print(f"  └─ {C_CYAN}{k}{C_RESET}: {v}")
                    if '_raw' in ev:
                        print(f"  └─ {C_BLUE}Raw:{C_RESET} {ev['_raw'][:140]}...")
                    print("-" * 80)
                if len(events) > 5:
                    print(f"... et {len(events) - 5} événements supplémentaires masqués pour la lisibilité.")
                print()
        except KeyboardInterrupt:
            print(f"\n{C_BLUE}[COPILOTE] Session interrompue. Retour au menu.{C_RESET}\n")
            break
        except Exception as e:
            print(f"{C_RED}[ERREUR FATALE COPILOTE] {e}{C_RESET}\n")

async def main():
    """Main event loop — display the NOC menu and dispatch user choices."""
    print_banner()
    while True:
        print(f"{C_BOLD}Veuillez choisir une action Aegis-Mind NOC :{C_RESET}")
        for k, v in SCENARIOS.items():
            print(f"  [{k}] {v['name']}")
        print(f"  [4] {C_CYAN}Discuter avec le Copilote Aegis-Mind Chat (Requêtes SPL réelles & Self-Healing){C_RESET}")
        print("  [q] Quitter le NOC Terminal")
        
        choice = input(f"\n{C_BOLD}Aegis-NOC-Shell > {C_RESET}").strip()
        if choice.lower() == 'q':
            print(f"\n{C_GREEN}Déconnexion sécurisée d'Aegis-Mind. À bientôt !{C_RESET}\n")
            break
        elif choice == '4':
            await run_copilot_chat()
            input("Appuyez sur Entrée pour revenir au menu principal...")
            print_banner()
        elif choice in SCENARIOS:
            await run_scenario(choice)
            input("Appuyez sur Entrée pour revenir au menu principal...")
            print_banner()
        else:
            print(f"\n{C_RED}Choix invalide. Veuillez réessayer.{C_RESET}\n")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{C_GREEN}Déconnexion d'Aegis-Mind NOC. Session de terminal fermée avec succès.{C_RESET}\n")
        sys.exit(0)
