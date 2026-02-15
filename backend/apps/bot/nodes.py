from __future__ import annotations

import logging
from datetime import datetime
from typing import cast

from django.utils import timezone

from apps.bot.models import Conversation, Message, Client
from apps.bot.prompts import (
    get_base_system_prompt,
    get_telegram_prompt,
    get_whatsapp_prompt,
    get_email_prompt,
)
from apps.bot.state import AgentState
from apps.bot.tools import (
    query_client_data,
    search_knowledge_base,
    process_multimedia_with_gemini,
    create_trello_card,
    format_trello_ticket_complete,
    send_telegram_message,
    send_whatsapp_message,
    create_gmail_draft,
)

logger = logging.getLogger(__name__)


def _get_system_prompt_for_channel(channel: str) -> str:
    if channel == "telegram":
        return get_telegram_prompt()
    if channel == "whatsapp":
        return get_whatsapp_prompt()
    if channel == "email":
        return get_email_prompt()
    return get_base_system_prompt()


def entry_node(state: AgentState) -> AgentState:
    """
    Punto de entrada del grafo.

    1. Valida mensaje.
    2. Carga/crea cliente.
    3. Carga historial reciente.
    4. Persiste mensaje de usuario.
    """
    start_ts = timezone.now()
    state.setdefault("nodes_executed", []).append("entry")

    phone = state["client_data"].get("phone")
    if not phone:
        raise ValueError("Falta phone en client_data para entry_node")

    client_info = query_client_data.invoke({"phone": phone})  # type: ignore[arg-type]

    if client_info is None:
        # Crear cliente mínimo en Django
        client = Client.objects.create(
            name=state["client_data"].get("name", "Desconocido"),
            phone=phone,
            unit_number=state["client_data"].get("unit_number", "N/A"),
        )
        client_info = client.get_contact_info()
        logger.info("Creado cliente nuevo %s", client)
    else:
        client = Client.objects.get(id=client_info["id"])

    state["client_data"] = client_info

    # Obtener/crear conversación
    conv, _ = Conversation.objects.get_or_create(
        conversation_id=state["conversation_id"],
        defaults={
            "client": client,
            "channel": state["channel"],
            "state": "processing",
            "metadata": state.get("metadata", {}),
        },
    )

    # Historial últimos 10 mensajes
    history_qs = conv.messages.order_by("-timestamp")[:10]
    history = [
        {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
        for m in reversed(list(history_qs))
    ]
    state["conversation_history"] = history

    # Guardar mensaje de usuario
    Message.objects.create(
        conversation=conv,
        role="user",
        content=state.get("user_message", ""),
        attachments=state.get("attachments", []),
        node_executed="entry",
    )

    duration = timezone.now() - start_ts
    logger.info("Entry node completado en %.3fs", duration.total_seconds())
    return state


def router_node(state: AgentState) -> AgentState:
    """
    Clasificador simple de intenciones basado en keywords.
    """
    state.setdefault("nodes_executed", []).append("router")
    text = (state.get("user_message") or "").lower()

    intent = "desconocido"
    needs_rag = False

    if any(k in text for k in ["deuda", "debo", "pago", "estado de cuenta"]):
        intent = "consulta_deuda"
        needs_rag = True
    elif any(k in text for k in ["estado de cuenta", "reglamento", "documento"]):
        intent = "solicitud_documento"
        needs_rag = True
    elif any(k in text for k in ["problema", "falla", "elevador", "luz", "agua"]):
        intent = "reporte_problema"
        needs_rag = True
    elif any(k in text for k in ["horario", "piscina", "gimnasio", "administración"]):
        intent = "faq_simple"
        needs_rag = False

    state["detected_intent"] = intent
    state["needs_rag"] = needs_rag
    return state


def direct_response_node(state: AgentState) -> AgentState:
    """
    Respuestas instantáneas para FAQs simples sin IA.
    """
    state.setdefault("nodes_executed", []).append("direct_response")

    faqs = {
        "horario_piscina": "La piscina está disponible de 8:00 AM a 8:00 PM todos los días.",
        "horario_gimnasio": "El gimnasio abre de 6:00 AM a 10:00 PM.",
        "administracion": (
            "La oficina de administración atiende de lunes a viernes de 9:00 AM a 5:00 PM "
            "en el primer piso de la Torre A."
        ),
    }

    msg = (state.get("user_message") or "").lower()
    answer = (
        "Te explico:\n"
        "- Piscina: 8:00 AM – 8:00 PM.\n"
        "- Gimnasio: 6:00 AM – 10:00 PM.\n"
        "- Administración: Lun–Vie 9:00 AM – 5:00 PM en Torre A."
    )

    if "piscina" in msg:
        answer = faqs["horario_piscina"]
    elif "gimnasio" in msg:
        answer = faqs["horario_gimnasio"]
    elif "administr" in msg:
        answer = faqs["administracion"]

    state["ai_response"] = answer
    return state


def rag_node(state: AgentState) -> AgentState:
    """
    Búsqueda simple en base de conocimiento.
    """
    state.setdefault("nodes_executed", []).append("rag")
    results = search_knowledge_base.invoke(  # type: ignore[arg-type]
        {"query": state.get("user_message", ""), "top_k": 3}
    )
    state["rag_results"] = cast(list[dict], results)
    return state


def gemini_processor_node(state: AgentState) -> AgentState:
    """
    Generación de respuesta con Gemini 1.5 Flash.
    """
    import google.generativeai as genai
    from django.conf import settings

    state.setdefault("nodes_executed", []).append("gemini")

    # 1. Procesar multimedia
    multimedia_context = ""
    for attachment in state.get("attachments", []):
        file_url = attachment.get("url")
        file_type = attachment.get("type")
        if not file_url or not file_type:
            continue

        result = process_multimedia_with_gemini.invoke(  # type: ignore[arg-type]
            {
                "file_path_or_url": file_url,
                "file_type": file_type,
                "prompt": "Analiza este archivo en el contexto de gestión de condominios",
            }
        )

        if file_type == "audio":
            transcription = result.get("transcription", "")
            multimedia_context += f"\n[Audio transcrito]: {transcription}"
            if not state.get("user_message"):
                state["user_message"] = transcription
        elif file_type == "image":
            multimedia_context += f"\n[Imagen analizada]: {result.get('analysis', '')}"
        elif file_type == "pdf":
            extracted = result.get("extracted_text", "")[:500]
            multimedia_context += f"\n[PDF extraído]: {extracted}..."
        elif file_type == "video":
            multimedia_context += f"\n[Video analizado]: {result.get('analysis', '')}"

    # 2. Construir prompt
    channel = state["channel"]
    system_prompt = _get_system_prompt_for_channel(channel)

    rag_snippets = ""
    for doc in state.get("rag_results", []):
        rag_snippets += f"\n### {doc.get('title')}\n{doc.get('content')}\n"

    history_lines = []
    for h in state.get("conversation_history", []):
        history_lines.append(f"{h['role']}: {h['content']}")
    history_text = "\n".join(history_lines)

    full_prompt = f"""
{system_prompt}

Contexto del cliente:
{state.get('client_data')}

Documentos relevantes (RAG):
{rag_snippets}

Contexto multimedia:
{multimedia_context}

Historial de conversación:
{history_text}

Mensaje actual del usuario:
{state.get('user_message')}

Genera una respuesta útil, precisa y centrada en la gestión del condominio.
"""

    # 3. Llamar a Gemini
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(full_prompt)
    state["ai_response"] = response.text
    return state


def quality_check_node(state: AgentState) -> AgentState:
    """
    Valida calidad de la respuesta generada.
    """
    state.setdefault("nodes_executed", []).append("quality_check")

    text = (state.get("ai_response") or "").strip()
    user_msg = (state.get("user_message") or "").strip()

    passes = True
    reason = ""
    score = 1.0

    low_markers = ["no sé", "no puedo", "no tengo información", "soy un modelo"]
    if len(text) < 20:
        passes = False
        reason = "Respuesta demasiado corta"
        score = 0.2
    elif any(m in text.lower() for m in low_markers):
        passes = False
        reason = "Respuesta indica falta de capacidad"
        score = 0.3
    elif text.lower().startswith(user_msg.lower()[:30]):
        passes = False
        reason = "Respuesta parece repetir la pregunta"
        score = 0.4

    state["quality_passed"] = passes
    state["quality_score"] = score
    state["quality_fail_reason"] = reason
    return state


def fallback_node(state: AgentState) -> AgentState:
    """
    Manejo de casos donde IA no puede resolver.
    """
    state.setdefault("nodes_executed", []).append("fallback")

    channel = state["channel"]
    client = state["client_data"]

    if channel in ("telegram", "whatsapp"):
        response = (
            "Lo siento, tu consulta requiere una revisión más detallada por parte "
            "de la administración del condominio. Registraremos un ticket PRIORITARIO "
            "y se comunicarán contigo en las próximas 24 horas al teléfono "
            f"{client.get('phone')}.\n\n"
            "Si se trata de una emergencia (luz, agua, seguridad), por favor llama "
            "inmediatamente al 📞 (01) 234-5678."
        )
    else:
        response = (
            "Estimado(a),\n\n"
            "Tu consulta requiere una revisión más detallada por parte de la "
            "administración del condominio. Hemos registrado un ticket prioritario "
            "y nos pondremos en contacto contigo en las próximas 24 horas.\n\n"
            "Saludos cordiales,\nAdministración del condominio"
        )

    state["final_response"] = response
    state["used_fallback"] = True
    state["fallback_reason"] = state.get("quality_fail_reason", "Calidad insuficiente")

    # Crear ticket Trello URGENTE
    title, description = format_trello_ticket_complete(
        state, category="intervencion_requerida", priority="URGENT"
    )
    trello_result = create_trello_card.invoke(  # type: ignore[arg-type]
        {
            "title": title,
            "description": description,
            "category": "intervencion_requerida",
            "priority": "URGENT",
        }
    )

    state["trello_ticket_created"] = True
    state["trello_ticket_data"] = trello_result

    return state


def action_planner_node(state: AgentState) -> AgentState:
    """
    Planificador de acciones finales: envío por canal + tickets Trello.
    """
    start = datetime.utcnow()
    state.setdefault("nodes_executed", []).append("action_planner")
    actions: list[dict] = []

    conv = Conversation.objects.get(conversation_id=state["conversation_id"])

    # Determinar texto final
    final_text = state.get("final_response") or state.get("ai_response") or ""
    state["final_response"] = final_text

    # 1. Enviar por canal
    if state["channel"] == "telegram" and state.get("telegram_chat_id"):
        result = send_telegram_message.invoke(  # type: ignore[arg-type]
            {
                "chat_id": state["telegram_chat_id"],
                "text": final_text,
                "parse_mode": "Markdown",
            }
        )
        actions.append(
            {
                "action": "send_message",
                "channel": "telegram",
                "success": result.get("success", True),
                "message_id": result.get("message_id"),
            }
        )
    elif state["channel"] == "whatsapp":
        result = send_whatsapp_message.invoke(  # type: ignore[arg-type]
            {"phone": state["client_data"]["phone"], "text": final_text}
        )
        actions.append(
            {
                "action": "send_message",
                "channel": "whatsapp",
                "success": result.get("success", True),
                "message_id": result.get("message_id"),
            }
        )
    elif state["channel"] == "email" and state["client_data"].get("email"):
        result = create_gmail_draft.invoke(  # type: ignore[arg-type]
            {
                "to": state["client_data"]["email"],
                "subject": "Respuesta automática - Fran Bot",
                "body": final_text,
            }
        )
        actions.append(
            {
                "action": "create_draft",
                "channel": "email",
                "success": True,
                "draft_id": result.get("draft_id"),
                "url": result.get("url"),
            }
        )

    # 2. Crear ticket Trello si aplica (no fallback)
    intent = state.get("detected_intent", "desconocido")
    if not state.get("used_fallback"):
        category = None
        priority = "MEDIUM"
        if intent == "solicitud_documento":
            category = "solicitud_documento"
            priority = "MEDIUM"
        elif intent == "reporte_problema":
            category = "reporte_problema"
            priority = "HIGH"
        elif intent == "consulta_deuda":
            category = "consulta_deuda"
            priority = "MEDIUM"

        if category:
            title, description = format_trello_ticket_complete(
                state, category=category, priority=priority
            )
            trello_result = create_trello_card.invoke(  # type: ignore[arg-type]
                {
                    "title": title,
                    "description": description,
                    "category": category,
                    "priority": priority,
                }
            )
            state["trello_ticket_created"] = True
            state["trello_ticket_data"] = trello_result
            actions.append(
                {
                    "action": "create_trello_ticket",
                    "success": True,
                    "ticket_id": trello_result.get("id"),
                    "ticket_url": trello_result.get("url"),
                    "priority": priority,
                }
            )

    # 3. Guardar mensaje de asistente y actualizar conversación
    Message.objects.create(
        conversation=conv,
        role="assistant",
        content=final_text,
        attachments=[],
        node_executed="action_planner",
    )

    conv.state = "fallback" if state.get("used_fallback") else "ai_resolved"
    conv.used_fallback = state.get("used_fallback", False)
    conv.fallback_reason = state.get("fallback_reason")
    conv.quality_score = state.get("quality_score")
    conv.processing_time_seconds = float(
        state.get("execution_time_seconds", 0.0)
    )
    if conv.state in ("fallback", "ai_resolved"):
        conv.resolved_at = timezone.now()
    conv.context = {
        "detected_intent": intent,
        "rag_results_count": len(state.get("rag_results", [])),
    }
    conv.save(update_fields=["state", "used_fallback", "fallback_reason",
                             "quality_score", "processing_time_seconds",
                             "resolved_at", "context", "updated_at"])

    state["actions_taken"] = actions
    end = datetime.utcnow()
    state["execution_time_seconds"] = state.get("execution_time_seconds", 0.0) + (
        end - start
    ).total_seconds()

    return state

