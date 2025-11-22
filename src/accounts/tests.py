from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from .backends import KeycloakBackend
from .keycloak_service import KeycloakService

class KeycloakBackendTests(TestCase):
    def setUp(self):
        self.backend = KeycloakBackend()
        self.user_info = {
            'preferred_username': 'testuser',
            'email': 'testuser@example.com',
            'given_name': 'Test',
            'family_name': 'User',
        }

    @patch('accounts.backends.KeycloakService')
    def test_authenticate_creates_user(self, MockKeycloakService):
        # Mock the KeycloakService
        mock_service_instance = MockKeycloakService.return_value
        
        # Mock the create_or_update_user method
        mock_user = User(username='testuser', email='testuser@example.com')
        mock_service_instance.create_or_update_user.return_value = mock_user

        # Authenticate the user
        user = self.backend.authenticate(request=None, user_info=self.user_info)

        # Assert that the user was created
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        mock_service_instance.create_or_update_user.assert_called_once_with(self.user_info)

    def test_get_user(self):
        # Create a user
        user = User.objects.create(username='testuser', pk=1)

        # Get the user
        retrieved_user = self.backend.get_user(1)

        # Assert that the correct user was retrieved
        self.assertEqual(user, retrieved_user)
