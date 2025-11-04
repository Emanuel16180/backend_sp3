# apps/appointments/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
# Importa la nueva vista de notas
from apps.clinical_history.views import SessionNoteViewSet 

# El router principal
router = DefaultRouter()
router.register(r'appointments', views.AppointmentViewSet, basename='appointment')
router.register(r'availability', views.PsychologistAvailabilityViewSet, basename='availability')

urlpatterns = [
    # Custom endpoints - MUST come FIRST (specific routes before generic ones)
    path('search-psychologists/', views.search_available_psychologists, name='search-psychologists'),
    path('psychologist/<int:psychologist_id>/schedule/', views.get_psychologist_schedule, name='psychologist-schedule'),
    
    # Rutas anidadas para notas de sesión
    path('appointments/<int:appointment_pk>/note/', SessionNoteViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='appointment-note-list'),
    path('appointments/<int:appointment_pk>/note/<int:pk>/', SessionNoteViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='appointment-note-detail'),
    
    # ViewSets - Generic router patterns come LAST
    path('', include(router.urls)),
]