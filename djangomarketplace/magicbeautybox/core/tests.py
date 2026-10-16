from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class SignupTests(TestCase):
    def test_signup_saves_email_and_hides_passwords(self):
        response = self.client.get(reverse('core:signup'))
        self.assertContains(response, 'type="password"', count=2)

        response = self.client.post(reverse('core:signup'), {
            'username': 'nuevo',
            'email': 'nuevo@example.com',
            'password1': 'UnaClave-Segura123',
            'password2': 'UnaClave-Segura123',
        })
        self.assertRedirects(response, reverse('core:login'))
        self.assertEqual(User.objects.get(username='nuevo').email, 'nuevo@example.com')

    def test_signup_rejects_invalid_email(self):
        response = self.client.post(reverse('core:signup'), {
            'username': 'nuevo',
            'email': 'no-es-email',
            'password1': 'UnaClave-Segura123',
            'password2': 'UnaClave-Segura123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuevo').exists())

    def test_logout(self):
        User.objects.create_user('u', password='pass12345')
        self.client.login(username='u', password='pass12345')
        self.client.post(reverse('core:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
