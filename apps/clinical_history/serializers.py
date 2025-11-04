# apps/clinical_history/serializers.py

from rest_framework import serializers
from .models import SessionNote, ClinicalDocument, ClinicalHistory, InitialTriage, MoodJournal, Objective, Task, TaskCompletion  # <-- 1. IMPORTA EL NUEVO MODELO
from apps.users.models import CustomUser

class SessionNoteSerializer(serializers.ModelSerializer):
    # Información adicional de la cita para el frontend
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='appointment.start_time', read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.get_full_name', read_only=True)
    
    class Meta:
        model = SessionNote
        fields = [
            'id',
            'appointment',
            'content',
            'created_at',
            'updated_at',
            # Campos adicionales para el frontend
            'appointment_date',
            'appointment_time', 
            'patient_name'
        ]
        # Hacemos que 'appointment' sea de solo lectura porque lo obtendremos de la URL.
        read_only_fields = ['appointment', 'appointment_date', 'appointment_time', 'patient_name']

    def validate_content(self, value):
        """Validar que el contenido no esté vacío"""
        if not value.strip():
            raise serializers.ValidationError("El contenido de la nota no puede estar vacío")
        return value.strip()


class ClinicalDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)

    class Meta:
        model = ClinicalDocument
        fields = [
            'id',
            'patient',
            'patient_name',
            'uploaded_by',
            'uploaded_by_name',
            'file',
            'file_url',
            'description',
            'uploaded_at'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_by_name', 'file_url', 'uploaded_at', 'patient_name']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def validate_description(self, value):
        """Validar que la descripción no esté vacía"""
        if not value.strip():
            raise serializers.ValidationError("La descripción del documento no puede estar vacía")
        return value.strip()


class PsychologistPatientSerializer(serializers.ModelSerializer):
    """Serializer simple para listar los pacientes de un psicólogo."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'full_name', 'email']


# --- 👇 AÑADE ESTA NUEVA CLASE AL FINAL DEL ARCHIVO 👇 ---

class ClinicalHistorySerializer(serializers.ModelSerializer):
    """
    Serializer para leer y escribir en el modelo de Historial Clínico.
    """
    class Meta:
        model = ClinicalHistory
        # Incluimos todos los campos que definimos en el modelo
        fields = [
            'patient',
            'consultation_reason',
            'history_of_illness',
            'personal_pathological_history',
            'family_history',
            'personal_non_pathological_history',
            'mental_examination',
            'complementary_tests',
            'diagnoses',
            'therapeutic_plan',
            'risk_assessment',
            'sensitive_topics',
            'created_by',
            'last_updated_by',
            'created_at',
            'updated_at',
        ]
        # Hacemos que ciertos campos sean de solo lectura para proteger los datos
        read_only_fields = ['patient', 'created_by', 'created_at', 'updated_at']

# apps/clinical_history/serializers.py
# ... (después de la clase ClinicalHistorySerializer) ...

class InitialTriageSubmitSerializer(serializers.ModelSerializer):
    """
    Serializer para recibir las respuestas del triaje.
    """
    # El frontend debe enviar un JSON con este formato:
    # { "answers": { "nodo1": "ansioso", "nodo3": "si_constantemente" } }
    answers = serializers.JSONField(write_only=True)

    class Meta:
        model = InitialTriage
        fields = ['patient', 'answers', 'pre_diagnosis', 'recommendation', 'created_at']
        read_only_fields = ['patient', 'pre_diagnosis', 'recommendation', 'created_at']

    def create(self, validated_data):
        # Aquí vinculamos la lógica del árbol de decisiones
        answers = validated_data.get('answers', {})
        patient = self.context['request'].user

        # 1. Procesar las respuestas
        pre_diagnosis, recommendation = self._process_triage_logic(answers)

        # 2. Guardar el resultado
        triage, created = InitialTriage.objects.update_or_create(
            patient=patient,
            defaults={
                'answers': answers,
                'pre_diagnosis': pre_diagnosis,
                'recommendation': recommendation
            }
        )
        return triage

    def _process_triage_logic(self, answers):
        """
        Implementación de la lógica del árbol de triaje (CU-21).
        """
        nodo1 = answers.get('nodo1')

        if nodo1 == 'triste_o_sin_ganas':
            # Nodo 2 (Depresión)
            nodo2 = answers.get('nodo2')
            if nodo2 == 'casi_todos_los_dias':
                return "Posible Depresión Moderada/Grave", "Se sugiere una evaluación profunda para confirmar el diagnóstico y comenzar un plan de apoyo."
            elif nodo2 == 'algunos_dias':
                return "Posible Depresión Leve", "Se sugiere una evaluación con un profesional para explorar estos síntomas."

        elif nodo1 == 'ansioso_preocupado_o_con_miedo':
            # Nodo 3 (Ansiedad)
            nodo3 = answers.get('nodo3')
            if nodo3 == 'si_constantemente':
                return "Posible Ansiedad Generalizada", "Se sugiere una evaluación más profunda con un profesional para confirmar el diagnóstico."
            elif nodo3 == 'a_veces_en_publico':
                return "Posible Ansiedad Social", "Un profesional puede ayudarte a desarrollar herramientas para manejar estas situaciones."

        elif nodo1 == 'irritable_o_dificultad_dormir':
            # Nodo 4 (Estrés)
            nodo4 = answers.get('nodo4')
            if nodo4 == 'trabajo_o_estudios':
                return "Posible Estrés Laboral/Académico", "Es importante desarrollar estrategias de manejo del estrés. Un profesional puede ayudarte."
            elif nodo4 == 'familia_o_relaciones':
                return "Posible Estrés Familiar", "La terapia puede ofrecer un espacio para gestionar estos conflictos."

        elif nodo1 == 'conflictos_personales_o_pareja':
            # Nodo 5 (Relaciones)
            nodo5 = answers.get('nodo5')
            if nodo5 == 'si_con_frecuencia':
                return "Posibles Conflictos Interpersonales", "La terapia de pareja o individual puede ser muy beneficiosa."

        elif nodo1 == 'consumo_alcohol_o_sustancias':
            # Nodo 6 (Adicciones)
            nodo6 = answers.get('nodo6')
            if nodo6 == 'si_pierdo_control':
                return "Posible Trastorno por Consumo", "Es fundamental buscar ayuda profesional especializada para evaluar la situación."

        # Por defecto o si es 'bien_sin_cambios'
        return "Sin Signos Relevantes Detectados", "No se detectan signos de alarma inmediatos, pero siempre puedes hablar con un profesional si lo necesitas."

class MoodJournalSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y listar entradas del diario de ánimo.
    """
    # Obtenemos el nombre legible (ej: "Feliz")
    mood_display = serializers.CharField(source='get_mood_display', read_only=True)

    class Meta:
        model = MoodJournal
        fields = [
            'id', 
            'patient', 
            'date', 
            'mood', 
            'mood_display',
            'notes', 
            'created_at'
        ]
        read_only_fields = ['id', 'patient', 'date', 'mood_display', 'created_at']

    def validate(self, data):
        # Verificación extra para dar un error amigable
        # (Aunque la BD también lo previene con unique_together)
        from datetime import date
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Contexto de request no válido")

        today = date.today()
        patient = request.user

        # Comprueba si ya existe una entrada para este paciente HOY
        if MoodJournal.objects.filter(patient=patient, date=today).exists():
            raise serializers.ValidationError("Ya has registrado tu estado de ánimo hoy.")

        return data

class TaskCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCompletion
        fields = ['id', 'task', 'completed_date', 'notes']
        # --- 👇 1. AÑADE ESTA LÍNEA 👇 ---
        # 'task' y 'completed_date' los provee la vista, no el frontend.
        read_only_fields = ['id', 'task', 'completed_date']

    # --- 👇 2. AÑADE ESTA FUNCIÓN DE VALIDACIÓN 👇 ---
    def validate(self, data):
        from datetime import date
        # Obtenemos la tarea desde el contexto que la vista le pasará
        task = self.context.get('task')
        patient = self.context.get('request').user
        today = date.today()

        if not task:
            # Esto no debería pasar si la vista funciona, pero es una buena guarda
            raise serializers.ValidationError("La tarea no fue especificada en el contexto.")

        # ¡La lógica clave! Comprobar si ya existe
        if TaskCompletion.objects.filter(
            task=task, 
            patient=patient, 
            completed_date=today
        ).exists():
            raise serializers.ValidationError("Esta tarea ya fue completada hoy.")
        
        return data

class TaskSerializer(serializers.ModelSerializer):
    # Campo dinámico para decirle al frontend si esta tarea ya se completó HOY
    is_completed_today = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'objective', 'title', 'recurrence', 'is_completed_today']

    def get_is_completed_today(self, obj):
        from datetime import date
        patient = self.context.get('patient')
        if not patient:
            return False
        # Comprueba si existe un registro de hoy para esta tarea y este paciente
        return TaskCompletion.objects.filter(
            task=obj,
            patient=patient,
            completed_date=date.today()
        ).exists()


class ObjectiveSerializer(serializers.ModelSerializer):
    """Serializer para LEER objetivos y sus tareas"""
    tasks = TaskSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    psychologist_name = serializers.CharField(source='psychologist.get_full_name', read_only=True)

    class Meta:
        model = Objective
        fields = [
            'id', 'patient', 'patient_name', 'psychologist_name', 
            'appointment', 'title', 'description', 'status', 
            'created_at', 'tasks'
        ]

    # ¡Idea Clave! Sobrescribimos el serializer de 'tasks'
    # para inyectar el 'patient' en su contexto.
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        task_serializer = TaskSerializer(
            instance.tasks.all(), 
            many=True, 
            context={'patient': instance.patient}
        )
        representation['tasks'] = task_serializer.data
        return representation


class ObjectiveCreateSerializer(serializers.ModelSerializer):
    """Serializer para CREAR un objetivo con sus tareas"""
    # El frontend enviará una lista de strings con los títulos de las tareas
    tasks = serializers.ListField(
        child=serializers.CharField(max_length=255), 
        write_only=True,
        required=True
    )
    # El frontend enviará el ID de la recurrencia
    recurrence = serializers.ChoiceField(
        choices=Task.RECURRENCE_CHOICES,
        write_only=True,
        required=True
    )

    class Meta:
        model = Objective
        fields = [
            'patient',       # ID del paciente
            'appointment',   # ID de la cita
            'title',
            'description',
            'tasks',
            'recurrence'
        ]

    def create(self, validated_data):
        # Sacamos los datos de las tareas antes de crear el objetivo
        tasks_data = validated_data.pop('tasks', [])
        recurrence_data = validated_data.pop('recurrence')

        # Creamos el Objetivo
        objective = Objective.objects.create(**validated_data)

        # Creamos las Tareas y las vinculamos
        for task_title in tasks_data:
            Task.objects.create(
                objective=objective, 
                title=task_title,
                recurrence=recurrence_data
            )

        return objective