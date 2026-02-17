from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import cast

from django.utils import timezone
from django.conf import settings

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

# --- HELPERS ---

def _get_system_prompt_for_channel(channel: str) -> str:
    if channel == "telegram":
        return get_telegram_prompt()
    if channel == "whatsapp":
        return get_whatsapp_prompt()
    if channel == "email":
        return get_email_prompt()
    return get_base_system_prompt()

def _is_trello_enabled() -> bool:
    """Verifica si Trello está habilitado en el entorno."""
    return os.getenv("USE_TRELLO", "false").lower() == "true"

# --- NODOS ---

def entry_node(state: AgentState) -> AgentState:
    start_ts = timezone.now()
    state.setdefault("nodes_executed", []).append("entry")

    phone = state["client_data"].get("phone")
    if not phone:
        raise ValueError("Falta phone en client_data para entry_node")

    client_info = query_client_data.invoke({"phone": phone})

    if client_info is None:
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

    conv, _ = Conversation.objects.get_or_create(
        conversation_id=state["conversation_id"],
        defaults={
            "client": client,
            "channel": state["channel"],
            "state": "processing",
            "metadata": state.get("metadata", {}),
        },
    )

    history_qs = conv.messages.order_by("-timestamp")[:10]
    history = [
        {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
        for m in reversed(list(history_qs))
    ]
    state["conversation_history"] = history

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
    Nodo de enrutamiento: Detecta saludos rápidos para ahorrar tokens y
    clasifica la intención del usuario para el flujo de Trello.
    """
    state.setdefault("nodes_executed", []).append("router")
    text = (state.get("user_message") or "").lower().strip()

    # 1. LÓGICA DE SALUDO (Bypass de IA)
    # Solo activamos el bypass si el mensaje es EXCLUSIVAMENTE un saludo corto.
    # Si el texto es largo, dejamos que pase a Gemini para no ignorar la pregunta.
    saludos = ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "buen dia", "saludos"]
    
    es_saludo_puro = any(s == text for s in saludos)
    es_saludo_corto = len(text) < 12 and any(s in text for s in saludos)

    if es_saludo_puro or es_saludo_corto:
        state["ai_response"] = (
            "¡Hola! Soy Fran Bot, tu asistente virtual para el condominio. "
            "¿En qué puedo ayudarte hoy?"
        )
        state["quality_passed"] = True
        state["is_greeting"] = True
        state["detected_intent"] = "saludo"
        return state

    # Si llegamos aquí, NO es un saludo simple (o es un saludo con pregunta)
    state["is_greeting"] = False

    # 2. CLASIFICACIÓN DE INTENCIONES (Para lógica de Trello posterior)
    # Definimos diccionarios de palabras clave para mayor claridad
    keywords = {
        "consulta_deuda": ["deuda", "pago", "debo", "monto", "expensas", "cbu", "alias", "pagué", "comprobante"],
        "solicitud_documento": ["documento", "reglamento", "estatuto", "copia", "acta", "pdf", "archivo"],
        "reporte_problema": ["falla", "problema", "roto", "averia", "limpieza", "ascensor", "luz", "agua", "humedad", "ruido"]
    }

    intent = "desconocido"
    for intent_name, keys in keywords.items():
        if any(k in text for k in keys):
            intent = intent_name
            break # Detenemos en la primera coincidencia clara

    state["detected_intent"] = intent
    
    # Marcamos si necesita RAG (casi siempre que no sea saludo corto)
    state["needs_rag"] = True 
    
    return state


def rag_node(state: AgentState) -> AgentState:
    state.setdefault("nodes_executed", []).append("rag")
    results = search_knowledge_base.invoke(
        {"query": state.get("user_message", ""), "top_k": 3}
    )
    state["rag_results"] = cast(list[dict], results)
    return state


def gemini_processor_node(state: AgentState) -> AgentState:
    import google.generativeai as genai
    state.setdefault("nodes_executed", []).append("gemini")

    multimedia_context = ""
    for attachment in state.get("attachments", []):
        file_url = attachment.get("url")
        file_type = attachment.get("type")
        if not file_url or not file_type: continue

        result = process_multimedia_with_gemini.invoke({
            "file_path_or_url": file_url,
            "file_type": file_type,
            "prompt": "Analiza este archivo para gestión de condominios",
        })

        if file_type == "audio":
            multimedia_context += f"\n[Audio]: {result.get('transcription', '')}"
        elif file_type == "image":
            multimedia_context += f"\n[Imagen]: {result.get('analysis', '')}"
        # ... otros tipos

    rag_snippets = "\n".join([f"- {doc.get('content')}" for doc in state.get("rag_results", [])])
    system_prompt = _get_system_prompt_for_channel(state["channel"])
    
    full_prompt = f"{system_prompt}\n\nCONOCIMIENTO:\n{rag_snippets}\n\nCONTEXTO EXTRA: {multimedia_context}\nUSUARIO: {state.get('user_message')}"

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-flash-latest")
    response = model.generate_content(full_prompt)
    
    state["ai_response"] = response.text
    return state


def quality_check_node(state: AgentState) -> AgentState:
    state.setdefault("nodes_executed", []).append("quality_check")
    text = (state.get("ai_response") or "").strip()
    
    passes = True
    reason = ""
    
    if len(text) < 15:
        passes = False
        reason = "Respuesta demasiado corta"
    elif any(m in text.lower() for m in ["no sé", "no tengo información", "soy un modelo"]):
        passes = False
        reason = "IA no encontró datos"

    state["quality_passed"] = passes
    state["quality_fail_reason"] = reason
    state["quality_score"] = 1.0 if passes else 0.0
    return state


def fallback_node(state: AgentState) -> AgentState:
    state.setdefault("nodes_executed", []).append("fallback")
    state["used_fallback"] = True
    client = state["client_data"]

    response = (
        "Lo siento, tu consulta requiere revisión humana. He registrado un ticket "
        f"y te contactaremos al {client.get('phone')} en menos de 24h."
    )
    state["final_response"] = response

    # CREACIÓN DE TICKET CONDICIONAL
    if _is_trello_enabled():
        title, description = format_trello_ticket_complete(state, category="URGENTE", priority="HIGH")
        create_trello_card.invoke({
            "title": title, "description": description, 
            "category": "intervencion_requerida", "priority": "URGENT"
        })
        state["trello_ticket_created"] = True
        logger.info("Ticket de fallback creado en Trello.")

    return state


def action_planner_node(state: AgentState) -> AgentState:
    start = datetime.utcnow()
    state.setdefault("nodes_executed", []).append("action_planner")
    actions: list[dict] = []
    intent = state.get("detected_intent")
    final_text = state.get("final_response") or state.get("ai_response") or ""

    # 1. ENVÍO POR CANAL
    if state["channel"] == "telegram" and state.get("telegram_chat_id"):
        result = send_telegram_message.invoke({
            "chat_id": state["telegram_chat_id"],
            "text": final_text,
            "parse_mode": "Markdown",
        })
        actions.append({"action": "send_telegram", "success": result.get("success", True)})

    # 2. TRELLO CONDICIONAL (SI NO ES SALUDO Y NO ES FALLBACK)
    if _is_trello_enabled() and not state.get("trello_ticket_created") and intent != "desconocido":
        category_map = {
            "solicitud_documento": ("solicitud_documento", "MEDIUM"),
            "reporte_problema": ("reporte_problema", "HIGH"),
            "consulta_deuda": ("consulta_deuda", "MEDIUM"),
        }
        
        if intent in category_map:
            cat, prio = category_map[intent]
            title, desc = format_trello_ticket_complete(state, category=cat, priority=prio)
            trello_res = create_trello_card.invoke({
                "title": title, "description": desc, "category": cat, "priority": prio
            })
            state["trello_ticket_created"] = True
            actions.append({"action": "create_trello", "id": trello_res.get("id")})

    # 3. PERSISTENCIA EN DB
    conv = Conversation.objects.get(conversation_id=state["conversation_id"])
    Message.objects.create(
        conversation=conv, role="assistant", content=final_text, node_executed="action_planner"
    )

    conv.state = "fallback" if state.get("used_fallback") else "ai_resolved"
    conv.save()

    state["actions_taken"] = actions
    state["execution_time_seconds"] = (datetime.utcnow() - start).total_seconds()
    return state