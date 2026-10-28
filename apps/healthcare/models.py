from django.conf import settings
from django.db import models


class Patient(models.Model):
    """
    Patient model.
    A patient is registered and owned by a User.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patients'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Doctor(models.Model):
    """
    Doctor model.
    A doctor record is created and owned by a User.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctors'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.specialization})"


class PatientDoctorMapping(models.Model):
    """
    Mapping between a Patient and a Doctor.
    Ensures unique assignment between patient and doctor.
    """
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='doctor_mappings'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='patient_mappings'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['patient', 'doctor'],
                name='unique_patient_doctor_mapping'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Patient {self.patient_id} -> Doctor {self.doctor_id}"

