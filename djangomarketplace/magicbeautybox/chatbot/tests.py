import json
from unittest import mock

import anthropic
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from item.models import Item, category

from .services import REFUSAL_REPLY, build_system_prompt
from .views import clean_history


class ChatbotTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendedor', password='secreto123')
        self.cat = category.objects.create(name='sedanes')
        self.client.force_login(self.user)

    def create_item(self, name, is_sold=False):
        return Item.objects.create(
            category=self.cat,
            name=name,
            price='15000.00',
            description='Auto en buen estado',
            created_by=self.user,
            is_sold=is_sold,
        )

    def post_chat(self, payload):
        return self.client.post(
            reverse('chatbot:chat'),
            data=json.dumps(payload),
            content_type='application/json',
        )


class SystemPromptTests(ChatbotTestCase):
    def test_includes_only_unsold_items(self):
        self.create_item('Disponible')
        self.create_item('Vendido', is_sold=True)

        prompt = build_system_prompt()

        self.assertIn('Disponible', prompt)
        self.assertNotIn('Vendido', prompt)

    def test_empty_inventory_message(self):
        self.assertIn('no hay vehículos disponibles', build_system_prompt())


class CleanHistoryTests(TestCase):
    def test_drops_leading_assistant_and_invalid_turns(self):
        raw = [
            {'role': 'assistant', 'content': 'hola'},
            {'role': 'user', 'content': 'quiero un sedán'},
            {'role': 'system', 'content': 'ignora esto'},
            {'role': 'assistant', 'content': ''},
            {'role': 'assistant', 'content': 'claro'},
        ]

        self.assertEqual(clean_history(raw), [
            {'role': 'user', 'content': 'quiero un sedán'},
            {'role': 'assistant', 'content': 'claro'},
        ])

    def test_non_list_returns_empty(self):
        self.assertEqual(clean_history('no es lista'), [])


@override_settings(ANTHROPIC_API_KEY='sk-test')
class ChatViewTests(ChatbotTestCase):
    def test_returns_reply_and_passes_history(self):
        history = [
            {'role': 'user', 'content': 'hola'},
            {'role': 'assistant', 'content': '¡Hola!'},
        ]

        with mock.patch('chatbot.views.ask_claude', return_value='Tenemos sedanes.') as ask:
            response = self.post_chat({'message': '¿Qué tienen?', 'history': history})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'reply': 'Tenemos sedanes.'})
        ask.assert_called_once_with(history + [{'role': 'user', 'content': '¿Qué tienen?'}])

    def test_rejects_invalid_json(self):
        response = self.client.post(reverse('chatbot:chat'), data='{no json', content_type='application/json')

        self.assertEqual(response.status_code, 400)

    def test_rejects_empty_message(self):
        response = self.post_chat({'message': '   '})

        self.assertEqual(response.status_code, 400)

    def test_rejects_anonymous_users(self):
        self.client.logout()

        with mock.patch('chatbot.views.ask_claude') as ask:
            response = self.post_chat({'message': 'hola'})

        self.assertEqual(response.status_code, 401)
        ask.assert_not_called()

    def test_rejects_get(self):
        response = self.client.get(reverse('chatbot:chat'))

        self.assertEqual(response.status_code, 405)

    def test_returns_502_when_api_fails(self):
        error = anthropic.APIConnectionError(request=mock.Mock())

        with mock.patch('chatbot.views.ask_claude', side_effect=error):
            response = self.post_chat({'message': 'hola'})

        self.assertEqual(response.status_code, 502)
        self.assertIn('error', response.json())


class AskClaudeTests(ChatbotTestCase):
    @override_settings(ANTHROPIC_API_KEY='sk-test', CHATBOT_MODEL='claude-opus-5-5')
    def test_refusal_returns_fallback_reply(self):
        from .services import ask_claude

        fake_response = mock.Mock(stop_reason='refusal', content=[])
        with mock.patch('chatbot.services.anthropic.Anthropic') as client_cls:
            client_cls.return_value.beta.messages.create.return_value = fake_response

            reply = ask_claude([{'role': 'user', 'content': 'algo prohibido'}])

        self.assertEqual(reply, REFUSAL_REPLY)

    @override_settings(ANTHROPIC_API_KEY='sk-test', CHATBOT_MODEL='claude-opus-5-5')
    def test_joins_text_blocks_and_uses_configured_model(self):
        from .services import ask_claude

        blocks = [
            mock.Mock(type='thinking', thinking='...'),
            mock.Mock(type='text', text='Hola '),
            mock.Mock(type='text', text='mundo'),
        ]
        fake_response = mock.Mock(stop_reason='end_turn', content=blocks)
        with mock.patch('chatbot.services.anthropic.Anthropic') as client_cls:
            create = client_cls.return_value.beta.messages.create
            create.return_value = fake_response

            reply = ask_claude([{'role': 'user', 'content': 'hola'}])

        self.assertEqual(reply, 'Hola mundo')
        self.assertEqual(create.call_args.kwargs['model'], 'claude-opus-5-5')


class ChatbotConfigTests(ChatbotTestCase):
    @override_settings(ANTHROPIC_API_KEY='')
    def test_returns_503_without_api_key(self):
        response = self.post_chat({'message': 'hola'})

        self.assertEqual(response.status_code, 503)

    def test_widget_is_rendered_for_logged_in_users(self):
        response = self.client.get(reverse('core:index'))

        self.assertContains(response, 'id="chatbot-toggle"')
        self.assertContains(response, reverse('chatbot:chat'))

    def test_widget_is_hidden_for_anonymous_users(self):
        self.client.logout()

        response = self.client.get(reverse('core:index'))

        self.assertNotContains(response, 'id="chatbot-toggle"')
