# apps/clinical_history/admin.py

from django.contrib import admin
from .models import SessionNote, ClinicalDocument

# ❌ NO USAR @admin.register() - Interfiere con multi-tenancy
# Los modelos se registran manualmente en config/admin_site.py

class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'appointment_date', 'patient_name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'appointment__appointment_date')
    search_fields = ('appointment__patient__first_name', 'appointment__patient__last_name', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    def appointment_date(self, obj):
        return obj.appointment.appointment_date
    appointment_date.short_description = 'Fecha de Cita'
    
    def patient_name(self, obj):
        return obj.appointment.patient.get_full_name()
    patient_name.short_description = 'Paciente'


class ClinicalDocumentAdmin(admin.ModelAdmin):
    list_display = ('description', 'patient_name', 'uploaded_by_name', 'uploaded_at', 'file_name')
    list_filter = ('uploaded_at', 'uploaded_by')
    search_fields = ('description', 'patient__first_name', 'patient__last_name', 'uploaded_by__first_name', 'uploaded_by__last_name')
    readonly_fields = ('uploaded_at',)
    
    def patient_name(self, obj):
        return obj.patient.get_full_name()
    patient_name.short_description = 'Paciente'
    
    def uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else 'N/A'
    uploaded_by_name.short_description = 'Subido por'
    
    def file_name(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else 'N/A'
    file_name.short_description = 'Archivo'
