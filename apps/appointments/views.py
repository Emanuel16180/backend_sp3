# apps/appointments/views.py

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Appointment, PsychologistAvailability, TimeSlot
from apps.professionals.models import ProfessionalProfile
from apps.professionals.models import ProfessionalProfile
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    PsychologistAvailabilitySerializer,
    TimeSlotSerializer,
    AvailablePsychologistSerializer,
    ReferralCreateSerializer
)

User = get_user_model()


class IsOwnerOrPsychologist(permissions.BasePermission):
    """
    Permiso personalizado para citas
    - El paciente puede ver/editar sus propias citas
    - El psicólogo puede ver/editar las citas donde es el profesional
    """
    def has_object_permission(self, request, view, obj):
        return (
            obj.patient == request.user or 
            obj.psychologist == request.user
        )


class IsPsychologist(permissions.BasePermission):
    """Solo psicólogos pueden acceder"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'professional' # <-- CAMBIO AQUÍ
class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar citas
    """
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrPsychologist]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Appointment.objects.all()
        
        # Filtrar por tipo de usuario
        if user.user_type == 'patient':
            queryset = queryset.filter(patient=user)
        elif user.user_type == 'professional':
            queryset = queryset.filter(psychologist=user)
        
        # Filtros adicionales por query params
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)
        
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)
        
        return queryset.order_by('-appointment_date', '-start_time')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        return AppointmentSerializer
    
    def create(self, request, *args, **kwargs):
        """Crear nueva cita (solo pacientes)"""
        if request.user.user_type != 'patient':
            return Response(
                {'error': 'Solo los pacientes pueden agendar citas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Retornar con el serializer completo
        appointment = serializer.instance
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Actualizar cita y devolver objeto completo"""
        # Llama al método de actualización original para que haga la validación y guardado
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Si el guardado fue exitoso, ahora devolvemos la instancia completa
        # usando el serializer principal (AppointmentSerializer)
        
        # Obtenemos la instancia actualizada de la base de datos
        instance = self.get_object() 
        # La serializamos con el serializer completo por defecto
        full_serializer = AppointmentSerializer(instance) 

        return Response(full_serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirmar una cita (solo el psicólogo)"""
        appointment = self.get_object()
        
        if request.user != appointment.psychologist:
            return Response(
                {'error': 'Solo el psicólogo puede confirmar la cita'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment.status != 'pending':
            return Response(
                {'error': 'Solo se pueden confirmar citas pendientes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'confirmed'
        appointment.save()
        
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar una cita"""
        appointment = self.get_object()
        
        if appointment.status in ['cancelled', 'completed']:
            return Response(
                {'error': 'Esta cita no se puede cancelar'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que no sea muy cerca de la cita (ej: 24 horas antes)
        now = datetime.now()
        appointment_datetime = datetime.combine(
            appointment.appointment_date,
            appointment.start_time
        )
        
        if (appointment_datetime - now).total_seconds() < 86400:  # 24 horas
            return Response(
                {'error': 'No se puede cancelar con menos de 24 horas de anticipación'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'cancelled'
        appointment.notes += f"\n\nCancelado por {request.user.get_full_name()} el {now.strftime('%Y-%m-%d %H:%M')}"
        appointment.save()
        
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Marcar cita como completada (solo el psicólogo)"""
        appointment = self.get_object()
        
        if request.user != appointment.psychologist:
            return Response(
                {'error': 'Solo el psicólogo puede completar la cita'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if appointment.status != 'confirmed':
            return Response(
                {'error': 'Solo se pueden completar citas confirmadas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'completed'
        appointment.save()
        
        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Obtener próximas citas"""
        today = datetime.now().date()
        appointments = self.get_queryset().filter(
            appointment_date__gte=today,
            status__in=['pending', 'confirmed']
        )[:10]
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Obtener historial de citas"""
        today = datetime.now().date()
        appointments = self.get_queryset().filter(
            Q(appointment_date__lt=today) | Q(status='completed')
        )
        
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='refer')
    def refer_appointment(self, request, pk=None):
        """
        NUEVO: Endpoint para derivar esta cita a otro colega.
        """
        appointment = self.get_object()

        # 1. Validar permisos
        if request.user != appointment.psychologist:
            return Response(
                {'error': 'Solo el psicólogo de la cita puede derivarla.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Validar que no haya sido derivada ya
        if hasattr(appointment, 'referral'):
            return Response(
                {'error': 'Esta cita ya ha sido derivada.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Validar los datos de entrada
        serializer = ReferralCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            referred_psychologist = User.objects.get(id=data['referred_psychologist_id'])

            # 4. Crear la derivación
            Referral.objects.create(
                appointment=appointment,
                referring_psychologist=request.user,
                referred_psychologist=referred_psychologist,
                reason=data['reason'],
                status='pending'
            )

            # 5. Actualizar la cita original (opcional, pero recomendado)
            # La marcamos como 'cancelled' para que libere el horario
            appointment.status = 'cancelled'
            appointment.notes += f"\n\n[Derivada a {referred_psychologist.get_full_name()} por: {data['reason']}]"
            appointment.save()

            logger.info(f"Cita {appointment.id} derivada a {referred_psychologist.email} por {request.user.email}")

            return Response(
                {'status': 'Cita derivada exitosamente.'},
                status=status.HTTP_201_CREATED
            )

        except User.DoesNotExist:
            return Response({'error': 'Psicólogo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error al crear derivación: {e}")
            return Response({'error': 'Error interno al crear la derivación.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# apps/appointments/views.py

class PsychologistAvailabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar disponibilidad de psicólogos
    """
    queryset = PsychologistAvailability.objects.all()
    serializer_class = PsychologistAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # --- 1. ARREGLO DE PAGINACIÓN ---
    # Le decimos a esta vista que NO use la paginación de 20 items.
    pagination_class = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # --- 2. ARREGLO DEL FILTRO DE USUARIO ---
        # Comparamos con 'professional' (como está en el modelo)
        # en lugar de 'psychologist'.
        if self.request.user.user_type == 'professional':
            queryset = queryset.filter(psychologist=self.request.user)
        # ----------------------------------------
        
        # Filtro por psicólogo específico (esto es para el admin, está bien)
        psychologist_id = self.request.query_params.get('psychologist', None)
        if psychologist_id:
            queryset = queryset.filter(psychologist_id=psychologist_id)
        
        return queryset.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        """Crear disponibilidad (solo psicólogos para sí mismos)"""
        
        # --- 3. ARREGLO DE PERMISOS DE CREACIÓN ---
        if request.user.user_type != 'professional':
        # ------------------------------------------
            return Response(
                {'error': 'Solo los psicólogos pueden crear disponibilidad'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Asignar automáticamente el psicólogo
        data = request.data.copy()
        data['psychologist'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Actualizar disponibilidad (solo el propio psicólogo)"""
        instance = self.get_object()
        
        if request.user != instance.psychologist:
            return Response(
                {'error': 'Solo puedes editar tu propia disponibilidad'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    # ... (el resto de las funciones @action se quedan igual) ...
    @action(detail=True, methods=['post'])
    def block_date(self, request, pk=None):
        """Bloquear una fecha específica"""
        availability = self.get_object()
        
        if request.user != availability.psychologist:
            return Response(
                {'error': 'Solo puedes bloquear tu propia disponibilidad'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        date_to_block = request.data.get('date')
        if not date_to_block:
            return Response(
                {'error': 'Debe proporcionar una fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if date_to_block not in availability.blocked_dates:
            availability.blocked_dates.append(date_to_block)
            availability.save()
        
        return Response(
            {'message': f'Fecha {date_to_block} bloqueada exitosamente'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def unblock_date(self, request, pk=None):
        """Desbloquear una fecha específica"""
        availability = self.get_object()
        
        if request.user != availability.psychologist:
            return Response(
                {'error': 'Solo puedes desbloquear tu propia disponibilidad'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        date_to_unblock = request.data.get('date')
        if not date_to_unblock:
            return Response(
                {'error': 'Debe proporcionar una fecha'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if date_to_unblock in availability.blocked_dates:
            availability.blocked_dates.remove(date_to_unblock)
            availability.save()
        
        return Response(
            {'message': f'Fecha {date_to_unblock} desbloqueada exitosamente'},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def search_available_psychologists(request):
    """
    Buscar psicólogos disponibles para una fecha y hora específica
    
    Query params:
    - date: YYYY-MM-DD
    - time: HH:MM (opcional)
    - specialization: ID de especialización (opcional)
    - city: ciudad (opcional)
    """
    date_str = request.query_params.get('date')
    time_str = request.query_params.get('time')
    specialization_id = request.query_params.get('specialization')
    city = request.query_params.get('city')
    
    if not date_str:
        return Response(
            {'error': 'Debe proporcionar una fecha'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response(
            {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar que no sea fecha pasada
    if search_date < datetime.now().date():
        return Response(
            {'error': 'No se puede buscar disponibilidad en fechas pasadas'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obtener el día de la semana
    weekday = search_date.weekday()
    
    # Filtrar psicólogos con disponibilidad en ese día
    psychologists = User.objects.filter(
        user_type='professional',
        is_active=True,
        availabilities__weekday=weekday,
        availabilities__is_active=True
    ).distinct()
    
    # Filtrar por especialización si se proporciona
    if specialization_id:
        psychologists = psychologists.filter(
            professional_profile__specializations__id=specialization_id
        )
    
    # Filtrar por ciudad si se proporciona
    if city:
        psychologists = psychologists.filter(
            professional_profile__city__icontains=city
        )
    
    # Si se proporciona hora específica, filtrar más
    if time_str:
        try:
            search_time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return Response(
                {'error': 'Formato de hora inválido. Use HH:MM'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filtrar por horario disponible
        psychologists = psychologists.filter(
            availabilities__start_time__lte=search_time,
            availabilities__end_time__gt=search_time
        )
    
    # Filtrar psicólogos que no tengan fechas bloqueadas
    available_psychologists = []
    for psychologist in psychologists:
        availabilities = psychologist.availabilities.filter(
            weekday=weekday,
            is_active=True
        )
        
        # Verificar si alguna disponibilidad no está bloqueada para esa fecha
        for availability in availabilities:
            if str(search_date) not in availability.blocked_dates:
                available_psychologists.append(psychologist)
                break
    
    # Serializar y devolver
    serializer = AvailablePsychologistSerializer(
        available_psychologists,
        many=True,
        context={'request': request}
    )
    
    return Response({
        'date': date_str,
        'day': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][weekday],
        'psychologists_count': len(available_psychologists),
        'psychologists': serializer.data
    })

# en apps/appointments/views.py

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_psychologist_schedule(request, psychologist_id):
    """
    Obtener el horario completo de un psicólogo para una semana
    """
    try: # <-- La indentación aquí está corregida
        # Buscamos el PERFIL PROFESIONAL por el ID del usuario, no por el ID del perfil
        profile = ProfessionalProfile.objects.get(user_id=psychologist_id)
        psychologist = profile.user
    except ProfessionalProfile.DoesNotExist:
        return Response(
            {'error': 'Perfil de Psicólogo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener fecha de inicio (por defecto, esta semana)
    date_str = request.query_params.get('week_start')
    if date_str:
        try:
            week_start = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            week_start = datetime.now().date()
    else:
        week_start = datetime.now().date()

    # Generar el horario de la semana
    schedule = []
    for i in range(7):
        current_date = week_start + timedelta(days=i)
        weekday = current_date.weekday()

        availabilities = PsychologistAvailability.objects.filter(
            psychologist=psychologist,
            weekday=weekday,
            is_active=True
        )

        day_schedule = {
            'date': current_date.strftime('%Y-%m-%d'),
            'weekday': weekday,
            'day_name': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][weekday],
            'is_available': False,
            'blocked': False,
            'time_slots': []
        }

        for availability in availabilities:
            if str(current_date) in availability.blocked_dates:
                day_schedule['blocked'] = True
                continue

            day_schedule['is_available'] = True

            current_time = datetime.combine(current_date, availability.start_time)
            end_time = datetime.combine(current_date, availability.end_time)

            duration = 60
            if hasattr(psychologist, 'professional_profile'):
                duration = psychologist.professional_profile.session_duration

            while current_time + timedelta(minutes=duration) <= end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=duration)).time()

                is_booked = Appointment.objects.filter(
                    psychologist=psychologist,
                    appointment_date=current_date,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start,
                    status__in=['pending', 'confirmed']
                ).exists()

                day_schedule['time_slots'].append({
                    'start_time': slot_start.strftime('%H:%M'),
                    'end_time': slot_end.strftime('%H:%M'),
                    'is_available': not is_booked,
                    'is_booked': is_booked
                })

                current_time += timedelta(minutes=duration)

        schedule.append(day_schedule)

    return Response({
        'psychologist': {
            'id': psychologist.id,
            'name': psychologist.get_full_name(),
            'email': psychologist.email
        },
        'week_start': week_start.strftime('%Y-%m-%d'),
        'week_end': (week_start + timedelta(days=6)).strftime('%Y-%m-%d'),
        'schedule': schedule
    })