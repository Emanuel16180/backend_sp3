# apps/tenants/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_tenants.utils import tenant_context, schema_context
from .models import Clinic, Domain
from .serializers import ClinicSerializer, ClinicCreateSerializer
import logging

logger = logging.getLogger(__name__)

class ClinicListCreateView(generics.ListCreateAPIView):
    """
    Vista para listar y crear clínicas.
    Solo disponible en el esquema público.
    """
    queryset = Clinic.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ClinicCreateSerializer
        return ClinicSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            clinic = serializer.save()
            # Devolver la respuesta con el serializer de lectura
            response_serializer = ClinicSerializer(clinic)
            return Response(
                response_serializer.data, 
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': f'Error creando la clínica: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class ClinicDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para obtener, actualizar y eliminar una clínica específica.
    """
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = [IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Verificar que no sea la clínica pública
        if instance.schema_name == 'public':
            return Response(
                {'error': 'No se puede eliminar el esquema público'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Eliminar dominios asociados
        Domain.objects.filter(tenant=instance).delete()
        
        # Eliminar la clínica (esto también eliminará el esquema)
        self.perform_destroy(instance)
        
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def global_admin_stats(request):
    """
    Endpoint para obtener estadísticas globales de todas las clínicas.
    Solo accesible desde el schema público por administradores globales.
    """
    # Verificar que estamos en el schema público
    try:
        current_schema = request.tenant.schema_name
        if current_schema != 'public':
            return Response(
                {'error': 'Este endpoint solo está disponible desde el admin global'}, 
                status=status.HTTP_403_FORBIDDEN
            )
    except AttributeError:
        return Response(
            {'error': 'No se pudo determinar el schema actual'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar que el usuario es un superuser o staff del schema público
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Permisos insuficientes para acceder a estadísticas globales'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Obtener todas las clínicas REALES (excluyendo el schema público)
        all_clinics = Clinic.objects.exclude(schema_name='public')
        total_clinics = all_clinics.count()
        
        # Obtener todos los dominios (incluyendo public para conteo total)
        total_domains = Domain.objects.count()
        active_domains = Domain.objects.filter(tenant__isnull=False).count()
        
        # Inicializar contadores globales SOLO para clínicas reales
        total_users_global = 0
        clinic_stats = []
        
        # Procesar cada clínica REAL para obtener estadísticas de usuarios
        for clinic in all_clinics:
            try:
                with schema_context(clinic.schema_name):
                    # Importar CustomUser dentro del contexto del schema
                    from apps.users.models import CustomUser
                    
                    # Contar usuarios en este tenant
                    total_users = CustomUser.objects.count()
                    patients = CustomUser.objects.filter(user_type='patient').count()
                    professionals = CustomUser.objects.filter(user_type='professional').count()
                    admins = CustomUser.objects.filter(user_type='admin').count()
                    
                # Fuera del contexto del schema, obtener dominios
                clinic_domains = Domain.objects.filter(tenant=clinic)
                domains_list = [domain.domain for domain in clinic_domains]
                primary_domain = clinic_domains.filter(is_primary=True).first()
                
                clinic_data = {
                    'id': clinic.id,
                    'name': clinic.name,
                    'schema_name': clinic.schema_name,
                    'created_on': clinic.created_on,
                    'total_users': total_users,
                    'patients': patients,
                    'professionals': professionals,
                    'admins': admins,
                    'domains': domains_list,
                    'primary_domain': primary_domain.domain if primary_domain else None,
                    'admin_url': f"http://{primary_domain.domain}:8000/admin/" if primary_domain else None,
                    'frontend_url': f"http://{primary_domain.domain}:3000" if primary_domain else None
                }
                
                clinic_stats.append(clinic_data)
                total_users_global += total_users
                
                logger.info(f"Estadísticas obtenidas para {clinic.name}: {total_users} usuarios")
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas para {clinic.name}: {str(e)}")
                # Agregar clínica con datos de error
                clinic_stats.append({
                    'id': clinic.id,
                    'name': clinic.name,
                    'schema_name': clinic.schema_name,
                    'created_on': clinic.created_on,
                    'total_users': 0,
                    'patients': 0,
                    'professionals': 0,
                    'admins': 0,
                    'domains': [],
                    'primary_domain': None,
                    'admin_url': None,
                    'frontend_url': None,
                    'error': f"Error: {str(e)}"
                })
        
        # Preparar respuesta con estadísticas globales
        response_data = {
            'system_status': 'active',
            'total_clinics': total_clinics,
            'total_domains': total_domains,
            'active_domains': active_domains,
            'total_users_global': total_users_global,
            'clinics': clinic_stats,
            'last_updated': request.tenant.created_on if hasattr(request.tenant, 'created_on') else None
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error en global_admin_stats: {str(e)}")
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clinic_detail_stats(request, clinic_id):
    """
    Obtener estadísticas detalladas de una clínica específica.
    """
    try:
        clinic = Clinic.objects.get(id=clinic_id)
        
        with schema_context(clinic.schema_name):
            # Importar modelos dentro del contexto
            from apps.users.models import CustomUser
            
            # Estadísticas básicas
            total_users = CustomUser.objects.count()
            patients = CustomUser.objects.filter(user_type='patient').count()
            professionals = CustomUser.objects.filter(user_type='professional').count()
            admins = CustomUser.objects.filter(user_type='admin').count()
            
            # Estadísticas avanzadas (opcional)
            try:
                from apps.appointments.models import Appointment
                from apps.professionals.models import ProfessionalProfile
                
                total_appointments = Appointment.objects.count()
                pending_appointments = Appointment.objects.filter(status='pending').count()
                confirmed_appointments = Appointment.objects.filter(status='confirmed').count()
                
                total_professionals_profiles = ProfessionalProfile.objects.count()
                verified_professionals = ProfessionalProfile.objects.filter(is_verified=True).count()
                
            except ImportError:
                total_appointments = 0
                pending_appointments = 0
                confirmed_appointments = 0
                total_professionals_profiles = 0
                verified_professionals = 0
            
            response_data = {
                'clinic': {
                    'id': clinic.id,
                    'name': clinic.name,
                    'schema_name': clinic.schema_name,
                    'created_on': clinic.created_on
                },
                'users': {
                    'total': total_users,
                    'patients': patients,
                    'professionals': professionals,
                    'admins': admins
                },
                'appointments': {
                    'total': total_appointments,
                    'pending': pending_appointments,
                    'confirmed': confirmed_appointments
                },
                'professionals': {
                    'total_profiles': total_professionals_profiles,
                    'verified': verified_professionals
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
    except Clinic.DoesNotExist:
        return Response(
            {'error': 'Clínica no encontrada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error en clinic_detail_stats: {str(e)}")
        return Response(
            {'error': f'Error interno: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ========== VISTAS PÚBLICAS PARA REGISTRO ==========

from rest_framework.permissions import AllowAny
from .serializers import TenantRegistrationSerializer, SubdomainCheckSerializer
from django.http import HttpResponse
from datetime import datetime

@api_view(['POST'])
@permission_classes([AllowAny])  # ⭐ Acceso público
def register_tenant(request):
    """
    Endpoint público para registro de nuevos tenants (clínicas).
    
    POST /api/public/register/
    Body: {
        "clinic_name": "Mi Clínica",
        "subdomain": "miclinica",
        "admin_email": "admin@miclinica.com",
        "admin_phone": "+34 600 000 000",  // opcional
        "address": "Calle Principal 123"    // opcional
    }
    
    Query params:
    ?download=true  -> Descarga archivo TXT con credenciales
    """
    serializer = TenantRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            result = serializer.save()
            
            # Verificar si se solicita descarga
            download = request.query_params.get('download', 'false').lower() == 'true'
            
            if download:
                # Generar archivo de texto con credenciales
                fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                contenido = f"""
╔════════════════════════════════════════════════════════════════╗
║          CREDENCIALES DE ADMINISTRADOR - NUEVA CLÍNICA         ║
╚════════════════════════════════════════════════════════════════╝

📋 INFORMACIÓN DE LA CLÍNICA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nombre de la Clínica:  {result['tenant'].name}
Subdominio:            {result['subdomain']}
Fecha de Creación:     {fecha_creacion}


🔐 CREDENCIALES DEL ADMINISTRADOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Email:                 {result['admin_email']}
Contraseña Temporal:   {result['temporary_password']}


🌐 ENLACES DE ACCESO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Panel de Administración:
  https://{result['subdomain']}.psicoadmin.xyz/admin/

Aplicación Web (Frontend):
  https://{result['subdomain']}.psicoadmin.xyz/


⚠️  INSTRUCCIONES IMPORTANTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Accede al panel de administración usando las credenciales arriba.
2. CAMBIA LA CONTRASEÑA TEMPORAL inmediatamente después del primer acceso.
3. Guarda este archivo en un lugar seguro.
4. No compartas estas credenciales por correo electrónico o mensajes sin cifrar.


📞 SOPORTE TÉCNICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Si tienes problemas para acceder, contacta a soporte técnico.


═══════════════════════════════════════════════════════════════════
Sistema PsicoAdmin - Gestión de Clínicas de Salud Mental
Generado automáticamente el {fecha_creacion}
═══════════════════════════════════════════════════════════════════
"""
                
                # Crear respuesta HTTP con archivo de texto
                response = HttpResponse(contenido, content_type='text/plain; charset=utf-8')
                filename = f"credenciales_{result['subdomain']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                
                logger.info(f"✅ Nueva clínica registrada con descarga: {result['tenant'].name} ({result['subdomain']})")
                
                return response
            else:
                # Respuesta JSON normal
                response_data = {
                    'success': True,
                    'message': '¡Clínica creada exitosamente!',
                    'data': {
                        'clinic_name': result['tenant'].name,
                        'subdomain': result['subdomain'],
                        'admin_url': f"https://{result['subdomain']}.psicoadmin.xyz/admin/",
                        'frontend_url': f"https://{result['subdomain']}.psicoadmin.xyz/",
                        'admin_email': result['admin_email'],
                        'temporary_password': result['temporary_password'],
                        'instructions': (
                            f"Tu clínica ha sido creada exitosamente. "
                            f"Puedes acceder al panel de administración en: "
                            f"https://{result['subdomain']}.psicoadmin.xyz/admin/ "
                            f"usando tu email y la contraseña temporal proporcionada. "
                            f"Por favor, cámbiala después del primer acceso."
                        )
                    }
                }
                
                logger.info(f"✅ Nueva clínica registrada: {result['tenant'].name} ({result['subdomain']})")
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Error en registro de tenant: {str(e)}")
            return Response(
                {'success': False, 'error': f'Error al crear la clínica: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return Response(
        {'success': False, 'errors': serializer.errors}, 
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])  # ⭐ Acceso público
def check_subdomain_availability(request):
    """
    Endpoint público para verificar disponibilidad de subdominio.
    
    POST /api/public/check-subdomain/
    Body: {
        "subdomain": "miclinica"
    }
    
    Response: {
        "available": true/false,
        "subdomain": "miclinica",
        "full_domain": "miclinica.psicoadmin.xyz"
    }
    """
    serializer = SubdomainCheckSerializer(data=request.data)
    
    if serializer.is_valid():
        subdomain = serializer.validated_data['subdomain']
        domain_name = f"{subdomain}.psicoadmin.xyz"
        
        # Verificar disponibilidad
        domain_exists = Domain.objects.filter(domain=domain_name).exists()
        schema_exists = Clinic.objects.filter(schema_name=subdomain).exists()
        
        available = not (domain_exists or schema_exists)
        
        response_data = {
            'available': available,
            'subdomain': subdomain,
            'full_domain': domain_name,
            'message': '✅ Subdominio disponible' if available else '❌ Subdominio no disponible'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(
        {'available': False, 'errors': serializer.errors}, 
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([])  # ⭐ Sin autenticación requerida
def public_clinic_list(request):
    """
    Vista pública para listar todas las clínicas disponibles.
    Usada por la app móvil para el selector de clínicas.
    No requiere autenticación.
    
    GET /api/tenants/
    
    Response:
    {
        "count": 2,
        "results": [
            {
                "id": 2,
                "name": "Clínica Bienestar",
                "schema_name": "bienestar",
                "description": "Clínica especializada en bienestar mental",
                "logo": null
            },
            {
                "id": 3,
                "name": "Clínica MindCare",
                "schema_name": "mindcare",
                "description": "Cuidado mental profesional",
                "logo": null
            }
        ]
    }
    """
    try:
        from django.db import connection
        
        # Guardar el schema actual
        current_schema = connection.schema_name if hasattr(connection, 'schema_name') else None
        
        logger.info(f"📋 public_clinic_list - Schema actual: {current_schema}")
        
        # Forzar el uso del schema público para acceder a todas las clínicas
        with schema_context('public'):
            logger.info("📋 Accediendo al schema público para listar clínicas...")
            
            # Obtener todas las clínicas (excluyendo el schema público)
            clinics = Clinic.objects.exclude(schema_name='public').order_by('id')
            
            logger.info(f"📋 Clínicas encontradas: {clinics.count()}")
            
            clinics_data = []
            for clinic in clinics:
                logger.info(f"📋 Procesando clínica: {clinic.name} (schema: {clinic.schema_name})")
                
                # Obtener el dominio principal
                domain = Domain.objects.filter(tenant=clinic, is_primary=True).first()
                
                clinic_data = {
                    'id': clinic.id,
                    'name': clinic.name,
                    'schema_name': clinic.schema_name,
                    'description': f"Clínica {clinic.name}",  # Descripción por defecto
                    'logo': None  # El modelo no tiene logo por ahora
                }
                
                if domain:
                    logger.info(f"   Dominio: {domain.domain}")
                
                clinics_data.append(clinic_data)
        
        logger.info(f"✅ public_clinic_list - Devolviendo {len(clinics_data)} clínicas")
        
        return Response({
            'count': len(clinics_data),
            'results': clinics_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error listando clínicas públicas: {str(e)}", exc_info=True)
        return Response(
            {'error': 'Error al obtener lista de clínicas', 'details': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )