import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.SplunkAIAssistant")

class SplunkAIAssistant:
    """
    Interface d'interaction avec le 'Splunk AI Assistant (SAIA)'.
    
    Permet de traduire des requêtes formulées en langage naturel en requêtes SPL 
    (Splunk Processing Language) conformes aux meilleures pratiques Splunk,
    et de valider la syntaxe des requêtes avant exécution.
    """

    @staticmethod
    def generate_spl(natural_language_request: str, index: str = "main") -> str:
        """
        Simule ou appelle le Splunk AI Assistant pour traduire une demande en requête SPL.
        
        Args:
            natural_language_request (str): La demande de recherche de logs en langage naturel.
            index (str): L'index Splunk ciblé.
            
        Returns:
            str: Requête SPL finale prête à être exécutée.
        """
        request_lower = natural_language_request.lower()
        spl_query = ""

        # Dictionnaire de règles bilingues (Français / Anglais) pour scénarios précis
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
            # Fallback SPL générique propre
            spl_query = (
                f'search index={index} "{natural_language_request}"\n'
                f'| head 100\n'
                f'| stats count by sourcetype, host'
            )

        # Ajouter automatiquement la commande d'enrichissement Aegis-Mind si elle n'est pas déjà présente
        # (on évite de l'ajouter si la requête se termine par une commande prédictive de séries temporelles spécifique)
        if "aegismind" not in spl_query.lower() and "predict" not in spl_query.lower():
            spl_query = spl_query.strip() + "\n| aegismind"

        logger.info(f"[SAIA] Traduction réussie.\nDemande: '{natural_language_request}'\nSPL généré:\n{spl_query}")
        return spl_query

    @staticmethod
    def validate_spl(spl_query: str) -> dict:
        """
        Valide la syntaxe de la requête SPL (moteur App Inspect / SAIA).
        
        Args:
            spl_query (str): Requête SPL à vérifier.
            
        Returns:
            dict: Statut de validation {"valid": bool, "error": str/None}.
        """
        # Vérification basique des balises et pipes
        if not spl_query.strip().startswith("search") and not spl_query.strip().startswith("|"):
            return {"valid": False, "error": "Une requête SPL doit commencer par le mot-clé 'search' ou un pipe '|'."}
            
        # Détection d'injections ou commandes d'écriture dangereuses pour la sécurité
        dangerous_commands = ["| delete", "| outputcsv", "| outputlookup"]
        for cmd in dangerous_commands:
            if cmd in spl_query.lower():
                return {"valid": False, "error": f"La commande de modification de données '{cmd}' est interdite pour des raisons de sécurité."}

        return {"valid": True, "error": None}
