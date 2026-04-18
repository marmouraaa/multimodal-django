# router_app/routers.py
import logging
from .classifier import ModalityClassifier

logger = logging.getLogger(__name__)


class RoutingResult:
    """Résultat du routage"""
    def __init__(self, answer, confidence, modality, fallback_used=False, fallback_method=None, method=None, mime=None):
        self.answer = answer
        self.confidence = confidence
        self.modality = modality
        self.fallback_used = fallback_used
        self.fallback_method = fallback_method
        self.method = method
        self.mime = mime


class MockModels:
    """Modèles mockés pour les tests"""
    
    class TextModel:
        def answer(self, content, question):
            if "durée" in question.lower():
                return "La durée est de 12 mois.", 0.92
            elif "prix" in question.lower():
                return "Le prix est de 150€.", 0.88
            return f"Réponse à: {question}", 0.85
    
    class VisionModel:
        def analyze(self, image, question):
            if "objet" in question.lower():
                return "Je vois des objets.", 0.90
            return "Description générique.", 0.80
    
    class StructuredModel:
        def query(self, data, question):
            if "moyenne" in question.lower():
                return "La moyenne est de 28 ans.", 0.94
            return "Résultat de l'analyse.", 0.87


class MultimodalRouter:
    """
    Routeur principal : détecte la modalité et envoie au bon modèle IA
    """
    
    def __init__(self, text_model=None, vision_model=None, structured_model=None, 
                 confidence_threshold=0.6):
        
        # Utilise les mocks si aucun modèle n'est fourni
        self.text_model = text_model or MockModels.TextModel()
        self.vision_model = vision_model or MockModels.VisionModel()
        self.structured_model = structured_model or MockModels.StructuredModel()
        
        self.classifier = ModalityClassifier()
        self.confidence_threshold = confidence_threshold
        
        logger.info(f"[ROUTER] Initialisé avec seuil: {confidence_threshold}")
    
    def process(self, parsed_content, question):
        """Traite la question et le contenu pour retourner une réponse"""
        
        logger.info("=" * 50)
        logger.info(f"[ROUTER] Question: {question}")
        
        if not parsed_content:
            return RoutingResult(
                answer="Désolé, aucun contenu à analyser.",
                confidence=0.0, modality="unknown",
                fallback_used=True, fallback_method="empty_content"
            )
        
        content_type = parsed_content.get("type", "unknown")
        file_path = parsed_content.get("file_path")
        
        if file_path:
            classification = self.classifier.classify(file_path)
            modality = classification.modality
            confidence = classification.confidence
            method = classification.method
            mime = classification.mime
            logger.info(f"[ROUTER] Classification: {modality} (conf: {confidence}, method: {method})")
        else:
            modality = content_type
            confidence = 0.70
            method = "provided"
            mime = None
            logger.info(f"[ROUTER] Type fourni: {modality}")
        
        if confidence < self.confidence_threshold:
            return RoutingResult(
                answer="Je ne suis pas sûr du type de fichier. Veuillez reformuler.",
                confidence=confidence, modality=modality,
                fallback_used=True, fallback_method="low_confidence",
                method=method, mime=mime
            )
        
        try:
            if modality == "document":
                text_content = parsed_content.get("text", "")
                answer, model_conf = self.text_model.answer(text_content, question)
            elif modality == "image":
                image_content = parsed_content.get("image")
                answer, model_conf = self.vision_model.analyze(image_content, question)
            elif modality == "structured":
                data_content = parsed_content.get("data")
                answer, model_conf = self.structured_model.query(data_content, question)
            else:
                return RoutingResult(
                    answer="Type de fichier non reconnu.",
                    confidence=0.0, modality=modality,
                    fallback_used=True, fallback_method="unknown_modality",
                    method=method, mime=mime
                )
            
            logger.info(f"[ROUTER] Réponse confiance: {model_conf}")
            
            if model_conf < self.confidence_threshold:
                return RoutingResult(
                    answer=f"{answer}\n\n(Confiance: {model_conf:.0%})",
                    confidence=model_conf, modality=modality,
                    fallback_used=False, method=method, mime=mime
                )
            
            return RoutingResult(
                answer=answer, confidence=model_conf, modality=modality,
                fallback_used=False, method=method, mime=mime
            )
            
        except Exception as e:
            logger.error(f"[ROUTER] Erreur: {e}")
            return RoutingResult(
                answer=f"Erreur: {str(e)}", confidence=0.0, modality=modality,
                fallback_used=True, fallback_method="error",
                method=method, mime=mime
            )