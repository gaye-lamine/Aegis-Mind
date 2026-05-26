import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AegisMind.CircuitBreaker")

class QuotaCircuitBreaker:
    """
    Gestionnaire dynamique de quota d'API et coupe-circuit (Circuit Breaker) pour Aegis-Mind.
    
    Cette classe évite la fatigue des API et l'emballement des coûts en :
    1. Comptabilisant le nombre d'appels passés au serveur Splunk MCP durant une investigation.
    2. Triplant (tripping) le circuit si le quota max d'appels par incident est atteint.
    3. Bloquant préventivement les étapes lourdes si l'investigateur initial détermine que
       l'alerte est un faux positif évident (score de confiance élevé pour Faux Positif).
    """

    def __init__(self, max_requests: int = 50, fp_confidence_threshold: float = 0.85):
        self.max_requests = max_requests
        self.fp_confidence_threshold = fp_confidence_threshold
        self.request_count = 0
        self.tripped = False
        self.trip_reason = ""

    def increment_and_check(self) -> bool:
        """
        Incrémente le compteur de requêtes et vérifie s'il dépasse la limite autorisée.
        
        Returns:
            bool: True si le circuit est ouvert (bloqué/tripped), False sinon.
        """
        if self.tripped:
            return True
            
        self.request_count += 1
        if self.request_count > self.max_requests:
            self.tripped = True
            self.trip_reason = f"Quota maximum de requêtes Splunk MCP atteint ({self.max_requests})."
            logger.warning(f"[CIRCUIT BREAKER] {self.trip_reason}")
            return True
            
        return False

    def evaluate_triage(self, is_false_positive: bool, confidence_score: float) -> bool:
        """
        Évalue le rapport de triage initial pour couper le circuit si c'est un faux positif.
        
        Args:
            is_false_positive (bool): True si le triage pense que c'est un faux positif.
            confidence_score (float): Score de confiance associé à l'évaluation (0.0 à 1.0).
            
        Returns:
            bool: True si le circuit est ouvert (coupé pour économie de quota), False sinon.
        """
        if self.tripped:
            return True

        if is_false_positive and confidence_score >= self.fp_confidence_threshold:
            self.tripped = True
            self.trip_reason = (
                f"Faux positif identifié avec un niveau de confiance de {confidence_score * 100:.1f}% "
                f"(seuil de coupure: {self.fp_confidence_threshold * 100:.1f}%). "
                f"Pipeline multi-agent arrêté pour préserver les quotas."
            )
            logger.info(f"[CIRCUIT BREAKER] {self.trip_reason}")
            return True

        return False

    def reset(self):
        """Réinitialise le compteur et l'état du coupe-circuit."""
        self.request_count = 0
        self.tripped = False
        self.trip_reason = ""
        logger.info("[CIRCUIT BREAKER] Réinitialisé.")
