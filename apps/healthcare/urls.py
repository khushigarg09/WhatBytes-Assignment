from django.urls import path

from .views import (
    PatientListCreateView,
    PatientDetailView,
    DoctorListCreateView,
    DoctorDetailView,
    PatientDoctorMappingListCreateView,
    PatientDoctorMappingDetailView,
)

urlpatterns = [
    # Patients
    path('patients/', PatientListCreateView.as_view(), name='patient_list_create'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient_detail'),

    # Doctors
    path('doctors/', DoctorListCreateView.as_view(), name='doctor_list_create'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor_detail'),

    # Mappings
    path('mappings/', PatientDoctorMappingListCreateView.as_view(), name='mapping_list_create'),
    path('mappings/<int:pk>/', PatientDoctorMappingDetailView.as_view(), name='mapping_detail'),
]

