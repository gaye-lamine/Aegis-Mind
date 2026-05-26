# Ressources de Développement : Splunk Agentic Ops Hackathon

Ce document compile tous les liens d'accès, la documentation officielle et les outils de support pour le développement de notre projet Aegis-Mind.

---

## 🔑 Obtention des Accès Splunk

1.  **Créer un compte Splunk gratuit :**
    *   S'inscrire sur [splunk.com/en_us/form/sign-up.html](https://www.splunk.com/en_us/form/sign-up.html).
2.  **Télécharger la version d'essai Splunk Enterprise :**
    *   Télécharger l'installateur sur [splunk.com/en_us/download/splunk-enterprise.html](https://www.splunk.com/en_us/download/splunk-enterprise.html) (valable 60 jours).
3.  **Demander une licence développeur :**
    *   S'enregistrer au programme développeur via [dev.splunk.com](https://dev.splunk.com/) pour obtenir une licence développeur gratuite (valable 6 mois).
    *   *Note :* Si vous possédez déjà une instance Splunk (Cloud ou Enterprise), vous pouvez simplement demander la licence développeur et l'appliquer à votre instance existante.

---

## 🛠️ Outils & Technologies IA Splunk

Nous sommes encouragés à intégrer une ou plusieurs des technologies suivantes :

### 1. AI for Splunk Apps (Python SDK)
Permet de concevoir des flux agentiques à l'intérieur des applications Splunk via le SDK Python.
*   [Dépôt & Instructions de Configuration (README)](#)
*   [Exemple d'application d'alertes personnalisées IA (AI Custom Alert App)](#)
*   [Exemple d'application de recherche personnalisée IA (AI Custom Search App)](#)
*   [Exemple d'entrée modulaire IA (AI Modular Input App)](#)

### 2. Splunk MCP Server
Permet de connecter de manière sécurisée des agents IA aux données Splunk en utilisant le **Model Context Protocol**.
*   **Authentification :** L'authentification OAuth est en phase de disponibilité contrôlée (CA). Pour ce hackathon, il est recommandé d'utiliser l'**authentification par jeton (token-based)**.
*   [Présentation du serveur MCP pour la plateforme Splunk](https://docs.splunk.com)
*   [Guide de configuration du serveur MCP](https://docs.splunk.com)
*   [Opérationnalisation de la sécurité du serveur MCP avec Splunk MCP TA](https://docs.splunk.com)
*   [Application Splunk MCP Server sur Splunkbase (App ID: 7931)](https://splunkbase.splunk.com/app/7931)

### 3. Splunk AI Assistant (SAIA)
Assistant IA pour aider à concevoir et optimiser des requêtes SPL en langage naturel.
*   [Aperçu général de Splunk AI Assistant pour SPL](https://docs.splunk.com)
*   [Téléchargement de l'application Splunk AI Assistant sur Splunkbase](https://splunkbase.splunk.com)
*   [Activation de l'assistant IA Enterprise pour SPL](https://docs.splunk.com)
*   [Intégration d'un assistant IA dans Splunk Observability Cloud](https://docs.splunk.com)

### 4. Splunk AI Toolkit (AITK)
Permet de concevoir des modèles d'apprentissage personnalisés pour obtenir des informations exploitables à partir de nos propres données.
*   [Présentation de Splunk AI Toolkit](https://docs.splunk.com)
*   [Téléchargement d'AITK sur Splunkbase](https://splunkbase.splunk.com)
*   [Mise en œuvre des cas d'usage IA avec Splunk](https://docs.splunk.com)

### 5. Modèles IA Hébergés (Splunk Hosted Models)
Utilisation de modèles d'IA pré-entraînés hébergés :
*   **Foundation AI Security Model (Foundation-Sec-1.1-8B-Instruct) :** Optimisé pour les tâches de cybersécurité. [Fiche Hugging Face](https://huggingface.co/Splunk/Foundation-Sec-1.1-8B-Instruct).
*   **Cisco Deep Time Series Model :** Conçu pour les séries temporelles industrielles et d'observabilité.
*   **Autres modèles open source de Splunk :** `gpt-oss-120b` et `gpt-oss-20b` sur Hugging Face.

---

## 💬 Support & Communauté du Hackathon

Pour échanger, poser des questions et collaborer :
*   **Canal Slack dédié :** `#splunk-ai-hackathon` sur le Slack de la Communauté Splunk.
*   **Comment rejoindre :**
    1.  Aller sur la page de connexion Slack de Splunk.
    2.  Se connecter avec vos identifiants Splunk (ou créer un compte).
    3.  Rechercher et rejoindre le canal `#splunk-ai-hackathon`.
