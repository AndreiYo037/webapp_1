from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('file/<int:file_id>/', views.view_file, name='view_file'),
    path('files/', views.list_files, name='list_files'),
    path('flashcards/<int:set_id>/', views.view_flashcards, name='view_flashcards'),
    path('sets/', views.list_flashcard_sets, name='list_sets'),
    path('signup/', views.signup, name='signup'),
    path('health/', views.health_check, name='health_check'),
]

