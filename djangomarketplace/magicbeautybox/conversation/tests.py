from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from item.models import category, Item

from .models import Conversation


class ConversationViewsTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user('seller', password='pass12345')
        self.buyer = User.objects.create_user('buyer', password='pass12345')
        self.outsider = User.objects.create_user('outsider', password='pass12345')
        cat = category.objects.create(name='SUV')
        self.item = Item.objects.create(category=cat, name='RAV4', price=200, created_by=self.seller)

    def test_new_conversation_redirects_to_conversation(self):
        self.client.login(username='buyer', password='pass12345')
        response = self.client.post(reverse('conversation:new', args=[self.item.pk]), {'content': 'Hola'})
        conversation = Conversation.objects.get()
        self.assertRedirects(response, reverse('conversation:detail', args=[conversation.pk]))
        self.assertEqual(conversation.members.count(), 2)

        self.assertEqual(self.client.get(reverse('conversation:inbox')).status_code, 200)

    def test_non_member_gets_404(self):
        conversation = Conversation.objects.create(item=self.item)
        conversation.members.add(self.seller, self.buyer)

        self.client.login(username='outsider', password='pass12345')
        response = self.client.get(reverse('conversation:detail', args=[conversation.pk]))
        self.assertEqual(response.status_code, 404)
