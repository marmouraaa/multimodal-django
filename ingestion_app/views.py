from django.shortcuts import render

import os
import logging
import mimetypes

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import FileUploadForm, QuestionForm
from .models import UploadedFile, QueryResponse

logger = logging.getLogger('pipeline')


# DÉTECTION DE MODALITÉ (temporaire - sera remplacé par  Amira)

def detect_modality(filename):
    """
    Détecte la modalité (type) d'un fichier à partir de son extension.

    Retourne : 'document', 'image', 'structured' ou 'unknown'

    NOTE : Cette version est simplifiée. Personne 3 (Amira) doit créer
    classifier.py avec détection MIME + score de confiance.
    """
    ext = os.path.splitext(filename)[1].lower()

    # Extensions pour chaque modalité
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


# =============================================================================
# VUE 1 : PAGE D'ACCUEIL (Upload de fichier)
# =============================================================================
# URL : / (racine du site)
# Template : templates/pipeline/home.html
# Méthodes HTTP : GET (afficher le formulaire) / POST (recevoir le fichier)
# =============================================================================
def home(request):
    """
    Page d'accueil avec le formulaire d'upload.

   
    """
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Récupérer le fichier envoyé par l'utilisateur
            uploaded_file_obj = request.FILES['file']

            # Détecter le type MIME (ex: application/pdf, image/jpeg)
            mime_type, _ = mimetypes.guess_type(uploaded_file_obj.name)
            mime_type = mime_type or 'application/octet-stream'

            # Créer l'enregistrement en base de données
            uploaded = UploadedFile(
                file=uploaded_file_obj,                           # Le fichier lui-même
                original_filename=uploaded_file_obj.name,         # Nom d'origine
                file_size=uploaded_file_obj.size,                 # Taille en octets
                modality=detect_modality(uploaded_file_obj.name), # Type détecté
                mime_type=mime_type,                               # Type MIME
            )
            uploaded.save()  # Sauvegarde le fichier sur le disque + en BDD

           

            # Message de succès affiché à l'utilisateur
            messages.success(
                request,
                f"Fichier \"{uploaded.original_filename}\" uploadé avec succès ! "
                f"Type détecté : {uploaded.get_modality_display()}"
            )

            # Rediriger vers la page de question pour ce fichier
            return redirect('question', file_id=uploaded.pk)
    else:
        form = FileUploadForm()

    # Récupérer les 10 derniers fichiers pour l'affichage
    recent_files = UploadedFile.objects.all()[:10]

    return render(request, 'pipeline/home.html', {
        'form': form,
        'recent_files': recent_files,
    })


# =============================================================================
# VUE 2 : PAGE DE QUESTION (Poser une question sur un fichier)
# =============================================================================

def question_view(request, file_id):
    """
    Page pour poser des questions sur un fichier uploadé.

  
    """
    # Récupérer le fichier uploadé (erreur 404 si pas trouvé)
    uploaded = get_object_or_404(UploadedFile, pk=file_id)
    form = QuestionForm()
    result = None  # Contiendra la réponse de l'IA

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question_text = form.cleaned_data['question']

            # ============================================================
            # TODO [ Amine] + [ Amira] : INTÉGRER L'IA ICI
            # ============================================================
            # Remplacer le bloc ci-dessous par l'appel au vrai pipeline.
            # ============================================================

            # --- DÉBUT PLACEHOLDER (à remplacer) ---
            query = QueryResponse.objects.create(
                uploaded_file=uploaded,
                question=question_text,
                answer="[En attente de l'intégration des modèles IA par l'équipe backend]",
                confidence=0.0,
                model_used="aucun",
                processing_time=0.0,
                is_fallback=False,
                fallback_reason="",
            )
            result = query

            messages.info(
                request,
                "Question enregistrée. L'intégration IA sera ajoutée par l'équipe."
            )
            # --- FIN PLACEHOLDER ---

    # Récupérer les questions précédentes pour ce fichier
    previous_queries = uploaded.queries.all()[:10]

    return render(request, 'pipeline/question.html', {
        'uploaded': uploaded,          # Le fichier uploadé
        'form': form,                  # Le formulaire de question
        'result': result,              # La dernière réponse (ou None)
        'previous_queries': previous_queries,  # Historique Q&A
    })


# =============================================================================
# VUE 3 : PAGE DE RÉSULTAT (Détail d'une réponse)
# =============================================================================


def result_view(request, query_id):
   
    query = get_object_or_404(QueryResponse, pk=query_id)
    return render(request, 'pipeline/result.html', {
        'query': query,                    # L'objet question-réponse
        'uploaded': query.uploaded_file,   # Le fichier associé
    })



