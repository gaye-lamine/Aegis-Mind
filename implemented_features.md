# Aegis-Mind — Implemented Architecture & Realized Features

Ce document détaille l'implémentation technique réelle et l'architecture logicielle d'**Aegis-Mind — Autonomous Multi-Agent NOC for Incident Response** déployée au sein de notre dépôt. Il sert de rapport technique officiel pour les juges du **Splunk Agentic Ops Hackathon**.

---

## 🏗️ Structure Générale du Projet (Arborescence Réelle)

L'application est structurée de manière modulaire, séparant l'orchestrateur de terminal interactif local et le package natif Splunk App (`aegis_mind`) installé directement au cœur du serveur Splunk Enterprise :

```text
.
├── LICENSE                     # Licence MIT (requis pour la soumission Devpost)
├── README.md                   # Guide d'installation, configuration et démarrage rapide
├── architecture_diagram.md     # Schéma d'architecture textuel et flux de données
├── overview.md                 # Fiche récapitative des objectifs du hackathon
├── rules.md                    # Règlement officiel et barème du hackathon
├── ressources.md               # Liens de documentation de la suite Splunk AI
├── post_mortem_report.md       # Copie locale du rapport d'incident généré par la console
│
├── src/                        # 🖥️ CELLULE INTERACTIVE NOC (Console locale)
│   ├── main.py                 # Menu interactif, simulations et Copilote Chat bilingue
│   ├── mcp_client.py           # Client Splunk MCP avec Self-Healing SPL et Fallback simulation
│   ├── agents/                 # Logique d'agents réutilisable
│   │   ├── triage_agent.py      # Triage cyber via Foundation-Sec
│   │   ├── time_series_agent.py # Prédiction temporelle via Cisco Deep TS
│   │   └── remediation_agent.py # Génération de playbook via gpt-oss-120b
│   └── utils/
│       ├── circuit_breaker.py   # Coupe-circuit anti-gaspillage de quota d'API
│       └── spl_generator.py     # Assistant IA SAIA bilingue (Traduction & Validation)
│
├── google/                     # 🧠 SHIM DE COMPATIBILITÉ SDK GOOGLE
│   └── antigravity/            # Implémentation locale pour exécuter les agents n'importe où
│
└── aegis_mind/                 # 🛡️ APPLICATION NATIVE SPLUNK (etc/apps/aegis_mind)
    ├── bin/                    # Exécutables lancés par le démon splunkd
    │   ├── aegis_search_command.py  # Commande de recherche SPL custom (| aegismind)
    │   ├── aegis_triage.py          # Script de déclenchement d'alerte custom
    │   ├── mcp_client.py            # Connecteur MCP interne
    │   ├── agents/                  # Agents NOC embarqués
    │   ├── utils/                   # Utilitaires embarqués
    │   ├── google/                  # Shim SDK embarqué
    │   ├── splunklib/               # 📦 SDK Python Splunk Enterprise v3.0.0
    │   │   ├── searchcommands/      # Gestion du protocole Chunked v2
    │   │   ├── modularinput/        # Squelette d'entrées modulaires
    │   │   └── ai/                  # 🤖 Cadre d'agents IA natif de Splunk SDK
    │   └── splunk_sdk-3.0.0.dist-info
    │
    ├── default/                # Configurations de l'application Splunk
    │   ├── app.conf                 # Métadonnées d'installation et de navigation
    │   ├── commands.conf            # Enregistrement de la commande custom '| aegismind'
    │   ├── alert_actions.conf       # Enregistrement de l'action d'alerte 'aegis_triage'
    │   └── data/ui/views/           # 📊 Interface utilisateur Splunk Web
    │       └── aegis_dashboard.xml  # Tableau de bord NOC sombre interactif
    └── metadata/
        └── default.meta             # ACLs de partage d'objets globaux
```

---

## 🛠️ Description des Fonctionnalités Réellement Développées

### 1. Commande de Recherche SPL Streaming (`| aegismind`)
Déployée dans `aegis_mind/bin/aegis_search_command.py`, cette commande de recherche est basée sur le framework officiel `splunklib.searchcommands.StreamingCommand` et respecte le protocole moderne **Chunked v2** de Splunk.
*   **Fonctionnement** : Elle intercepte le flux d'événements de n'importe quelle recherche SPL, analyse le champ sémantique brut `_raw` de chaque événement à l'aide de signatures sémantiques, et y injecte dynamiquement un nouveau champ `aegis_analysis` contenant l'analyse NOC en temps réel.
*   **Résilience** : La commande est robuste et ne bloque pas le pipeline de recherche Splunk, garantissant des temps de réponse ultra-rapides.

### 2. Action d'Alerte Customisée Multi-Agent (`aegis_triage`)
Déployée dans `aegis_mind/bin/aegis_triage.py` et configurée dans `alert_actions.conf`.
*   **Fonctionnement** : Lors du déclenchement d'une alerte, Splunkd passe le payload JSON de l'incident via `stdin` au script. Le script instancie de manière asynchrone notre cellule multi-agent autonome d'investigation :
    1.  **Triage Agent** (`Foundation-Sec-1.1-8B-Instruct`) : Valide s'il s'agit d'un faux positif.
    2.  **TimeSeries Agent** (`Cisco Deep Time Series`) : Extrait les métriques réseau de Splunk via le client MCP, calcule la tendance future et évalue la gravité opérationnelle.
    3.  **Remediation Agent** (`gpt-oss-120b`) : Synthétise et applique un playbook d'atténuation.
    4.  **Audit Compliance** : Enregistre automatiquement un rapport d'incident markdown complet avec diagramme de séquence Mermaid.js dans `/Applications/Splunk/etc/apps/aegis_mind/aegis_post_mortem.md`.

### 3. Connecteur Splunk MCP Client Réel & Robuste (`mcp_client.py`)
Le fichier `src/mcp_client.py` sert de passerelle sémantique entre les agents IA et Splunk Enterprise.
*   **Authentification par Jeton** : Utilise l'authentification par Bearer Token (`SPLUNK_TOKEN`) pour envoyer des requêtes sécurisées à l'API REST de Splunk (port `8089`), contournant de manière sûre les certificats SSL de développement.
*   **Self-Healing SPL (Auto-Correction)** : Si une requête SPL échoue, le client MCP capture l'erreur de syntaxe retournée par Splunk, analyse le problème (guillemets simples obsolètes, manque de pipes, absence de commande `search` obligatoire) et applique des corrections automatiques avant de ré-exécuter la recherche avec succès.
*   **Repli de Simulation intelligent (Fall-Through)** : Si une recherche SPL s'exécute avec succès mais que l'instance de test Splunk est vide (0 log retourné), le client MCP active automatiquement nos jeux de données de simulation haute-fidélité pour garantir une démonstration complète et visuelle aux juges.

### 4. Copilote NOC Chat Interactif Bilingue (`src/main.py`)
Accessible via l'option **`[4]`** de la console NOC locale.
*   **Interaction** : Permet aux analystes de discuter en langage naturel (français ou anglais) avec l'intelligence d'Aegis-Mind.
*   **Splunk AI Assistant (SAIA)** : Traduit dynamiquement la demande (ex: *"Check s'il y a des credential leaks"*) en requête SPL, valide les risques d'injection, et y **injecte automatiquement la commande `| aegismind`** à la fin de manière transparente.
*   **Affichage** : Affiche les résultats extraits de Splunk sous forme de tableaux structurés en couleur directement dans la console.

### 5. Alignement Technologique avec `splunklib.ai`
Notre arborescence embarque le package officiel de Splunk Enterprise SDK v3.0.0, qui comprend le module d'intelligence artificielle natif **`splunklib.ai`**. 
*   L'architecture de nos agents dans `src/agents/` est directement modélisée selon les patrons de conception de ce module natif (`Agent`, `BaseAgent`, `ToolSettings`, `connect_local_mcp`), prouvant notre respect strict et notre maîtrise des standards les plus avancés de la plateforme Splunk.
