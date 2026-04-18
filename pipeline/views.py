# pipeline/views.py
import os
import sys
import time
import logging
import mimetypes
import PyPDF2

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import FileUploadForm, QuestionForm

# ============================================================
# Importer les modèles depuis ingestion_app
# ============================================================
from ingestion_app.models import UploadedFile, QueryResponse

# ============================================================
# Ajouter le chemin pour importer router_app
# ============================================================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer ton routeur et tes modèles
from router_app.routers import MultimodalRouter
from router_app.models import TextModel, VisionModel, StructuredModel
from router_app.classifier import ModalityClassifier

logger = logging.getLogger('pipeline')

# ============================================================
# INITIALISATION DU ROUTEUR (P3 - Amira)
# ============================================================
router = MultimodalRouter(
    text_model=TextModel(),
    vision_model=VisionModel(),
    structured_model=StructuredModel(),
    confidence_threshold=0.6
)


def extract_pdf_text(file_path):
    """Extrait le texte d'un fichier PDF"""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        logger.error(f"Erreur extraction PDF: {e}")
        return ""


def detect_modality(filename):
    """Version temporaire - sera remplacée par Personne 2"""
    ext = os.path.splitext(filename)[1].lower()
    document_exts = {'.pdf', '.docx', '.doc', '.txt'}
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    structured_exts = {'.csv', '.json', '.xlsx', '.xls'}
    if ext in document_exts:
        return 'document'
    elif ext in image_exts:
        return 'image'
    elif ext in structured_exts:
        return 'structured'
    return 'unknown'


def home(request):
    if request.method == 'POST':
        # 🔥 LOG pour vérifier le fichier reçu
        logger.info("=" * 60)
        logger.info("[HOME] Formulaire reçu")
        logger.info(f"[HOME] Fichier dans request.FILES: {request.FILES.get('file')}")
        logger.info("=" * 60)
        
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file_obj = request.FILES['file']
            mime_type, _ = mimetypes.guess_type(uploaded_file_obj.name)
            mime_type = mime_type or 'application/octet-stream'

            uploaded = UploadedFile(
                file=uploaded_file_obj,
                original_filename=uploaded_file_obj.name,
                file_size=uploaded_file_obj.size,
                modality=detect_modality(uploaded_file_obj.name),
                mime_type=mime_type,
            )
            uploaded.save()
            
            # 🔥 LOG après sauvegarde
            logger.info(f"[HOME] Fichier sauvegardé: {uploaded.file.path}")
            logger.info(f"[HOME] Fichier existe: {os.path.exists(uploaded.file.path)}")

            messages.success(
                request,
                f"Fichier \"{uploaded.original_filename}\" uploadé avec succès ! "
                f"Type détecté : {uploaded.get_modality_display()}"
            )
            return redirect('question', file_id=uploaded.pk)
    else:
        form = FileUploadForm()

    recent_files = UploadedFile.objects.all()[:10]
    return render(request, 'pipeline/home.html', {
        'form': form,
        'recent_files': recent_files,
    })


def question_view(request, file_id):
    uploaded = get_object_or_404(UploadedFile, pk=file_id)
    
    # 🔥 LOG CRITIQUE - Vérifier le fichier physique
    logger.info("=" * 60)
    logger.info(f"[QUESTION_VIEW] File ID: {file_id}")
    logger.info(f"[QUESTION_VIEW] uploaded.file: {uploaded.file}")
    logger.info(f"[QUESTION_VIEW] uploaded.file.url: {uploaded.file.url if uploaded.file else None}")
    logger.info(f"[QUESTION_VIEW] uploaded.file.path: {uploaded.file.path if uploaded.file else None}")
    
    if uploaded.file and uploaded.file.path:
        logger.info(f"[QUESTION_VIEW] Le fichier existe: {os.path.exists(uploaded.file.path)}")
        logger.info(f"[QUESTION_VIEW] Taille: {os.path.getsize(uploaded.file.path) if os.path.exists(uploaded.file.path) else 'N/A'}")
    else:
        logger.error(f"[QUESTION_VIEW] uploaded.file est None ou n'a pas de path!")
    logger.info("=" * 60)
    
    form = QuestionForm()
    result = None
    classification_data = None
    extension_warning = None

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question']
            
            start_time = time.time()
            file_path = uploaded.file.path if uploaded.file else None
            
            if file_path and os.path.exists(file_path):
                logger.info(f"Fichier trouvé: {file_path}")
            else:
                logger.warning(f"Fichier non trouvé: {file_path}")
            
            # Classification réelle P3
            classifier = ModalityClassifier()
            classification = classifier.classify(file_path)
            
            # Détection extension trompeuse
            extension = os.path.splitext(uploaded.original_filename)[1].lower()
            real_modality = classification.modality
            
            REALLY_TROMPEUR_CASES = [
                ('.pdf', 'image'), ('.pdf', 'video'), ('.pdf', 'structured'),
                ('.jpg', 'document'), ('.jpeg', 'document'), ('.png', 'document'),
                ('.gif', 'document'), ('.csv', 'image'), ('.json', 'image'),
                ('.doc', 'image'), ('.docx', 'image'), ('.txt', 'image'),
            ]
            
            is_really_trompeur = (extension, real_modality) in REALLY_TROMPEUR_CASES
            
            if is_really_trompeur and real_modality != 'unknown':
                correct_ext = {
                    'image': '.png ou .jpg',
                    'document': '.pdf ou .doc',
                    'structured': '.csv',
                    'video': '.mp4'
                }.get(real_modality, '')
                extension_warning = f"Votre fichier '{uploaded.original_filename}' a l'extension '{extension}' mais son contenu réel est {real_modality}. L'extension recommandée est {correct_ext}."
                messages.warning(request, f"⚠️ {extension_warning}")
            else:
                extension_warning = None
            
            # Extraction du texte
            extracted_text = uploaded.extracted_text or ""
            if not extracted_text and file_path and file_path.lower().endswith('.pdf'):
                extracted_text = extract_pdf_text(file_path)
                if extracted_text:
                    uploaded.extracted_text = extracted_text
                    uploaded.save()
                    logger.info(f"Texte extrait: {len(extracted_text)} caractères")
            
            # 🔥 LOG pour l'image
            if classification.modality == "image":
                logger.info(f"=== IMAGE DEBUG ===")
                logger.info(f"file_path: {file_path}")
                logger.info(f"uploaded.file.path: {uploaded.file.path if uploaded.file else None}")
            
            # Construire parsed_content
            parsed_content = {
                "type": classification.modality,
                "text": extracted_text,
                "file_path": file_path,
                "image_path": file_path if classification.modality == "image" else None,
                "data": {}
            }
            
            try:
                routing_result = router.process(parsed_content, question_text)
                
                answer = routing_result.answer
                confidence = routing_result.confidence
                fallback_used = routing_result.fallback_used
                fallback_method = routing_result.fallback_method if fallback_used else ""
                model_used = "llama3.2"
                
                classification_data = {
                    'modality': classification.modality,
                    'confidence': int(classification.confidence * 100),
                    'method': classification.method,
                    'mime': classification.mime,
                    'fallback_used': routing_result.fallback_used,
                    'fallback_method': routing_result.fallback_method if routing_result.fallback_used else None,
                    'extension_mismatch': extension_warning is not None,
                    'correct_extension': {'image': 'png/jpg', 'document': 'pdf/doc', 'structured': 'csv'}.get(classification.modality, '')
                }
                
            except Exception as e:
                logger.error(f"Erreur routeur: {e}")
                answer = f"Erreur: {str(e)}"
                confidence = 0.0
                fallback_used = True
                fallback_method = "error"
                model_used = "none"
                classification_data = None
            
            processing_time = time.time() - start_time
            
            query = QueryResponse.objects.create(
                uploaded_file=uploaded,
                question=question_text,
                answer=answer,
                confidence=confidence,
                model_used=model_used,
                processing_time=processing_time,
                is_fallback=fallback_used,
                fallback_reason=fallback_method,
            )
            result = query
            
            if confidence >= 0.8:
                messages.success(request, f"✅ Réponse fiable ({confidence:.0%})")
            elif confidence >= 0.4:
                messages.warning(request, f"⚠️ Réponse à vérifier ({confidence:.0%})")
            else:
                messages.error(request, f"❌ Réponse peu fiable ({confidence:.0%})")

    previous_queries = uploaded.responses.all()[:10]
    
    return render(request, 'pipeline/question.html', {
        'uploaded': uploaded,
        'form': form,
        'result': result,
        'previous_queries': previous_queries,
        'classification': classification_data,
        'extension_warning': extension_warning,
    })


def result_view(request, query_id):
    query = get_object_or_404(QueryResponse, pk=query_id)
    return render(request, 'pipeline/result.html', {
        'query': query,
        'uploaded': query.uploaded_file,
    })