# pipeline/forms.py
import os
from django import forms


SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.csv', '.json', '.xlsx', '.xls',
}


class FileUploadForm(forms.Form):
    """Formulaire d'upload de fichier"""
    
    file = forms.FileField(
        label="Choisir un fichier",
        help_text="Formats acceptés : PDF, DOCX, TXT, JPG, PNG, CSV, JSON, XLSX",
        widget=forms.ClearableFileInput(attrs={
            'class': 'glass-input',
            'id': 'file-input',
            'accept': '.pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.gif,.bmp,.webp,.csv,.json,.xlsx,.xls',
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Taille max 10 Mo
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier est trop volumineux (max 10 Mo).")
            
            # Vérifier l'extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise forms.ValidationError(
                    f"Format non supporté ({ext}). "
                    f"Formats acceptés : {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                )
        return file


class QuestionForm(forms.Form):
    """Formulaire pour poser une question"""
    
    question = forms.CharField(
        label="Votre question",
        widget=forms.Textarea(attrs={
            'class': 'glass-input w-100',
            'rows': 3,
            'placeholder': 'Posez votre question sur le fichier...',
            'id': 'question-input',
        }),
        max_length=1000,
    )