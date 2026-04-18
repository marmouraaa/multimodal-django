# ingestion_app/models.py
import os
from django.db import models
from django.utils import timezone


class UploadedFile(models.Model):
    """Modèle pour stocker les fichiers uploadés"""
    
    MODALITY_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('structured', 'Données structurées'),
        ('unknown', 'Inconnu'),
    ]
    
    EXTRACTION_STATUS = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('done', 'Terminé'),
        ('error', 'Erreur'),
    ]
    
    # Fichier
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    
    # Détection
    mime_type = models.CharField(max_length=100, blank=True)
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES, default='unknown')
    
    # Extraction
    extraction_status = models.CharField(max_length=20, choices=EXTRACTION_STATUS, default='pending')
    extracted_text = models.TextField(blank=True)
    extraction_error = models.TextField(blank=True)
    
    # Dates
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Métadonnées documents
    page_count = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    
    # Métadonnées images
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    image_mode = models.CharField(max_length=50, blank=True)
    
    # Métadonnées structurées
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    columns_list = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.modality})"
    
    def get_file_size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def get_modality_display(self):
        return dict(self.MODALITY_CHOICES).get(self.modality, 'Inconnu')


class ParsedMetadata(models.Model):
    """Métadonnées extraites du fichier"""
    
    uploaded_file = models.ForeignKey(
        UploadedFile, 
        on_delete=models.CASCADE, 
        related_name='metadata'
    )
    key = models.CharField(max_length=100)
    value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['key']
        unique_together = ['uploaded_file', 'key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class QueryResponse(models.Model):
    """Modèle pour stocker les questions et réponses"""
    
    uploaded_file = models.ForeignKey(
        UploadedFile, 
        on_delete=models.CASCADE, 
        related_name='responses'
    )
    question = models.TextField()
    answer = models.TextField()
    confidence = models.FloatField(default=0.0)
    model_used = models.CharField(max_length=100, blank=True)
    processing_time = models.FloatField(default=0.0)
    is_fallback = models.BooleanField(default=False)
    fallback_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."
    
    def confidence_percent(self):
        return int(self.confidence * 100)
    
    def confidence_level(self):
        if self.confidence >= 0.8:
            return 'high'
        elif self.confidence >= 0.4:
            return 'medium'
        return 'low'