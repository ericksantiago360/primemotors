from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import category, Item


class ItemViewsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='pass12345')
        self.other = User.objects.create_user('other', password='pass12345')
        self.category = category.objects.create(name='Sedan')
        self.item = Item.objects.create(category=self.category, name='Civic', price=100, created_by=self.owner)

    def test_pages_render_items_without_image(self):
        for url in [reverse('core:index'), reverse('item:items'), reverse('item:detail', args=[self.item.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_items_invalid_category_does_not_crash(self):
        response = self.client.get(reverse('item:items'), {'category': 'abc'})
        self.assertEqual(response.status_code, 200)

    def test_delete_requires_post(self):
        self.client.login(username='owner', password='pass12345')
        response = self.client.get(reverse('item:delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

        self.client.post(reverse('item:delete', args=[self.item.pk]))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_cannot_delete_other_users_item(self):
        self.client.login(username='other', password='pass12345')
        response = self.client.post(reverse('item:delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 404)
