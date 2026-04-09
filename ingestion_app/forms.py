import os

from django import forms


SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.csv', '.json', '.xlsx', '.xls',
}


class FileUploadForm(forms.Form):
    """
    Formulaire d'upload de fichier.

    Utilisé dans : templates/pipeline/home.html
    Vue associée : views.home()

   
    """
    file = forms.FileField(
        label="Choisir un fichier",
        help_text="Formats acceptés : PDF, DOCX, TXT, JPG, PNG, CSV, JSON, XLSX",
        widget=forms.ClearableFileInput(attrs={
            'class': 'glass-input',   # Classe CSS personnalisée (style.css)
            'id': 'file-input',       # ID utilisé par le JavaScript (app.js)
            'accept': '.pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.gif,.bmp,.webp,.csv,.json,.xlsx,.xls',
        })
    )

    def clean_file(self):
        """
        Validation personnalisée du fichier uploadé.
        Appelée automatiquement par Django lors de form.is_valid().
        """
        file = self.cleaned_data.get('file')
        if file:
            # Vérifier la taille (max 10 Mo)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Le fichier est trop volumineux (max 10 Mo).")

            # Vérifier que l'extension est supportée
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                raise forms.ValidationError(
                    f"Format non supporté ({ext}). "
                    f"Formats acceptés : {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                )
        return file


class QuestionForm(forms.Form):
    """
    Utilisé dans : templates/pipeline/question.html
    Vue associée : views.question_view()
    
    """
    question = forms.CharField(
        label="Votre question",
        widget=forms.Textarea(attrs={
            'class': 'glass-input w-100',  # Classe CSS personnalisée
            'rows': 3,                     
            'placeholder': 'Posez votre question sur le fichier...',
            'id': 'question-input',         # ID utilisé par le JavaScript
        }),
        max_length=1000,
    )
