# apps/authentication/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # CU-01: Registrarse en el Sistema
    path('register/', views.register_user, name='register'),
    
    # CU-02: Iniciar Sesión
    path('login/', views.login_user, name='login'),
    
    # CU-03: Cerrar Sesión
    path('logout/', views.logout_user, name='logout'),
    
    # CU-04: Recuperar Contraseña
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Cambiar contraseña (parte de CU-05)
    path('change-password/', views.change_password, name='change_password'),
    
    # Obtener perfil del usuario autenticado
    path('profile/', views.user_profile, name='user_profile'),
]