# pipeline/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('question/<int:file_id>/', views.question_view, name='question'),
    path('result/<int:query_id>/', views.result_view, name='result'),
]