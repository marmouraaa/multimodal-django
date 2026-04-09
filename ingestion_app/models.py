import os
from django.db import models
from django.utils import timezone


class UploadedFile(models.Model):
    """
    Modèle pour stocker les fichiers uploadés par l'utilisateur.

   
    """

    # Choix possibles pour le type de fichier
    MODALITY_CHOICES = [
        ('document', 'Document'),           # PDF, DOCX, TXT
        ('image', 'Image'),                 # JPG, PNG, etc.
        ('structured', 'Données structurées'),  # CSV, JSON, Excel
        ('unknown', 'Inconnu'),             # Type non reconnu
    ]

    # --- Champs de la table ---

    # Le fichier lui-même (sauvegardé dans media/uploads/)
    file = models.FileField(upload_to='uploads/')

    # Nom original du fichier (ex: "contrat_location.pdf")
    original_filename = models.CharField(max_length=255)

    # Taille du fichier en octets
    file_size = models.PositiveIntegerField(help_text="Taille en octets")

    # Type MIME détecté (ex: "application/pdf", "image/jpeg")
    mime_type = models.CharField(max_length=100, blank=True)

    # Modalité détectée par le classifieur (P3 - Amira)
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES, default='unknown')

    # Date et heure de l'upload
    uploaded_at = models.DateTimeField(default=timezone.now)

  
    extracted_content = models.TextField(blank=True, help_text="Contenu extrait du fichier")

    # Métadonnées supplémentaires en JSON (taille image, nb pages, etc.)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-uploaded_at']  # Les plus récents en premier
        verbose_name = "Fichier uploadé"
        verbose_name_plural = "Fichiers uploadés"

    def __str__(self):
        """Affichage dans l'admin Django et le shell."""
        return f"{self.original_filename} ({self.modality})"

    @property
    def extension(self):
        """Retourne l'extension du fichier (ex: '.pdf', '.jpg')."""
        return os.path.splitext(self.original_filename)[1].lower()


class QueryResponse(models.Model):
    """
    Modèle pour stocker les questions et réponses de l'IA.

    Correspond aux ÉTAPES 4-7 du pipeline (Routage → IA → Fallback → Affichage).
    Chaque réponse inclut un score de confiance utilisé pour l'affichage.
    """

    # --- Champs de la table ---

    # Lien vers le fichier uploadé (clé étrangère)
    # related_name='queries' permet d'accéder aux questions depuis le fichier :
    #   uploaded_file.queries.all()  → toutes les questions de ce fichier
    uploaded_file = models.ForeignKey(
        UploadedFile, on_delete=models.CASCADE, related_name='queries'
    )

    # La question posée par l'utilisateur
    question = models.TextField()

    # La réponse générée par l'IA (P1 - Amine)
    answer = models.TextField()

    # Score de confiance entre 0.0 et 1.0 (P3 - Amira)
    # >= 0.8 → Vert (fiable)
    # >= 0.4 → Orange (moyen, à vérifier)
    # < 0.4  → Rouge (faible, incertain)
    confidence = models.FloatField(default=0.0, help_text="Score de confiance (0 à 1)")

    # Nom du modèle IA utilisé (ex: "Gemini Flash 2 (texte)")
    model_used = models.CharField(max_length=100, blank=True)

    # Temps de traitement en secondes
    processing_time = models.FloatField(default=0.0, help_text="Temps de traitement en secondes")

    # Est-ce que le fallback a été déclenché ? (P3 - Amira)
    is_fallback = models.BooleanField(default=False)

    # Raison du fallback (ex: "Confiance trop faible (0.32 < 0.6)")
    fallback_reason = models.CharField(max_length=255, blank=True)

    # Date et heure de la réponse
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']  # Les plus récentes en premier
        verbose_name = "Question-Réponse"
        verbose_name_plural = "Questions-Réponses"

    def __str__(self):
        return f"Q: {self.question[:50]}..."

    # --- Propriétés utilisées dans les templates (P4 - Mariem) ---

    @property
    def confidence_level(self):
        """
        Retourne le niveau de confiance en texte.
        Utilisé dans les templates : {% if query.confidence_level == 'high' %}
        """
        if self.confidence >= 0.8:
            return 'high'    # Vert - fiable
        elif self.confidence >= 0.4:
            return 'medium'  # Orange - moyen
        return 'low'         # Rouge - faible

    @property
    def confidence_color(self):
        """
        Retourne la classe Bootstrap pour la couleur.
        Utilisé dans les templates : class="bg-{{ query.confidence_color }}"
        """
        if self.confidence >= 0.8:
            return 'success'   # Vert Bootstrap
        elif self.confidence >= 0.4:
            return 'warning'   # Orange Bootstrap
        return 'danger'        # Rouge Bootstrap

    @property
    def confidence_percent(self):
        """
        Retourne le score de confiance en pourcentage (0-100).
        Utilisé dans les templates : style="width: {{ query.confidence_percent }}%"
        """
        return int(self.confidence * 100)
