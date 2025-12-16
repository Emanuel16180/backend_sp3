# apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, PatientProfile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'user_type')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = (
        'email', 'first_name', 'last_name', 'user_type', 
        'ci', 'phone', 'is_active', 'is_staff', 'date_joined'
    )
    list_filter = ('user_type', 'is_active', 'is_staff', 'gender')
    search_fields = ('email', 'first_name', 'last_name', 'ci', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        ('Información Personal', {
            'fields': (
                'first_name', 'last_name', 'ci', 'phone', 
                'gender', 'date_of_birth', 'address', 'profile_picture'
            )
        }),
        ('Configuración de Cuenta', {
            'fields': ('user_type', 'is_verified', 'is_active_patient')
        }),
        ('Permisos', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 
                'groups', 'user_permissions'
            ),
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'user_type',
                'password1', 'password2'
            ),
        }),
        ('Información Adicional (Opcional)', {
            'classes': ('collapse',),
            'fields': (
                'ci', 'phone', 'gender', 'date_of_birth', 'address'
            ),
        }),
    )

class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Paciente'
    fk_name = 'user'

class PatientProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'emergency_contact_name', 'emergency_contact_phone',
        'occupation', 'profile_completed'
    )
    list_filter = ('education_level', 'profile_completed')
    search_fields = (
        'user__first_name', 'user__last_name', 'user__email',
        'emergency_contact_name', 'occupation'
    )
    readonly_fields = ('profile_completed',)

# Registrar los modelos en el admin por defecto
# NO registrar en el admin por defecto - se registran en admin sites específicos
# admin.site.register(CustomUser, CustomUserAdmin)
# admin.site.register(PatientProfile, PatientProfileAdmin)

# Registrar también en el tenant admin
from config.tenant_admin import tenant_admin_site
tenant_admin_site.register(CustomUser, CustomUserAdmin)
tenant_admin_site.register(PatientProfile, PatientProfileAdmin)

# Personalizar títulos del admin
admin.site.site_header = "Centro de Salud Mental - Administración"
admin.site.site_title = "Admin Centro Salud Mental"
admin.site.index_title = "Gestión del Sistema"