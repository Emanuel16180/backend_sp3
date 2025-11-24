# apps/clinical_history/urls.py

from django.urls import path
from . import views

urlpatterns = [
    
    # --- 👇 RUTAS MANUALES PARA CU-45 (Psiquiatra) 👇 ---
    
    # Endpoint para que el Psiquiatra liste recetas de UN paciente o cree una NUEVA receta
    # GET, POST -> /api/clinical-history/patient/<int:patient_id>/prescriptions/
    path(
        'patient/<int:patient_id>/prescriptions/', 
        views.PrescriptionViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }), 
        name='patient-prescription-list'
    ),
    
    # Endpoint para que el Psiquiatra obtenga, actualice o borre UNA receta específica
    # GET, PUT, PATCH, DELETE -> /api/clinical-history/prescriptions/<int:pk>/
    # (Usamos <int:pk> para la receta, no necesitamos el patient_id en la URL aquí)
    path(
        'prescriptions/<int:pk>/', 
        views.PrescriptionViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), 
        name='prescription-detail'
    ),

    # --- 👇 RUTA MANUAL PARA CU-45 (Paciente) 👇 ---
    
    # Endpoint para que el PACIENTE vea SUS recetas
    # GET -> /api/clinical-history/prescriptions/my-prescriptions/
    path(
        'prescriptions/my-prescriptions/', 
         views.MyPrescriptionsListView.as_view(), 
         name='my-prescriptions'
    ),

    # --- 👇 RUTAS PARA RECORDATORIOS DE MEDICAMENTOS 👇 ---
    
    # CRUD completo de recordatorios
    path(
        'medication-reminders/',
        views.MedicationReminderViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='medication-reminder-list'
    ),
    path(
        'medication-reminders/<int:pk>/',
        views.MedicationReminderViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='medication-reminder-detail'
    ),
    
    # Vista simplificada para pacientes
    path(
        'medication-reminders/my-reminders/',
        views.MyMedicationRemindersView.as_view(),
        name='my-medication-reminders'
    ),

    # --- (Tus URLs existentes se quedan igual) ---
    path('objectives/', views.ObjectiveCreateView.as_view(), name='objective-create'),
    path('objectives/my/', views.MyObjectivesListView.as_view(), name='objective-list-my'),
    path('objectives/my/stats/', views.get_patient_stats_view, name='objective-stats-my'),
    path('tasks/<int:task_id>/complete/', views.complete_task_view, name='task-complete'),
    
    
    path('mood-journal/', views.MoodJournalView.as_view(), name='mood-journal-list-create'),
    path('mood-journal/today/', views.TodayMoodJournalView.as_view(), name='mood-journal-today'),

    path('my-documents/', views.MyDocumentsListView.as_view(), name='my-documents'),
    path('my-patients/', views.MyPastPatientsListView.as_view(), name='my-past-patients'),
    path('documents/upload/', views.DocumentUploadView.as_view(), name='document-upload'),
    path('documents/<int:pk>/download/', views.DownloadDocumentView.as_view(), name='document-download'),

    path('patient/<int:patient_id>/', views.ClinicalHistoryDetailView.as_view(), name='clinical-history-detail'),
    
    path('triage/', views.InitialTriageView.as_view(), name='initial-triage'),
]