from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from item.models import Item, category


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('dueno', password='pass12345')
        self.cat = category.objects.create(name='Sedan')

    def test_requires_login(self):
        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('core:login'), response['Location'])

    def test_lists_newest_first_and_marks_sold(self):
        old = Item.objects.create(category=self.cat, name='Viejo', price=1, created_by=self.user)
        new = Item.objects.create(category=self.cat, name='Nuevo', price=1, created_by=self.user, is_sold=True)
        self.client.login(username='dueno', password='pass12345')

        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(list(response.context['items']), [new, old])
        self.assertContains(response, 'vendido')
