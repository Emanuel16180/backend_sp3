# apps/appointments/management/commands/create_availability.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.appointments.models import PsychologistAvailability
from datetime import time

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea disponibilidad de ejemplo para psicólogos'
    
    def handle(self, *args, **kwargs):
        # Obtener todos los psicólogos
        psychologists = User.objects.filter(user_type='professional')
        
        if not psychologists.exists():
            self.stdout.write(
                self.style.WARNING('No hay psicólogos registrados. Registra psicólogos primero.')
            )
            return
        
        # Horarios comunes de trabajo
        morning_schedules = [
            (time(8, 0), time(12, 0)),
            (time(9, 0), time(13, 0)),
        ]
        
        afternoon_schedules = [
            (time(14, 0), time(18, 0)),
            (time(15, 0), time(19, 0)),
        ]
        
        evening_schedules = [
            (time(16, 0), time(20, 0)),
            (time(17, 0), time(21, 0)),
        ]
        
        created_count = 0
        
        for psychologist in psychologists:
            self.stdout.write(f'Creando disponibilidad para {psychologist.get_full_name()}...')
            
            # Limpiar disponibilidad existente
            PsychologistAvailability.objects.filter(psychologist=psychologist).delete()
            
            # Asignar horarios variados
            if psychologist.id % 3 == 0:
                # Horario matutino (Lunes a Viernes)
                schedule = morning_schedules[0]
                days = [0, 1, 2, 3, 4]  # Lun-Vie
            elif psychologist.id % 3 == 1:
                # Horario vespertino (Lunes a Viernes)
                schedule = afternoon_schedules[0]
                days = [0, 1, 2, 3, 4]  # Lun-Vie
            else:
                # Horario mixto (incluye sábados)
                schedule = evening_schedules[0]
                days = [1, 2, 3, 4, 5]  # Mar-Sáb
            
            for day in days:
                availability = PsychologistAvailability.objects.create(
                    psychologist=psychologist,
                    weekday=day,
                    start_time=schedule[0],
                    end_time=schedule[1],
                    is_active=True
                )
                created_count += 1
            
            # Algunos psicólogos también trabajan en horario adicional
            if psychologist.id % 2 == 0:
                # Agregar horario de tarde algunos días
                extra_days = [1, 3]  # Martes y Jueves
                extra_schedule = (time(19, 0), time(21, 0))
                
                for day in extra_days:
                    if not PsychologistAvailability.objects.filter(
                        psychologist=psychologist,
                        weekday=day,
                        start_time=extra_schedule[0]
                    ).exists():
                        PsychologistAvailability.objects.create(
                            psychologist=psychologist,
                            weekday=day,
                            start_time=extra_schedule[0],
                            end_time=extra_schedule[1],
                            is_active=True
                        )
                        created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Se crearon {created_count} registros de disponibilidad '
                f'para {psychologists.count()} psicólogos'
            )
        )