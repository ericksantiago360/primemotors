import json
import logging

import anthropic
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import ask_claude

logger = logging.getLogger(__name__)

MAX_HISTORY = 20
MAX_MESSAGE_CHARS = 1000


def clean_history(raw):
    if not isinstance(raw, list):
        return []

    cleaned = []
    for turn in raw[-MAX_HISTORY:]:
        if (
            isinstance(turn, dict)
            and turn.get('role') in ('user', 'assistant')
            and isinstance(turn.get('content'), str)
            and turn['content'].strip()
        ):
            cleaned.append({'role': turn['role'], 'content': turn['content'][:MAX_MESSAGE_CHARS]})

    # La API exige que la conversación empiece con un mensaje del usuario
    while cleaned and cleaned[0]['role'] != 'user':
        cleaned.pop(0)

    return cleaned


@require_POST
def chat(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Inicia sesión para usar el chatbot.'}, status=401)

    if not settings.ANTHROPIC_API_KEY:
        return JsonResponse({'error': 'El chatbot no está configurado.'}, status=503)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'El cuerpo debe ser JSON válido.'}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({'error': 'El cuerpo debe ser un objeto JSON.'}, status=400)

    message = str(data.get('message', '')).strip()
    if not message or len(message) > MAX_MESSAGE_CHARS:
        return JsonResponse({'error': f'El mensaje debe tener entre 1 y {MAX_MESSAGE_CHARS} caracteres.'}, status=400)

    messages = clean_history(data.get('history')) + [{'role': 'user', 'content': message}]

    try:
        reply = ask_claude(messages)
    except anthropic.APIError:
        logger.exception('Error al consultar la API de Claude')
        return JsonResponse({'error': 'No pude responder en este momento.'}, status=502)

    return JsonResponse({'reply': reply})
