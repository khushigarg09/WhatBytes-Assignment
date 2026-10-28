from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Patient, Doctor, PatientDoctorMapping
from .serializers import (
    PatientSerializer,
    DoctorSerializer,
    PatientDoctorMappingSerializer,
    PatientDoctorMappingCreateSerializer,
)


# ============================================================================
# Patient Views
# ============================================================================

class PatientListCreateView(generics.ListCreateAPIView):
    """
    POST /api/patients/ - Add a new patient (authenticated user).
    GET  /api/patients/ - Retrieve all patients created by the authenticated user.
    """
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/patients/<id>/ - Get details of a specific patient owned by user.
    PUT    /api/patients/<id>/ - Update patient details.
    DELETE /api/patients/<id>/ - Delete a patient record.
    Returns 404 for records not owned by the current user.
    """
    serializer_class = PatientSerializer

    def get_queryset(self):
        return Patient.objects.filter(created_by=self.request.user)


# ============================================================================
# Doctor Views
# ============================================================================

class DoctorListCreateView(generics.ListCreateAPIView):
    """
    POST /api/doctors/ - Add a new doctor (authenticated user).
    GET  /api/doctors/ - Retrieve all doctors.
    """
    serializer_class = DoctorSerializer

    def get_queryset(self):
        return Doctor.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/doctors/<id>/ - Get details of a specific doctor owned by user.
    PUT    /api/doctors/<id>/ - Update doctor details.
    DELETE /api/doctors/<id>/ - Delete a doctor record.
    Returns 404 for records not owned by the current user.
    """
    serializer_class = DoctorSerializer

    def get_queryset(self):
        return Doctor.objects.filter(created_by=self.request.user)


# ============================================================================
# Mapping Views
# ============================================================================

class PatientDoctorMappingListCreateView(APIView):
    """
    POST /api/mappings/ - Assign a doctor to a patient.
    GET  /api/mappings/ - Retrieve all patient-doctor mappings for user's records.
    """

    def get(self, request):
        mappings = (
            PatientDoctorMapping.objects
            .filter(
                patient__created_by=request.user,
                doctor__created_by=request.user
            )
            .select_related('patient', 'doctor')
        )
        serializer = PatientDoctorMappingSerializer(mappings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PatientDoctorMappingCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        mapping = serializer.save()
        output_serializer = PatientDoctorMappingSerializer(mapping)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PatientDoctorMappingDetailView(APIView):
    """
    GET    /api/mappings/<patient_id>/ - Get all doctors assigned to that owned patient.
    DELETE /api/mappings/<id>/         - Remove a doctor mapping by mapping ID.
    Returns 404 for records outside the current user's scope.
    """

    def get(self, request, pk):
        # Look up patient scoped to user; returns 404 if not found or not owned
        patient = get_object_or_404(
            Patient.objects.filter(created_by=request.user),
            pk=pk
        )
        mappings = (
            PatientDoctorMapping.objects
            .filter(patient=patient)
            .select_related('doctor')
        )
        doctors = [m.doctor for m in mappings]
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        # Look up mapping scoped to user; returns 404 if not found or not owned
        mapping = get_object_or_404(
            PatientDoctorMapping.objects.filter(
                patient__created_by=request.user,
                doctor__created_by=request.user
            ),
            pk=pk
        )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

