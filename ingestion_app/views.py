# ingestion_app/views.py
import os
import logging
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import UploadedFile, ParsedMetadata, QueryResponse
from .parsers import run_parsing_pipeline

logger = logging.getLogger(__name__)


def index(request):
    """Page d'accueil ingestion"""
    recent_files = UploadedFile.objects.all()[:5]
    return render(request, 'ingestion/index.html', {
        'recent_files': recent_files,
    })


def upload_file(request):
    """Upload et traitement d'un fichier"""
    if request.method != 'POST':
        return redirect('ingestion_index')
    
    uploaded_file_obj = request.FILES.get('file')
    question = request.POST.get('question', '')
    
    if not uploaded_file_obj:
        messages.error(request, "Aucun fichier sélectionné")
        return redirect('ingestion_index')
    
    # Détection basique de la modalité par extension
    ext = Path(uploaded_file_obj.name).suffix.lower()
    document_exts = {'.pdf', '.docx', '.doc', '.txt'}
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    structured_exts = {'.csv', '.json', '.xlsx', '.xls'}
    
    if ext in document_exts:
        modality = 'document'
    elif ext in image_exts:
        modality = 'image'
    elif ext in structured_exts:
        modality = 'structured'
    else:
        modality = 'unknown'
    
    db_file = UploadedFile(
        original_filename=uploaded_file_obj.name,
        file_size=uploaded_file_obj.size,
        modality=modality,
        extraction_status='processing',
    )
    db_file.file = uploaded_file_obj
    db_file.save()
    
    file_path = db_file.file.path
    
    try:
        result = run_parsing_pipeline(file_path, uploaded_file_obj.name)
        
        db_file.extraction_status = 'done' if result['success'] else 'error'
        db_file.mime_type = result.get('mime_type', '')
        db_file.modality = result.get('modality', modality)
        db_file.extracted_text = result.get('extracted_text', '')
        db_file.processed_at = timezone.now()
        
        extra = result.get('extra', {})
        if db_file.modality == 'document':
            db_file.page_count = extra.get('page_count')
            db_file.word_count = extra.get('word_count')
        elif db_file.modality == 'image':
            db_file.image_width = extra.get('width')
            db_file.image_height = extra.get('height')
        elif db_file.modality == 'structured':
            db_file.row_count = extra.get('row_count')
            db_file.column_count = extra.get('column_count')
            cols = extra.get('columns', [])
            db_file.columns_list = ', '.join(str(c) for c in cols)
        
        if result.get('errors'):
            db_file.extraction_error = '\n'.join(result['errors'])
        
        db_file.save()
        
        # Sauvegarder les métadonnées
        for key, value in result.get('metadata', {}).items():
            if value:
                ParsedMetadata.objects.create(uploaded_file=db_file, key=key, value=str(value))
        
        for warning in result.get('warnings', []):
            messages.warning(request, warning)
        
        if result['success']:
            messages.success(request, f"✅ Fichier '{uploaded_file_obj.name}' traité avec succès !")
        else:
            messages.error(request, f"❌ Erreur : {'; '.join(result['errors'])}")
            
    except Exception as e:
        logger.exception(f"Erreur pipeline pour {uploaded_file_obj.name}")
        db_file.extraction_status = 'error'
        db_file.extraction_error = str(e)
        db_file.save()
        messages.error(request, f"Erreur inattendue : {str(e)}")
    
    url = reverse('file_detail', args=[db_file.pk])
    if question:
        import urllib.parse
        url += f"?question={urllib.parse.quote(question)}"
    return redirect(url)


def file_detail(request, pk):
    """Détail d'un fichier uploadé"""
    db_file = get_object_or_404(UploadedFile, pk=pk)
    question = request.GET.get('question', '').strip()
    metadata = db_file.metadata.all()
    ai_response = None
    classification_data = None
    history = db_file.responses.all()[:10]
    
    if question and db_file.extraction_status == 'done':
        # Vérifier le cache
        cached = db_file.responses.filter(question=question).first()
        if cached:
            ai_response = cached
            classification_data = {
                'modality': db_file.modality,
                'confidence': 98,
                'method': 'cache',
                'mime': db_file.mime_type,
            }
        else:
            try:
                from .router import route_and_answer
                result = route_and_answer(db_file, question)
                
                ai_response = QueryResponse.objects.create(
                    uploaded_file=db_file,
                    question=question,
                    answer=result.answer,
                    confidence=result.confidence,
                    model_used=result.model_used,
                    processing_time=result.processing_time,
                    is_fallback=result.fallback_used,
                    fallback_reason=result.fallback_reason,
                )
                
                classification_data = {
                    'modality': result.modality,
                    'confidence': result.classification_confidence,
                    'method': result.classification_method,
                    'mime': result.mime_type,
                }
                
                if result.confidence >= 0.8:
                    messages.success(request, f"✅ Réponse fiable ({result.confidence_percent}%)")
                elif result.confidence >= 0.4:
                    messages.warning(request, f"⚠️ Réponse à vérifier ({result.confidence_percent}%)")
                else:
                    messages.error(request, f"❌ Réponse peu fiable ({result.confidence_percent}%)")
                    
            except Exception as e:
                logger.exception("Erreur lors de l'appel IA")
                messages.error(request, f"Erreur IA : {str(e)}")
    
    return render(request, 'ingestion/file_detail.html', {
        'db_file': db_file,
        'question': question,
        'metadata': metadata,
        'ai_response': ai_response,
        'classification': classification_data,
        'history': history,
        'text_preview': db_file.extracted_text[:800] if db_file.extracted_text else "Aucun texte extrait",
    })


def file_list(request):
    """Liste des fichiers uploadés"""
    files = UploadedFile.objects.all()
    return render(request, 'ingestion/file_list.html', {'files': files})


@require_POST
def delete_file(request, pk):
    """Supprimer un fichier"""
    db_file = get_object_or_404(UploadedFile, pk=pk)
    filename = db_file.original_filename
    if db_file.file and os.path.exists(db_file.file.path):
        os.remove(db_file.file.path)
    db_file.delete()
    messages.success(request, f"Fichier '{filename}' supprimé.")
    return redirect('file_list')


def api_file_info(request, pk):
    """API pour les infos d'un fichier"""
    db_file = get_object_or_404(UploadedFile, pk=pk)
    data = {
        'id': db_file.pk,
        'original_filename': db_file.original_filename,
        'modality': db_file.modality,
        'mime_type': db_file.mime_type,
        'file_size': db_file.file_size,
        'extraction_status': db_file.extraction_status,
        'extracted_text': db_file.extracted_text,
        'uploaded_at': db_file.uploaded_at.isoformat(),
        'page_count': db_file.page_count,
        'word_count': db_file.word_count,
        'image_width': db_file.image_width,
        'image_height': db_file.image_height,
        'row_count': db_file.row_count,
        'column_count': db_file.column_count,
        'columns_list': db_file.columns_list,
    }
    return JsonResponse(data)


def ollama_status(request):
    """Page de statut Ollama"""
    from .ai_models import get_ollama_status, OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_VISION
    status = get_ollama_status()
    return render(request, 'ingestion/ollama_status.html', {
        'status': status,
        'ollama_url': OLLAMA_BASE_URL,
        'ollama_model': OLLAMA_MODEL,
        'ollama_vision': OLLAMA_VISION,
    })