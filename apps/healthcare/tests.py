from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Patient, Doctor, PatientDoctorMapping

User = get_user_model()


class HealthcareAPITests(APITestCase):
    def setUp(self):
        # User 1
        self.user1 = User.objects.create_user(
            email='user1@healthcare.org',
            name='User One',
            password='Password123!'
        )
        refresh1 = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh1.access_token)

        # User 2
        self.user2 = User.objects.create_user(
            email='user2@healthcare.org',
            name='User Two',
            password='Password123!'
        )
        refresh2 = RefreshToken.for_user(self.user2)
        self.token2 = str(refresh2.access_token)

        # Sample patient for user 1
        self.patient1 = Patient.objects.create(
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 1, 1),
            gender='Male',
            phone='1234567890',
            email='john.doe@example.com',
            address='123 Main St',
            created_by=self.user1
        )

        # Sample doctor for user 1
        self.doctor1 = Doctor.objects.create(
            first_name='Sarah',
            last_name='Smith',
            specialization='Cardiology',
            phone='0987654321',
            email='dr.smith@example.com',
            created_by=self.user1
        )

        # Sample patient for user 2
        self.patient2 = Patient.objects.create(
            first_name='Jane',
            last_name='Roe',
            date_of_birth=date(1995, 5, 5),
            gender='Female',
            phone='5555555555',
            email='jane.roe@example.com',
            address='456 Elm St',
            created_by=self.user2
        )

        # Sample doctor for user 2
        self.doctor2 = Doctor.objects.create(
            first_name='Gregory',
            last_name='House',
            specialization='Diagnostics',
            phone='6666666666',
            email='dr.house@example.com',
            created_by=self.user2
        )

    def auth_client(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def clear_auth(self):
        self.client.credentials()

    # ========================================================================
    # 1. Unauthenticated Requests Rejected
    # ========================================================================

    def test_unauthenticated_requests_rejected(self):
        self.clear_auth()
        endpoints = [
            ('get', reverse('patient_list_create')),
            ('post', reverse('patient_list_create')),
            ('get', reverse('patient_detail', kwargs={'pk': self.patient1.id})),
            ('put', reverse('patient_detail', kwargs={'pk': self.patient1.id})),
            ('delete', reverse('patient_detail', kwargs={'pk': self.patient1.id})),
            ('get', reverse('doctor_list_create')),
            ('post', reverse('doctor_list_create')),
            ('get', reverse('doctor_detail', kwargs={'pk': self.doctor1.id})),
            ('put', reverse('doctor_detail', kwargs={'pk': self.doctor1.id})),
            ('delete', reverse('doctor_detail', kwargs={'pk': self.doctor1.id})),
            ('get', reverse('mapping_list_create')),
            ('post', reverse('mapping_list_create')),
            ('get', reverse('mapping_detail', kwargs={'pk': self.patient1.id})),
            ('delete', reverse('mapping_detail', kwargs={'pk': 1})),
        ]
        for method, url in endpoints:
            handler = getattr(self.client, method)
            response = handler(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED,
                f"Expected 401 for unauthenticated {method.upper()} {url}, got {response.status_code}"
            )
            self.assertIn('detail', response.data)

    # ========================================================================
    # 2. Patient CRUD & Ownership Isolation
    # ========================================================================

    def test_create_patient_success(self):
        self.auth_client(self.token1)
        data = {
            'first_name': 'Michael',
            'last_name': 'Scott',
            'date_of_birth': '1980-03-15',
            'gender': 'Male',
            'phone': '1112223333',
            'email': 'michael@dundermifflin.com',
            'address': 'Scranton, PA',
        }
        response = self.client.post(reverse('patient_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Michael')
        self.assertEqual(response.data['created_by'], self.user1.id)

    def test_patient_date_of_birth_future_rejected(self):
        self.auth_client(self.token1)
        future_date = (date.today() + timedelta(days=10)).isoformat()
        data = {
            'first_name': 'Baby',
            'last_name': 'Future',
            'date_of_birth': future_date,
            'gender': 'Female',
            'phone': '1234567890',
            'email': 'baby@future.com',
            'address': 'Nowhere',
        }
        response = self.client.post(reverse('patient_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date_of_birth', response.data)

    def test_patient_list_ownership_isolation(self):
        self.auth_client(self.token1)
        response = self.client.get(reverse('patient_list_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see patient1, NOT patient2
        patient_ids = [p['id'] for p in response.data]
        self.assertIn(self.patient1.id, patient_ids)
        self.assertNotIn(self.patient2.id, patient_ids)

    def test_patient_retrieve_own_success(self):
        self.auth_client(self.token1)
        response = self.client.get(reverse('patient_detail', kwargs={'pk': self.patient1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')

    def test_patient_retrieve_other_user_returns_404(self):
        self.auth_client(self.token1)
        # User 1 attempts to retrieve User 2's patient -> must return 404, not 403
        response = self.client.get(reverse('patient_detail', kwargs={'pk': self.patient2.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_update_own_success(self):
        self.auth_client(self.token1)
        data = {
            'first_name': 'Johnny',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'gender': 'Male',
            'phone': '9998887777',
            'email': 'johnny.updated@example.com',
            'address': '789 Pine St',
        }
        response = self.client.put(reverse('patient_detail', kwargs={'pk': self.patient1.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.patient1.refresh_from_db()
        self.assertEqual(self.patient1.first_name, 'Johnny')
        self.assertEqual(self.patient1.phone, '9998887777')

    def test_patient_update_other_user_returns_404(self):
        self.auth_client(self.token1)
        data = {
            'first_name': 'Hacked',
            'last_name': 'Roe',
            'date_of_birth': '1995-05-05',
            'gender': 'Female',
            'phone': '5555555555',
            'email': 'jane.roe@example.com',
            'address': '456 Elm St',
        }
        response = self.client.put(reverse('patient_detail', kwargs={'pk': self.patient2.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patient_delete_own_success(self):
        self.auth_client(self.token1)
        response = self.client.delete(reverse('patient_detail', kwargs={'pk': self.patient1.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Patient.objects.filter(id=self.patient1.id).exists())

    def test_patient_delete_other_user_returns_404(self):
        self.auth_client(self.token1)
        response = self.client.delete(reverse('patient_detail', kwargs={'pk': self.patient2.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Patient.objects.filter(id=self.patient2.id).exists())

    # ========================================================================
    # 3. Doctor CRUD & Ownership Isolation
    # ========================================================================

    def test_create_doctor_success(self):
        self.auth_client(self.token1)
        data = {
            'first_name': 'Stephen',
            'last_name': 'Strange',
            'specialization': 'Neurosurgy',
            'phone': '1234445555',
            'email': 'dr.strange@sanctum.org',
        }
        response = self.client.post(reverse('doctor_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Stephen')
        self.assertEqual(response.data['created_by'], self.user1.id)

    def test_doctor_list_retrieves_all_doctors(self):
        self.auth_client(self.token1)
        response = self.client.get(reverse('doctor_list_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doctor_ids = [d['id'] for d in response.data]
        # GET /api/doctors/ returns all doctors as per specification
        self.assertIn(self.doctor1.id, doctor_ids)
        self.assertIn(self.doctor2.id, doctor_ids)

    def test_doctor_retrieve_own_success(self):
        self.auth_client(self.token1)
        response = self.client.get(reverse('doctor_detail', kwargs={'pk': self.doctor1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Sarah')

    def test_doctor_retrieve_other_user_returns_404(self):
        self.auth_client(self.token1)
        response = self.client.get(reverse('doctor_detail', kwargs={'pk': self.doctor2.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_doctor_update_own_success(self):
        self.auth_client(self.token1)
        data = {
            'first_name': 'Sarah',
            'last_name': 'Connor',
            'specialization': 'Cardiology',
            'phone': '0987654321',
            'email': 'dr.connor@example.com',
        }
        response = self.client.put(reverse('doctor_detail', kwargs={'pk': self.doctor1.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.doctor1.refresh_from_db()
        self.assertEqual(self.doctor1.last_name, 'Connor')

    def test_doctor_update_other_user_returns_404(self):
        self.auth_client(self.token1)
        data = {
            'first_name': 'Greg',
            'last_name': 'House',
            'specialization': 'Diagnostics',
            'phone': '6666666666',
            'email': 'dr.house@example.com',
        }
        response = self.client.put(reverse('doctor_detail', kwargs={'pk': self.doctor2.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_doctor_delete_own_success(self):
        self.auth_client(self.token1)
        response = self.client.delete(reverse('doctor_detail', kwargs={'pk': self.doctor1.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Doctor.objects.filter(id=self.doctor1.id).exists())

    def test_doctor_delete_other_user_returns_404(self):
        self.auth_client(self.token1)
        response = self.client.delete(reverse('doctor_detail', kwargs={'pk': self.doctor2.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Doctor.objects.filter(id=self.doctor2.id).exists())

    # ========================================================================
    # 4. Mappings: Creation, Duplication, Isolation, Querying, Deletion
    # ========================================================================

    def test_create_mapping_success(self):
        self.auth_client(self.token1)
        data = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id,
        }
        response = self.client.post(reverse('mapping_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['patient']['id'], self.patient1.id)
        self.assertEqual(response.data['doctor']['id'], self.doctor1.id)
        self.assertTrue(
            PatientDoctorMapping.objects.filter(
                patient=self.patient1,
                doctor=self.doctor1
            ).exists()
        )

    def test_prevent_duplicate_mapping(self):
        self.auth_client(self.token1)
        PatientDoctorMapping.objects.create(
            patient=self.patient1,
            doctor=self.doctor1
        )
        data = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor1.id,
        }
        response = self.client.post(reverse('mapping_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mapping_with_other_user_patient_rejected_and_hidden(self):
        self.auth_client(self.token1)
        # Attempt to map User 2's patient to User 1's doctor -> must return 404
        data = {
            'patient_id': self.patient2.id,
            'doctor_id': self.doctor1.id,
        }
        response = self.client.post(reverse('mapping_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mapping_with_other_user_doctor_rejected_and_hidden(self):
        self.auth_client(self.token1)
        # Attempt to map User 1's patient to User 2's doctor -> must return 404
        data = {
            'patient_id': self.patient1.id,
            'doctor_id': self.doctor2.id,
        }
        response = self.client.post(reverse('mapping_list_create'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mapping_list_contains_nested_details_and_isolation(self):
        # Create mapping for user 1
        m1 = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        # Create mapping for user 2
        m2 = PatientDoctorMapping.objects.create(patient=self.patient2, doctor=self.doctor2)

        self.auth_client(self.token1)
        response = self.client.get(reverse('mapping_list_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        mapping_ids = [m['id'] for m in response.data]
        self.assertIn(m1.id, mapping_ids)
        self.assertNotIn(m2.id, mapping_ids)

        # Verify nested concise patient and doctor details
        first_mapping = response.data[0]
        self.assertIn('patient', first_mapping)
        self.assertIn('doctor', first_mapping)
        self.assertEqual(first_mapping['patient']['id'], self.patient1.id)
        self.assertEqual(first_mapping['doctor']['id'], self.doctor1.id)
        self.assertEqual(first_mapping['patient']['first_name'], self.patient1.first_name)
        self.assertEqual(first_mapping['doctor']['specialization'], self.doctor1.specialization)

    def test_get_doctors_assigned_to_owned_patient(self):
        # Create a second doctor for user 1
        doctor1_b = Doctor.objects.create(
            first_name='Leonard',
            last_name='McCoy',
            specialization='General Medicine',
            phone='7778889999',
            email='mccoy@enterprise.org',
            created_by=self.user1
        )
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        PatientDoctorMapping.objects.create(patient=self.patient1, doctor=doctor1_b)

        self.auth_client(self.token1)
        response = self.client.get(reverse('mapping_detail', kwargs={'pk': self.patient1.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        returned_doctor_ids = [d['id'] for d in response.data]
        self.assertIn(self.doctor1.id, returned_doctor_ids)
        self.assertIn(doctor1_b.id, returned_doctor_ids)

    def test_get_doctors_for_other_user_patient_returns_404(self):
        self.auth_client(self.token1)
        # User 1 queries doctors for User 2's patient
        response = self.client.get(reverse('mapping_detail', kwargs={'pk': self.patient2.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_mapping_own_success(self):
        m = PatientDoctorMapping.objects.create(patient=self.patient1, doctor=self.doctor1)
        self.auth_client(self.token1)
        response = self.client.delete(reverse('mapping_detail', kwargs={'pk': m.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PatientDoctorMapping.objects.filter(id=m.id).exists())

    def test_delete_mapping_other_user_returns_404(self):
        m2 = PatientDoctorMapping.objects.create(patient=self.patient2, doctor=self.doctor2)
        self.auth_client(self.token1)
        response = self.client.delete(reverse('mapping_detail', kwargs={'pk': m2.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(PatientDoctorMapping.objects.filter(id=m2.id).exists())

