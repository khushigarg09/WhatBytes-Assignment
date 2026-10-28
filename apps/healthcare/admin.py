from django.contrib import admin
from .models import Patient, Doctor, PatientDoctorMapping


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone', 'created_by', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('gender', 'created_at')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'specialization', 'email', 'phone', 'created_by', 'created_at')
    search_fields = ('first_name', 'last_name', 'specialization', 'email', 'phone')
    list_filter = ('specialization', 'created_at')


@admin.register(PatientDoctorMapping)
class PatientDoctorMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient__first_name', 'patient__last_name', 'doctor__first_name', 'doctor__last_name')

