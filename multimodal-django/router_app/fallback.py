# router_app/fallback.py
import logging
import ollama
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class FallbackHandler:
    """
    Gestionnaire de fallback avec 3 stratégies utilisant les vrais modèles Ollama
    """
    
    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold
        
        # Noms exacts des modèles
        self.models = {
            "principal": "llama3.2:latest",
            "alternatif": "mistral:7b",
            "secondaire": "qwen3:8b",
            "vision": "llava:latest",
        }
        
        logger.info(f"[Fallback] Initialisé avec seuil: {confidence_threshold}")
    
    def handle(self, modality: str, question: str, context: dict, 
               original_confidence: float, original_answer: str = None) -> Tuple[str, float, str]:
        """Gère le fallback selon la modalité"""
        
        logger.info(f"[Fallback] Activation - Modalité: {modality}, Confiance: {original_confidence:.0%}")
        
        # Stratégie 1: Modèle alternatif
        answer, confidence, method = self._try_alternative_model(modality, question, context)
        if answer and confidence >= self.confidence_threshold:
            logger.info(f"[Fallback] ✅ Stratégie 1 réussie: {method}")
            return answer, confidence, method
        
        # Stratégie 2: Reformulation
        answer, confidence, method = self._try_reformulation(modality, question, context)
        if answer and confidence >= self.confidence_threshold:
            logger.info(f"[Fallback] ✅ Stratégie 2 réussie: {method}")
            return answer, confidence, method
        
        # Stratégie 3: Réponse générique
        answer, confidence, method = self._generic_response(modality, question, original_confidence)
        logger.info(f"[Fallback] ⚠️ Stratégie 3 utilisée: {method}")
        return answer, confidence, method
    
    def _try_alternative_model(self, modality: str, question: str, context: dict):
        """Utilise le modèle alternatif (mistral)"""
        logger.info(f"[Fallback] Stratégie 1: Modèle alternatif ({self.models['alternatif']})")
        
        try:
            if modality == "document":
                content = context.get("text", "")
                if not content:
                    return None, 0.0, None
                
                prompt = f"Document: {content[:2500]}\n\nQuestion: {question}\n\nRéponse:"
                response = ollama.chat(
                    model=self.models["alternatif"],
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.5}
                )
                return response['message']['content'], 0.82, f"alternative_model ({self.models['alternatif']})"
            
            elif modality == "structured":
                data = context.get("data", {})
                content = str(data)[:2000]
                prompt = f"Données: {content}\n\nQuestion: {question}\n\nRéponse:"
                response = ollama.chat(
                    model=self.models["alternatif"],
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.5}
                )
                return response['message']['content'], 0.80, f"alternative_structured ({self.models['alternatif']})"
                
        except Exception as e:
            logger.error(f"[Fallback] Erreur modèle alternatif: {e}")
        
        return None, 0.0, None
    
    def _try_reformulation(self, modality: str, question: str, context: dict):
        """Reformule la question et réessaie avec le modèle principal"""
        logger.info(f"[Fallback] Stratégie 2: Reformulation")
        
        try:
            reformulations = self._generate_reformulations(question)
            
            for reformulated in reformulations:
                logger.info(f"[Fallback] Test: '{reformulated}'")
                
                if modality == "document":
                    content = context.get("text", "")
                    if not content:
                        continue
                    
                    prompt = f"Document: {content[:2500]}\n\nQuestion: {reformulated}\n\nRéponse:"
                    response = ollama.chat(
                        model=self.models["principal"],
                        messages=[{"role": "user", "content": prompt}],
                        options={"temperature": 0.6}
                    )
                    answer = response['message']['content']
                    if len(answer) > 10:
                        return answer, 0.78, f"reformulation: '{reformulated[:30]}...'"
                        
        except Exception as e:
            logger.error(f"[Fallback] Erreur reformulation: {e}")
        
        return None, 0.0, None
    
    def _generate_reformulations(self, question: str) -> list:
        """Génère des reformulations de la question"""
        reformulations = []
        q = question.lower()
        
        # Supprimer les formules de politesse
        politesse = ["pourriez-vous", "s'il vous plaît", "est-ce que", "pourrais-tu"]
        for p in politesse:
            if p in q:
                q = q.replace(p, "")
        q = q.strip()
        if q and q != question.lower():
            reformulations.append(q)
        
        # Version courte
        mots = q.split()
        if len(mots) > 6:
            reformulations.append(" ".join(mots[:6]) + " ?")
        
        # Questions spécifiques
        if "durée" in q:
            reformulations.append("Quelle est la durée ?")
        if "prix" in q:
            reformulations.append("Quel est le prix ?")
        if "âge" in q:
            reformulations.append("Quel âge ?")
        
        if not reformulations:
            reformulations = [question.strip().replace("?", "").split(".")[0] + " ?"]
        
        return list(set(reformulations))[:5]
    
    def _generic_response(self, modality: str, question: str, original_confidence: float):
        """Réponse générique quand tout a échoué"""
        logger.info(f"[Fallback] Stratégie 3: Réponse générique")
        
        messages = {
            "document": [
                "Je n'ai pas trouvé de réponse fiable dans ce document.",
                "Vérifiez que le document contient l'information recherchée.",
                "Essayez de reformuler votre question plus simplement."
            ],
            "image": [
                "Je n'ai pas pu analyser cette image de façon fiable.",
                "L'image n'est pas assez claire.",
                "Essayez avec une image plus nette."
            ],
            "structured": [
                "Je n'ai pas trouvé de réponse fiable dans ces données.",
                "Vérifiez que les données sont correctement formatées.",
                "Essayez une question plus précise."
            ]
        }
        
        msg = messages.get(modality, messages["document"])
        answer = f"""Désolé, je n'ai pas de réponse fiable.

{msg[0]}
{msg[1]}

💡 Suggestion: {msg[2]}

(Confiance originale: {original_confidence:.0%})"""
        
        return answer, 0.30, "generic_response"