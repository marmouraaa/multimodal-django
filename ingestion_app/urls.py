from django.urls import path
from . import views

urlpatterns = [
    # Page d'accueil : formulaire d'upload de fichier
    path('', views.home, name='home'),

    # Page de question : poser une question sur un fichier uploadé
    # <int:file_id> = l'identifiant du fichier dans la base de données
    path('question/<int:file_id>/', views.question_view, name='question'),

    # Page de résultat : détail d'une réponse IA spécifique
    # <int:query_id> = l'identifiant de la question-réponse en BDD
    path('result/<int:query_id>/', views.result_view, name='result'),

   
]
