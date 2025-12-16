# config/admin_site.py

from django.contrib import admin
from apps.tenants.models import Clinic, Domain, PublicUser
from apps.tenants.forms import PublicAdminAuthenticationForm

class PublicAdminSite(admin.AdminSite):
    """
    Admin site personalizado para el esquema público.
    Solo gestiona clínicas y dominios, sin logs ni funcionalidades complejas.
    """
    site_header = "Administración Global de Psico SAS"
    site_title = "Admin Global"
    index_title = "Gestión Centralizada de Clínicas"
    index_template = "admin/public_index.html"  # Usar nuestra plantilla personalizada
    
    # Le decimos que use nuestro formulario de login personalizado
    login_form = PublicAdminAuthenticationForm
    
    def index(self, request, extra_context=None):
        """
        Personalizar el dashboard principal con estadísticas reales
        """
        extra_context = extra_context or {}
        
        try:
            from django_tenants.utils import schema_context
            from apps.users.models import CustomUser
            
            # Obtener estadísticas de clínicas reales (excluyendo public)
            real_clinics = Clinic.objects.exclude(schema_name='public')
            total_clinics = real_clinics.count()
            total_domains = Domain.objects.count()
            active_domains = Domain.objects.filter(tenant__isnull=False).count()
            
            # Calcular usuarios totales de todas las clínicas reales
            total_users_real_clinics = 0
            total_patients = 0
            total_professionals = 0
            
            for clinic in real_clinics:
                try:
                    with schema_context(clinic.schema_name):
                        clinic_users = CustomUser.objects.count()
                        clinic_patients = CustomUser.objects.filter(user_type='patient').count()
                        clinic_professionals = CustomUser.objects.filter(user_type='professional').count()
                        
                        total_users_real_clinics += clinic_users
                        total_patients += clinic_patients
                        total_professionals += clinic_professionals
                except Exception:
                    pass
            
            # Agregar estadísticas al contexto
            extra_context.update({
                'total_clinics': total_clinics,
                'total_domains': total_domains,
                'active_domains': active_domains,
                'total_users_real_clinics': total_users_real_clinics,
                'total_patients': total_patients,
                'total_professionals': total_professionals,
            })
            
        except Exception as e:
            # En caso de error, mostrar valores por defecto
            extra_context.update({
                'total_clinics': 0,
                'total_domains': 0,
                'active_domains': 0,
                'total_users_real_clinics': 0,
                'total_patients': 0,
                'total_professionals': 0,
                'stats_error': str(e),
            })
        
        return super().index(request, extra_context)

class TenantAdminSite(admin.AdminSite):
    """
    Admin site específico para tenants individuales (clínicas).
    Muestra todas las funcionalidades normales de Django admin
    para gestionar usuarios, citas, chats, etc.
    SIN mostrar gestión de clínicas.
    """
    site_header = "Administración de Clínica"
    site_title = "Admin Clínica" 
    index_title = "Panel de Control"
    
    def each_context(self, request):
        """
        Personalizar el contexto para mostrar información del tenant actual
        """
        context = super().each_context(request)
        
        # Intentar obtener información del tenant actual
        if hasattr(request, 'tenant'):
            context['tenant_name'] = getattr(request.tenant, 'name', 'Clínica')
            context['site_header'] = f"Administración de {context['tenant_name']}"
        
        return context

# Instancias de los admin sites
public_admin_site = PublicAdminSite(name='public_admin')
tenant_admin_site = TenantAdminSite(name='tenant_admin')

# --- ADMIN CLASSES PARA PÚBLICO ---

class ClinicAdmin(admin.ModelAdmin):
    """Admin para gestionar clínicas con estadísticas dinámicas"""
    list_display = ('name', 'schema_name', 'get_user_count', 'get_primary_domain', 'created_on')
    search_fields = ('name', 'schema_name')
    readonly_fields = ('created_on',)
    list_filter = ('created_on',)
    
    def get_queryset(self, request):
        """Mostrar solo clínicas reales, excluyendo el schema público"""
        return super().get_queryset(request).exclude(schema_name='public')
    
    def get_user_count(self, obj):
        """Obtener el conteo real de usuarios para esta clínica"""
        try:
            from django_tenants.utils import schema_context
            from apps.users.models import CustomUser
            
            with schema_context(obj.schema_name):
                user_count = CustomUser.objects.count()
                patients = CustomUser.objects.filter(user_type='patient').count()
                professionals = CustomUser.objects.filter(user_type='professional').count()
                
            return f"{user_count} usuarios ({patients}P, {professionals}Pr)"
        except Exception:
            return "Error"
    
    get_user_count.short_description = "Usuarios"
    get_user_count.admin_order_field = 'name'
    
    def get_primary_domain(self, obj):
        """Obtener el dominio principal de la clínica"""
        try:
            primary_domain = Domain.objects.filter(tenant=obj, is_primary=True).first()
            if primary_domain:
                return f"{primary_domain.domain}"
            return "Sin dominio"
        except Exception:
            return "Error"
    
    get_primary_domain.short_description = "Dominio Principal"

class DomainAdmin(admin.ModelAdmin):
    """Admin para gestionar dominios"""
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain',)

class PublicUserAdmin(admin.ModelAdmin):
    """Admin simplificado para usuarios públicos"""
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('email',)
    
    fields = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser')

# --- REGISTRAR MODELOS SOLO EN ADMIN PÚBLICO ---
public_admin_site.register(Clinic, ClinicAdmin)
public_admin_site.register(Domain, DomainAdmin)
public_admin_site.register(PublicUser, PublicUserAdmin)

# --- REGISTRAR MODELOS EN ADMIN DE TENANTS ---
# Importar y registrar todos los modelos de las apps de tenants

# 1. Usuarios y Perfiles
try:
    from apps.users.models import CustomUser, PatientProfile
    from apps.users.admin import CustomUserAdmin, PatientProfileAdmin
    tenant_admin_site.register(CustomUser, CustomUserAdmin)
    tenant_admin_site.register(PatientProfile, PatientProfileAdmin)
except ImportError:
    pass

# 2. Profesionales
try:
    from apps.professionals.models import ProfessionalProfile, Specialization, WorkingHours, Review
    from apps.professionals.admin import ProfessionalProfileAdmin, SpecializationAdmin, ReviewAdmin
    tenant_admin_site.register(ProfessionalProfile, ProfessionalProfileAdmin)
    tenant_admin_site.register(Specialization, SpecializationAdmin)
    tenant_admin_site.register(WorkingHours)  # Sin admin personalizado
    tenant_admin_site.register(Review, ReviewAdmin)
except ImportError:
    pass

# 3. Citas
try:
    from apps.appointments.models import Appointment, PsychologistAvailability
    from apps.appointments.admin import AppointmentAdmin, PsychologistAvailabilityAdmin
    tenant_admin_site.register(Appointment, AppointmentAdmin)
    tenant_admin_site.register(PsychologistAvailability, PsychologistAvailabilityAdmin)
except ImportError:
    pass

# 4. Chat
try:
    from apps.chat.models import ChatMessage
    from apps.chat.admin import ChatMessageAdmin
    # ChatMessage ya se registra en su propio admin.py, pero lo agregamos aquí también
    if not tenant_admin_site.is_registered(ChatMessage):
        tenant_admin_site.register(ChatMessage, ChatMessageAdmin)
except ImportError:
    pass

# 5. Historia Clínica
try:
    from apps.clinical_history.models import SessionNote, ClinicalDocument
    from apps.clinical_history.admin import SessionNoteAdmin, ClinicalDocumentAdmin
    # Registrar en el admin de tenant (ya no están en admin por defecto)
    tenant_admin_site.register(SessionNote, SessionNoteAdmin)
    tenant_admin_site.register(ClinicalDocument, ClinicalDocumentAdmin)
except ImportError:
    pass