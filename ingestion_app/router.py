# ingestion_app/router.py
"""
Pont d'intégration complet entre :
- P2 (Rayen) : parsed_content, extracted_text
- P3 (Amira) : classification, routage, fallback
- P1 (Amine) : modèles IA
"""

import time
import logging
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class IntegrationResult:
    """Résultat standardisé pour toute l'application"""
    answer: str
    confidence: float
    confidence_percent: int
    modality: str
    model_used: str
    processing_time: float
    fallback_used: bool
    fallback_reason: str
    classification_method: str
    classification_confidence: int
    mime_type: Optional[str]


def route_and_answer(uploaded_file, question: str) -> IntegrationResult:
    start = time.time()
    
    # ============================================================
    # LOGS INITIAUX
    # ============================================================
    logger.info("=" * 80)
    logger.info(f"[INTEGRATION] === DÉBUT ROUTAGE ===")
    logger.info(f"[INTEGRATION] Fichier: {uploaded_file.original_filename}")
    logger.info(f"[INTEGRATION] Modalité BDD: {uploaded_file.modality}")
    logger.info(f"[INTEGRATION] Question: {question[:100]}...")
    
    # ============================================================
    # ÉTAPE 1 : CLASSIFICATION P3 (Amira)
    # ============================================================
    from router_app.classifier import ModalityClassifier
    
    classifier = ModalityClassifier()
    file_path = uploaded_file.file.path
    
    logger.info(f"[INTEGRATION] Chemin fichier: {file_path}")
    logger.info(f"[INTEGRATION] Fichier existe: {os.path.exists(file_path)}")
    
    classification = classifier.classify(file_path)
    
    logger.info(f"[INTEGRATION] Classification P3: {classification.modality} "
                f"(conf: {classification.confidence}, method: {classification.method}, mime: {classification.mime})")
    
    # ============================================================
    # ÉTAPE 2 : PRÉPARATION CONTENU P2 (Rayen)
    # ============================================================
    parsed_content = {
        "type": classification.modality,
        "text": uploaded_file.extracted_text or "",
        "file_path": file_path,
        "image_path": file_path if classification.modality == "image" else None,
        "data": {},
    }
    
    # ============================================================
    # LOGS DU CONTENU PARSÉ
    # ============================================================
    logger.info(f"[INTEGRATION] parsed_content:")
    logger.info(f"  - type: {parsed_content['type']}")
    logger.info(f"  - file_path: {parsed_content['file_path']}")
    logger.info(f"  - image_path: {parsed_content['image_path']}")
    logger.info(f"  - text length: {len(parsed_content['text'])}")
    
    # ============================================================
    # ÉTAPE 3 : ROUTAGE VERS MODÈLES P1 (Amira)
    # ============================================================
    from .ai_models import DocumentModel, ImageModel, StructuredDataModel, FallbackModel
    
    fallback_used = False
    fallback_reason = ""
    response = None
    
    try:
        if classification.modality == "document":
            logger.info("[INTEGRATION] Routage vers DocumentModel (P1)")
            model = DocumentModel()
            response = model.answer(question, parsed_content.get("text", ""))
            
        elif classification.modality == "image":
            logger.info("[INTEGRATION] === IMAGE DEBUG ===")
            logger.info(f"[INTEGRATION] file_path: {file_path}")
            logger.info(f"[INTEGRATION] uploaded_file.file.path: {uploaded_file.file.path if uploaded_file.file else None}")
            
            # Vérifier si le fichier existe
            if file_path and os.path.exists(file_path):
                logger.info(f"[INTEGRATION] ✅ Fichier image trouvé: {file_path}")
                logger.info(f"[INTEGRATION] Taille: {os.path.getsize(file_path)} bytes")
            else:
                logger.error(f"[INTEGRATION] ❌ Fichier image NON trouvé: {file_path}")
                # Essayer un autre chemin
                alt_path = uploaded_file.file.path if uploaded_file.file else None
                if alt_path and os.path.exists(alt_path):
                    file_path = alt_path
                    logger.info(f"[INTEGRATION] ✅ Chemin alternatif fonctionne: {file_path}")
            
            model = ImageModel()
            response = model.answer(question, "", file_path=file_path)
            
        elif classification.modality == "structured":
            logger.info("[INTEGRATION] Routage vers StructuredDataModel (P1)")
            logger.info(f"[INTEGRATION] extracted_text length: {len(uploaded_file.extracted_text)}")
            logger.info(f"[INTEGRATION] extracted_text preview: {uploaded_file.extracted_text[:200] if uploaded_file.extracted_text else 'VIDE'}")
            model = StructuredDataModel()
            response = model.answer(question, parsed_content.get("text", ""))
            
        else:
            logger.warning(f"[INTEGRATION] Modalité inconnue: {classification.modality}")
            model = FallbackModel()
            response = model.answer(question, "", modality="unknown")
            fallback_used = True
            fallback_reason = f"Modalité inconnue: {classification.modality}"
        
        # Si la confiance est trop faible, déclencher fallback P3
        if response and response.confidence < 0.6 and not fallback_used:
            logger.info(f"[INTEGRATION] Confiance P1 trop faible ({response.confidence:.0%}) → fallback P3")
            from router_app.fallback import FallbackHandler
            fallback = FallbackHandler(confidence_threshold=0.6)
            fb_answer, fb_conf, fb_method = fallback.handle(
                modality=classification.modality,
                question=question,
                context=parsed_content,
                original_confidence=response.confidence,
                original_answer=response.answer
            )
            response.answer = fb_answer
            response.confidence = fb_conf
            fallback_used = True
            fallback_reason = f"Fallback P3: {fb_method}"
        
        if response and response.fallback_used and not fallback_used:
            fallback_used = True
            fallback_reason = response.fallback_reason or "Fallback interne P1"
            
    except Exception as e:
        logger.error(f"[INTEGRATION] Erreur: {e}")
        response = FallbackModel().answer(question, "", modality=classification.modality)
        fallback_used = True
        fallback_reason = f"Erreur: {str(e)}"
    
    # ============================================================
    # LOG FINAL
    # ============================================================
    logger.info(f"[INTEGRATION] Résultat final:")
    logger.info(f"  - answer: {response.answer[:200] if response.answer else 'VIDE'}...")
    logger.info(f"  - confidence: {response.confidence}")
    logger.info(f"  - fallback_used: {fallback_used}")
    logger.info("=" * 80)
    
    # ============================================================
    # ÉTAPE 4 : RÉSULTAT FORMATÉ
    # ============================================================
    return IntegrationResult(
        answer=response.answer,
        confidence=response.confidence,
        confidence_percent=int(response.confidence * 100),
        modality=classification.modality,
        model_used=response.model_used,
        processing_time=round(time.time() - start, 2),
        fallback_used=fallback_used,
        fallback_reason=fallback_reason,
        classification_method=classification.method,
        classification_confidence=int(classification.confidence * 100),
        mime_type=classification.mime,
    )