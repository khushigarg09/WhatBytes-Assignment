from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from .models import Patient, Doctor, PatientDoctorMapping


class PatientSerializer(serializers.ModelSerializer):
    """Full serializer for Patient model."""

    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Patient
        fields = (
            'id',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'phone',
            'email',
            'address',
            'created_by',
            'created_at',
            'updated_at',
        )

    def validate_date_of_birth(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        return value


class DoctorSerializer(serializers.ModelSerializer):
    """Full serializer for Doctor model."""

    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Doctor
        fields = (
            'id',
            'first_name',
            'last_name',
            'specialization',
            'phone',
            'email',
            'created_by',
            'created_at',
            'updated_at',
        )


class ConcisePatientSerializer(serializers.ModelSerializer):
    """Concise Patient representation for nested mapping responses."""

    class Meta:
        model = Patient
        fields = ('id', 'first_name', 'last_name', 'phone', 'email')


class ConciseDoctorSerializer(serializers.ModelSerializer):
    """Concise Doctor representation for nested mapping responses."""

    class Meta:
        model = Doctor
        fields = ('id', 'first_name', 'last_name', 'specialization', 'phone', 'email')


class PatientDoctorMappingSerializer(serializers.ModelSerializer):
    """Serializer for reading PatientDoctorMapping with nested concise details."""

    patient = ConcisePatientSerializer(read_only=True)
    doctor = ConciseDoctorSerializer(read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = ('id', 'patient', 'doctor', 'created_at')


class PatientDoctorMappingCreateSerializer(serializers.Serializer):
    """Serializer for creating a new PatientDoctorMapping."""

    patient_id = serializers.IntegerField(required=True)
    doctor_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        user = self.context['request'].user
        patient_id = attrs.get('patient_id')
        doctor_id = attrs.get('doctor_id')

        # User may only map their own patient to their own doctor.
        # Return 404 for records outside current user's scope to prevent existence leaking.
        patient = Patient.objects.filter(id=patient_id, created_by=user).first()
        if not patient:
            raise NotFound(detail=f"Patient with id {patient_id} not found.")

        doctor = Doctor.objects.filter(id=doctor_id, created_by=user).first()
        if not doctor:
            raise NotFound(detail=f"Doctor with id {doctor_id} not found.")

        # Check for duplicate assignment
        if PatientDoctorMapping.objects.filter(patient=patient, doctor=doctor).exists():
            raise serializers.ValidationError("This doctor is already assigned to this patient.")

        attrs['patient'] = patient
        attrs['doctor'] = doctor
        return attrs

    def create(self, validated_data):
        return PatientDoctorMapping.objects.create(
            patient=validated_data['patient'],
            doctor=validated_data['doctor']
        )

