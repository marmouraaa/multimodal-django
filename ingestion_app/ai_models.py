# ingestion_app/ai_models.py
import os
import base64
import logging
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration Ollama
OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_VISION = os.environ.get("OLLAMA_VISION_MODEL", "llava:latest")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))


@dataclass
class AIResponse:
    """Réponse standardisée retournée par tous les modèles IA"""
    answer: str
    confidence: float
    model_used: str
    modality: str
    processing_time: float
    fallback_used: bool = False
    fallback_reason: str = ""
    error: Optional[str] = None
    
    def confidence_percent(self):
        return int(self.confidence * 100)
    
    def confidence_level(self):
        if self.confidence >= 0.8:
            return 'high'
        elif self.confidence >= 0.4:
            return 'medium'
        return 'low'


def call_ollama(prompt: str, model: str = None, system: str = None, image_base64: str = None):
    """Appelle l'API Ollama"""
    model = model or OLLAMA_MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 800}
    }
    if system:
        payload["system"] = system
    if image_base64:
        payload["images"] = [image_base64]
    
    logger.info(f"Appel Ollama model={model}")
    r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=OLLAMA_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    response_text = data.get("response", "").strip()
    confidence = 0.85 if len(response_text) > 30 else 0.68
    return response_text, confidence


class DocumentModel:
    """Modèle pour les documents texte"""
    
    def __init__(self):
        self.model_name = OLLAMA_MODEL
        logger.info(f"[DocumentModel] Initialisé: {self.model_name}")
    
    def answer(self, question: str, content: str) -> AIResponse:
        import time
        start = time.time()
        
        truncated = content[:6000]
        prompt = f"Document:\n---\n{truncated}\n---\n\nQuestion: {question}\n\nRéponse:"
        
        try:
            text, conf = call_ollama(prompt)
            return AIResponse(
                answer=text, confidence=conf,
                model_used=f"ollama/{self.model_name}",
                modality="document", processing_time=round(time.time()-start, 2)
            )
        except Exception as e:
            logger.error(f"DocumentModel error: {e}")
            return AIResponse(
                answer="", confidence=0.0, model_used="none",
                modality="document", processing_time=round(time.time()-start, 2),
                error=str(e)
            )


class ImageModel:
    """Modèle pour les images"""
    
    def __init__(self):
        self.model_name = OLLAMA_VISION
        logger.info(f"[ImageModel] Initialisé: {self.model_name}")
    
    def _load_image_b64(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.warning(f"Impossible de charger l'image: {e}")
            return None
    
    def answer(self, question: str, content: str = "", **kwargs) -> AIResponse:
        import time
        start = time.time()
        file_path = kwargs.get("file_path")
        img_b64 = self._load_image_b64(file_path)
        
        try:
            if img_b64:
                text, conf = call_ollama(question, model=self.model_name, image_base64=img_b64)
                return AIResponse(
                    answer=text, confidence=conf,
                    model_used=f"ollama/{self.model_name}",
                    modality="image", processing_time=round(time.time()-start, 2)
                )
            else:
                return AIResponse(
                    answer="Impossible de charger l'image.", confidence=0.0,
                    model_used="none", modality="image",
                    processing_time=round(time.time()-start, 2), error="Image non trouvée"
                )
        except Exception as e:
            logger.error(f"ImageModel error: {e}")
            return AIResponse(
                answer="", confidence=0.0, model_used="none",
                modality="image", processing_time=round(time.time()-start, 2), error=str(e)
            )


class StructuredDataModel:
    """Modèle pour les données structurées"""
    
    def __init__(self):
        self.model_name = OLLAMA_MODEL
        logger.info(f"[StructuredDataModel] Initialisé: {self.model_name}")
    
    def answer(self, question: str, content: str) -> AIResponse:
        import time
        start = time.time()
        
        prompt = f"Données:\n---\n{content[:5000]}\n---\n\nQuestion: {question}\n\nRéponse:"
        
        try:
            text, conf = call_ollama(prompt)
            return AIResponse(
                answer=text, confidence=conf,
                model_used=f"ollama/{self.model_name}",
                modality="structured", processing_time=round(time.time()-start, 2)
            )
        except Exception as e:
            logger.error(f"StructuredDataModel error: {e}")
            return AIResponse(
                answer="", confidence=0.0, model_used="none",
                modality="structured", processing_time=round(time.time()-start, 2), error=str(e)
            )


class FallbackModel:
    """Modèle de fallback"""
    
    def __init__(self):
        self.model_name = OLLAMA_MODEL
        logger.info(f"[FallbackModel] Initialisé: {self.model_name}")
    
    def answer(self, question: str, content: str = "", **kwargs) -> AIResponse:
        import time
        start = time.time()
        modality = kwargs.get("modality", "unknown")
        
        prompt = f"Question: {question}\n\nRéponds de façon courte et simple (une phrase maximum)."
        
        try:
            text, conf = call_ollama(prompt)
            conf = min(conf, 0.60)
            return AIResponse(
                answer=text, confidence=conf,
                model_used=f"ollama/{self.model_name} (fallback)",
                modality=modality, processing_time=round(time.time()-start, 2),
                fallback_used=True, fallback_reason="Confiance insuffisante"
            )
        except Exception as e:
            return AIResponse(
                answer="Je ne suis pas en mesure de répondre. Essayez de reformuler votre question.",
                confidence=0.15, model_used="none", modality=modality,
                processing_time=round(time.time()-start, 2),
                fallback_used=True, fallback_reason=str(e), error=str(e)
            )


def get_ollama_status() -> dict:
    """Retourne le statut d'Ollama"""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return {
                "available": True,
                "url": OLLAMA_BASE_URL,
                "models": models,
                "llama3_ok": any(m.startswith("llama3") for m in models),
                "llava_ok": any(m.startswith("llava") for m in models),
            }
    except Exception:
        pass
    return {"available": False, "url": OLLAMA_BASE_URL, "models": [], "message": "Ollama non disponible"}