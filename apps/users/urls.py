# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # CU-05: Gestionar Perfil Personal
    path('profile/', views.user_profile_detail, name='user_profile_detail'),
    
    # CU-05: Gestionar Perfil de Paciente
    path('patient-profile/', views.patient_profile_detail, name='patient_profile_detail'),
    
    # CU-05: Actualizar perfil completo
    path('complete-profile/', views.update_complete_profile, name='update_complete_profile'),
    
    # Eliminar cuenta
    path('delete-account/', views.delete_account, name='delete_account'),
]