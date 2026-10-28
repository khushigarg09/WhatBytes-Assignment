from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.refresh_url = reverse('token_refresh')
        self.valid_user_data = {
            'name': 'Dr. Alice Smith',
            'email': 'alice@healthcare.org',
            'password': 'StrongPassword123!',
        }

    def test_register_success(self):
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'alice@healthcare.org')
        self.assertEqual(response.data['user']['name'], 'Dr. Alice Smith')
        self.assertNotIn('password', response.data['user'])
        self.assertNotIn('password', response.data)
        self.assertTrue(User.objects.filter(email='alice@healthcare.org').exists())

    def test_register_duplicate_email_rejected(self):
        User.objects.create_user(
            email='alice@healthcare.org',
            name='Alice',
            password='StrongPassword123!'
        )
        response = self.client.post(self.register_url, self.valid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_weak_password_rejected(self):
        data = {
            'name': 'Bob',
            'email': 'bob@healthcare.org',
            'password': '123',
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_missing_fields_rejected(self):
        response = self.client.post(self.register_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
        self.assertIn('name', response.data)

    def test_login_success(self):
        User.objects.create_user(
            email='alice@healthcare.org',
            name='Dr. Alice',
            password='StrongPassword123!'
        )
        login_data = {
            'email': 'alice@healthcare.org',
            'password': 'StrongPassword123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_password(self):
        User.objects.create_user(
            email='alice@healthcare.org',
            name='Dr. Alice',
            password='StrongPassword123!'
        )
        login_data = {
            'email': 'alice@healthcare.org',
            'password': 'WrongPassword999'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email(self):
        login_data = {
            'email': 'nobody@healthcare.org',
            'password': 'AnyPassword123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_success(self):
        user = User.objects.create_user(
            email='alice@healthcare.org',
            name='Dr. Alice',
            password='StrongPassword123!'
        )
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        response = self.client.post(self.refresh_url, {'refresh': str(refresh)}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_token_refresh_invalid(self):
        response = self.client.post(self.refresh_url, {'refresh': 'invalid_token_string'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

