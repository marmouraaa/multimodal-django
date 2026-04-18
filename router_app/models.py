# router_app/models.py
import ollama
import logging
import base64
import os

logger = logging.getLogger(__name__)


class TextModel:
    """Modèle texte pour documents - utilise llama3.2:latest"""
    
    def __init__(self, model_name="llama3.2:latest"):
        self.model_name = model_name
        logger.info(f"[TextModel] Initialisé: {model_name}")
    
    def answer(self, content, question):
        try:
            max_length = 3000
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            prompt = f"""Voici un document texte :
{content}

Question : {question}

Réponds de manière précise et concise en te basant uniquement sur le document fourni.
Réponse :"""
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.7,
                    "num_predict": 500
                }
            )
            answer = response['message']['content']
            return answer, 0.85
            
        except Exception as e:
            logger.error(f"[TextModel] Erreur: {e}")
            return f"Erreur du modèle texte: {str(e)}", 0.0



# router_app/models.py - VisionModel

class VisionModel:
    """Modèle vision pour images - utilise llava:latest"""
    
    def __init__(self, model_name="llava:latest"):
        self.model_name = model_name.strip()
        logger.info(f"[VisionModel] Initialisé: {self.model_name}")
    
    def analyze(self, image_input, question):
        logger.info(f"[VisionModel] Début analyse - Type: {type(image_input)}")
        
        try:
            image_bytes = None
            
            # Si c'est une string (chemin de fichier)
            if isinstance(image_input, str):
                logger.info(f"[VisionModel] String reçue: {image_input}")
                if not os.path.exists(image_input):
                    raise FileNotFoundError(f"Fichier non trouvé: {image_input}")
                with open(image_input, 'rb') as f:
                    image_bytes = f.read()
                logger.info(f"[VisionModel] Lu {len(image_bytes)} bytes depuis chemin")
            
            # Si c'est déjà des bytes
            elif isinstance(image_input, bytes):
                logger.info(f"[VisionModel] Bytes reçus: {len(image_input)}")
                image_bytes = image_input
            
            # Si c'est None
            elif image_input is None:
                logger.error("[VisionModel] image_input est None!")
                return "Aucune image fournie. Veuillez uploader une image valide.", 0.0
            
            else:
                logger.error(f"[VisionModel] Type non supporté: {type(image_input)}")
                return f"Type d'image non supporté: {type(image_input)}", 0.0
            
            if image_bytes is None:
                return "Aucune donnée image reçue", 0.0
            
            # Convertir en base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.info(f"[VisionModel] Base64 encodé: {len(image_base64)} caractères")
            
            # Appel à Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": question,
                    "images": [image_base64]
                }],
                options={
                    "temperature": 0.7,
                    "num_predict": 500
                }
            )
            
            answer = response['message']['content']
            logger.info(f"[VisionModel] Réponse reçue: {answer[:100]}...")
            return answer, 0.88
            
        except FileNotFoundError as e:
            logger.error(f"[VisionModel] Fichier non trouvé: {e}")
            return f"L'image n'a pas été trouvée: {str(e)}", 0.0
        except Exception as e:
            logger.error(f"[VisionModel] Erreur: {e}")
            return f"Erreur d'analyse de l'image: {str(e)}", 0.0
class StructuredModel:
    """Modèle pour données structurées - utilise qwen3:8b"""
    
    def __init__(self, model_name="qwen3:8b"):
        self.model_name = model_name
        logger.info(f"[StructuredModel] Initialisé: {model_name}")
    
    def query(self, data, question):
        try:
            if hasattr(data, 'to_dict'):
                text_data = str(data.head(50)).strip()
            elif isinstance(data, dict):
                import json
                text_data = json.dumps(data, ensure_ascii=False, indent=2)[:2000]
            elif isinstance(data, list):
                text_data = str(data)[:2000]
            else:
                text_data = str(data)[:2000]
            
            prompt = f"""Voici des données structurées :
{text_data}

Question : {question}

Analyse ces données et réponds à la question de manière précise.
Réponse :"""
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "num_predict": 500
                }
            )
            answer = response['message']['content']
            return answer, 0.85
            
        except Exception as e:
            logger.error(f"[StructuredModel] Erreur: {e}")
            return f"Erreur d'analyse des données: {str(e)}", 0.0


class AlternativeTextModel:
    """Modèle texte alternatif pour fallback - utilise mistral:7b"""
    
    def __init__(self, model_name="mistral:7b"):
        self.model_name = model_name
        logger.info(f"[AlternativeTextModel] Initialisé: {model_name}")
    
    def answer(self, content, question):
        try:
            max_length = 3000
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            prompt = f"""Document : {content}

Question : {question}

Réponse :"""
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.5,
                    "num_predict": 500
                }
            )
            answer = response['message']['content']
            return answer, 0.80
            
        except Exception as e:
            logger.error(f"[AlternativeTextModel] Erreur: {e}")
            return "", 0.0