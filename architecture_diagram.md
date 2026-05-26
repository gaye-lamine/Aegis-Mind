# Aegis-Mind: Architecture Diagram

This document presents the detailed architectural blueprint of **Aegis-Mind — Autonomous Multi-Agent NOC for Incident Response**, showing how the core agents, external systems (Splunk), and user interfaces coordinate to manage infrastructure crises autonomously.

---

## 🏗️ System Architecture

```text
[ Infrastructure Télémétrie ]
             │
             ▼ (Ingestion continue)
┌───────────────────────────────────────────────┐
│              Splunk Enterprise                │◄────────┐
│             (Moteur de Recherche)             │         │
└───────────────────────┬───────────────────────┘         │
                        │                                 │
     Déclenchement      │ (Token Auth)                    │ Requêtes SPL /
    AI Custom Alert     ▼                                 │ Tool-Calling
┌───────────────────────────────────────────────┐         │ (Splunk MCP Server)
│             Aegis-Mind Gateway                │         │
└───────────────────────┬───────────────────────┘         │
                        │                                 │
                        ▼ (Orchestration des Tâches)      │
┌─────────────────────────────────────────────────────────┼────────┐
│                     AEGIS-MIND CORE                     │        │
│                                                         │        │
│    ┌─────────────────────────────────────────────┐      │        │
│    │  🕵️♂️ Agent d'Investigation (Triage)         ├──────►│        │
│    │  Modèle : Foundation-Sec-1.1-8B-Instruct     │      │        │
│    └──────────────────────┬──────────────────────┘      │        │
│                           │                             │        │
│    ┌──────────────────────▼──────────────────────┐      │        │
│    │  📊 Agent de Corrélation Temporelle         ├──────►│        │
│    │  Modèle : Cisco Deep Time Series Model      │      │        │
│    └──────────────────────┬──────────────────────┘      │        │
│                           │                             │        │
│    ┌──────────────────────▼──────────────────────┐      │        │
│    │  ⚡ Agent d'Auto-Remédiation (Playbook)      ├──────┘        │
│    │  Modèle : gpt-oss-120b                      │               │
│    └─────────────────────────────────────────────┘               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux d'Exécution & Données (Data Flow)

### Étape 1 : Détection & Déclenchement (AI Custom Alert)
*   **Source :** Les logs d'infrastructure (Kubernetes, AWS, firewall, base de données) sont centralisés dans **Splunk**.
*   **Mécanisme :** Une alerte personnalisée d'intelligence artificielle (**AI Custom Alert**) surveille les anomalies de sécurité ou opérationnelles.
*   **Action :** Dès qu'une anomalie critique est détectée, Splunk envoie une alerte HTTP contenant les métadonnées de l'incident à la passerelle **Aegis-Mind Gateway**.

### Étape 2 : Triage & Analyse Cyber (Triage Agent)
*   **Orchestrateur :** L'agent d'investigation se réveille sous l'égide du **Google Antigravity SDK**.
*   **Modèle Utilisé :** `Foundation-Sec-1.1-8B-Instruct`.
*   **Interactions :**
    *   L'agent se connecte de manière sécurisée au **Splunk MCP Server** en utilisant l'authentification par jeton (*Token Authentication*).
    *   Il utilise le **Splunk AI Assistant** pour formuler dynamiquement des requêtes SPL adaptées au contexte.
    *   Il extrait les logs environnants des 2 dernières heures concernant l'adresse IP, le conteneur ou l'utilisateur suspect pour cartographier le vecteur d'attaque.
    *   **Circuit Breaker :** Si l'analyse révèle un faux positif évident, l'agent coupe immédiatement le flux pour économiser les quotas d'API Splunk.

### Étape 3 : Corrélation Temporelle & Prévision d'Impact (Time-Series Agent)
*   **Mission :** Comprendre l'impact global sur la production.
*   **Modèle Utilisé :** `Cisco Deep Time Series Model`.
*   **Interactions :**
    *   L'agent extrait les indicateurs de performance clés (KPI) de l'infrastructure via le serveur MCP.
    *   Il compare les métriques actuelles avec les baselines historiques de Splunk.
    *   Il prédit l'évolution des métriques critiques à court terme (t + 15 min, t + 1 h) pour évaluer si l'incident va paralyser les services de production.

### Étape 4 : Conception du Playbook & Auto-Remédiation (Remediation Agent)
*   **Mission :** Générer, valider et exécuter le plan de secours.
*   **Modèle Utilisé :** `gpt-oss-120b` (ou équivalent LLM de remédiation).
*   **Interactions :**
    *   Sur la base des rapports d'incident et d'impact, l'agent élabore un script de remédiation cyber précis (par exemple, mise à jour des règles du pare-feu, révocation de jeton IAM compromise, redémarrage du pod Kubernetes).
    *   Le playbook est exécuté via l'infrastructure sécurisée.
    *   Une fois la correction appliquée, l'agent ré-interroge Splunk via le serveur MCP pour valider le retour à la normale de la production.

### Étape 5 : Clôture & Rapport de Crise (NOC Terminal UI)
*   **Visualisation :** Toutes les pensées de l'agent (*thoughts*), les requêtes SPL formulées, et les playbooks générés sont diffusés en direct sur l'interface **NOC Terminal**.
*   **Livrable Final :** Le système enregistre automatiquement un rapport d'incident complet contenant un diagramme d'attaque au format **Mermaid.js** dans l'espace de travail.
