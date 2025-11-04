# apps/clinical_history/urls.py

from django.urls import path
from . import views

urlpatterns = [
    
    path('objectives/', views.ObjectiveCreateView.as_view(), name='objective-create'),
    path('objectives/my/', views.MyObjectivesListView.as_view(), name='objective-list-my'),
    path('objectives/my/stats/', views.get_patient_stats_view, name='objective-stats-my'),
    path('tasks/<int:task_id>/complete/', views.complete_task_view, name='task-complete'),
    
    
    path('mood-journal/', views.MoodJournalView.as_view(), name='mood-journal-list-create'),
    path('mood-journal/today/', views.TodayMoodJournalView.as_view(), name='mood-journal-today'),

    # --- (Tus URLs existentes no cambian) ---
    path('my-documents/', views.MyDocumentsListView.as_view(), name='my-documents'),
    path('my-patients/', views.MyPastPatientsListView.as_view(), name='my-past-patients'),
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('documents/<int:pk>/download/', views.DownloadDocumentView.as_view(), name='document-download'),

    # --- 👇 AÑADE ESTA NUEVA LÍNEA 👇 ---
    path('patient/<int:patient_id>/', views.ClinicalHistoryDetailView.as_view(), name='clinical-history-detail'),
    path('triage/', views.InitialTriageView.as_view(), name='initial-triage'),
]