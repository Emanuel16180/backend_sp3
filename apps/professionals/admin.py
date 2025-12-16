from django.contrib import admin

# Register your models here.
# en apps/professionals/admin.py

from django.contrib import admin
from .models import ProfessionalProfile, Specialization, WorkingHours, Review

class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

class ProfessionalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'experience_years', 'average_rating', 'total_reviews', 'is_active', 'profile_completed')
    list_filter = ('is_active', 'profile_completed', 'specializations')
    search_fields = ('user__first_name', 'user__last_name', 'license_number')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('patient', 'professional', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('patient__first_name', 'patient__last_name', 'professional__user__first_name', 'professional__user__last_name')
    readonly_fields = ('created_at',)

# NO registrar en el admin por defecto - se registran en admin sites específicos
# admin.site.register(ProfessionalProfile, ProfessionalProfileAdmin)
# admin.site.register(Specialization, SpecializationAdmin)
# admin.site.register(WorkingHours)
# admin.site.register(Review, ReviewAdmin)

# Registrar también en el tenant admin
from config.tenant_admin import tenant_admin_site
tenant_admin_site.register(ProfessionalProfile, ProfessionalProfileAdmin)
tenant_admin_site.register(Specialization, SpecializationAdmin)
tenant_admin_site.register(WorkingHours)
tenant_admin_site.register(Review, ReviewAdmin)