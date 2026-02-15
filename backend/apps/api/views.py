from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict

from django.http import HttpRequest, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from apps.bot.tasks import process_message_task

logger = logging.getLogger(__name__)


def _enqueue_normalized_message(payload: Dict[str, Any]) -> None:
    """
    Encolar mensaje normalizado en Celery.
    """
    process_message_task.delay(payload)


@csrf_exempt
def telegram_webhook(request: HttpRequest) -> HttpResponse:
    """
    Webhook para desarrollo vía Telegram.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    logger.info("📥 Telegram webhook recibido: %s", body)

    message = body.get("message") or {}
    chat = message.get("chat") or {}

    text = message.get("text") or ""
    chat_id = str(chat.get("id"))

    conversation_id = str(chat_id)
    message_id = str(message.get("message_id") or uuid.uuid4())

    payload: Dict[str, Any] = {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "channel": "telegram",
        "user_message": text,
        "attachments": [],
        "client_data": {
            "phone": chat_id,  # en dev usamos chat_id como identificador único
            "name": chat.get("first_name") or "Usuario Telegram",
            "unit_number": "N/A",
        },
        "telegram_chat_id": chat_id,
        "telegram_message_id": message.get("message_id"),
        "conversation_history": [],
        "detected_intent": "desconocido",
        "needs_rag": False,
        "rag_results": [],
        "ai_response": "",
        "quality_passed": False,
        "quality_score": 0.0,
        "quality_fail_reason": "",
        "used_fallback": False,
        "fallback_reason": "",
        "final_response": "",
        "actions_taken": [],
        "trello_ticket_created": False,
        "trello_ticket_data": None,
        "metadata": {"raw_telegram": body},
        "timestamp": "",
        "execution_time_seconds": 0.0,
        "nodes_executed": [],
    }

    _enqueue_normalized_message(payload)
    return JsonResponse({"status": "queued"}, status=202)


@csrf_exempt
def whatsapp_webhook(request: HttpRequest) -> HttpResponse:
    """
    Webhook para WhatsApp Business (producción).

    Implementación mínima; se asume payload estándar de Meta.
    """
    if request.method == "GET":
        # Verificación de webhook
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        from django.conf import settings

        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge or "")
        return HttpResponse("Error de verificación", status=403)

    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    logger.info("📥 WhatsApp webhook recibido: %s", body)

    # Simplificación: tomar primer mensaje del primer entry
    try:
        entry = body["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        message = value["messages"][0]
        contact = value["contacts"][0]
    except (KeyError, IndexError):
        logger.warning("Payload WhatsApp inesperado")
        return JsonResponse({"detail": "payload inesperado"}, status=400)

    from_number = message.get("from")
    text = ""
    if message.get("type") == "text":
        text = message["text"]["body"]

    conversation_id = from_number
    message_id = message.get("id") or str(uuid.uuid4())

    payload = {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "channel": "whatsapp",
        "user_message": text,
        "attachments": [],
        "client_data": {
            "phone": f"+{from_number}",
            "name": contact.get("profile", {}).get("name", "Usuario WhatsApp"),
            "unit_number": "N/A",
        },
        "whatsapp_message_id": message.get("id"),
        "conversation_history": [],
        "detected_intent": "desconocido",
        "needs_rag": False,
        "rag_results": [],
        "ai_response": "",
        "quality_passed": False,
        "quality_score": 0.0,
        "quality_fail_reason": "",
        "used_fallback": False,
        "fallback_reason": "",
        "final_response": "",
        "actions_taken": [],
        "trello_ticket_created": False,
        "trello_ticket_data": None,
        "metadata": {"raw_whatsapp": body},
        "timestamp": "",
        "execution_time_seconds": 0.0,
        "nodes_executed": [],
    }

    _enqueue_normalized_message(payload)
    return JsonResponse({"status": "queued"}, status=202)


@csrf_exempt
def gmail_webhook(request: HttpRequest) -> HttpResponse:
    """
    Webhook para Gmail (solo modo draft).

    En esta versión se asume que otra integración convierte el email
    en un JSON con los campos básicos.
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Método no permitido"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido"}, status=400)

    logger.info("📥 Gmail webhook recibido: %s", body)

    email_from = body.get("from_email")
    text = body.get("text", "")
    gmail_message_id = body.get("message_id") or str(uuid.uuid4())

    if not email_from:
        return JsonResponse({"detail": "Falta from_email"}, status=400)

    conversation_id = email_from
    payload = {
        "conversation_id": conversation_id,
        "message_id": gmail_message_id,
        "channel": "email",
        "user_message": text,
        "attachments": [],
        "client_data": {
            "phone": "",
            "email": email_from,
            "name": body.get("from_name", "Usuario Email"),
            "unit_number": "N/A",
        },
        "gmail_message_id": gmail_message_id,
        "conversation_history": [],
        "detected_intent": "desconocido",
        "needs_rag": False,
        "rag_results": [],
        "ai_response": "",
        "quality_passed": False,
        "quality_score": 0.0,
        "quality_fail_reason": "",
        "used_fallback": False,
        "fallback_reason": "",
        "final_response": "",
        "actions_taken": [],
        "trello_ticket_created": False,
        "trello_ticket_data": None,
        "metadata": {"raw_gmail": body},
        "timestamp": "",
        "execution_time_seconds": 0.0,
        "nodes_executed": [],
    }

    _enqueue_normalized_message(payload)
    return JsonResponse({"status": "queued"}, status=202)

