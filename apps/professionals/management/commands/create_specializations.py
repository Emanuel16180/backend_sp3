# apps/professionals/management/commands/create_specializations.py

from django.core.management.base import BaseCommand
from apps.professionals.models import Specialization

class Command(BaseCommand):
    help = 'Crear especialidades básicas para psicólogos'
    
    def handle(self, *args, **options):
        specializations = [
            ('Psicología Clínica', 'Tratamiento de trastornos mentales y emocionales'),
            ('Psicología Infantil', 'Especialización en niños y adolescentes'),
            ('Terapia de Pareja', 'Consejería y terapia para parejas'),
            ('Psicología Familiar', 'Terapia familiar y dinámicas familiares'),
            ('Ansiedad y Estrés', 'Tratamiento de trastornos de ansiedad'),
            ('Depresión', 'Tratamiento especializado en depresión'),
            ('Trastornos Alimentarios', 'Anorexia, bulimia y otros trastornos'),
            ('Adicciones', 'Tratamiento de dependencias'),
            ('Terapia Cognitivo-Conductual', 'Enfoque TCC'),
            ('Psicoanálisis', 'Enfoque psicoanalítico'),
        ]
        
        for name, description in specializations:
            specialization, created = Specialization.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            if created:
                self.stdout.write(f'Especialización creada: {name}')
            else:
                self.stdout.write(f'Especialización ya existe: {name}')
        
        self.stdout.write(
            self.style.SUCCESS('Especialidades creadas exitosamente')
        )