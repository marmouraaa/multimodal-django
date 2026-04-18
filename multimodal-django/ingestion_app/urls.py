# ingestion_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='ingestion_index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('file/<int:pk>/', views.file_detail, name='file_detail'),
    path('files/', views.file_list, name='file_list'),
    path('delete/<int:pk>/', views.delete_file, name='delete_file'),
    path('api/file/<int:pk>/', views.api_file_info, name='api_file_info'),
    path('ollama-status/', views.ollama_status, name='ollama_status'),
]