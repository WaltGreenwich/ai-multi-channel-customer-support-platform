from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from langchain_core.tools import tool

from apps.bot.state import AgentState

logger = logging.getLogger(__name__)


@tool
def query_client_data(phone: str) -> Optional[dict]:
    """
    Consultar datos del cliente en DB o Supabase.

    Args:
        phone: Teléfono del cliente (formato: +51987654321)

    Returns:
        Dict con datos del cliente o None si no existe.
    """
    from apps.bot.models import Client
    from apps.integrations.supabase_client import supabase_client

    # Intentar con Supabase primero (si está habilitado)
    if supabase_client.use_supabase:
        result = supabase_client.get_client_by_phone(phone)
        if result:
            return result

    # Fallback a Django ORM (desarrollo)
    try:
        client = Client.objects.get(phone=phone)
        return client.get_contact_info()
    except Client.DoesNotExist:
        logger.warning("Cliente no encontrado: %s", phone)
        return None


@tool
def search_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
    """
    Buscar en base de conocimiento (RAG).

    Desarrollo: mock en memoria.
    Producción: se puede conectar a Supabase Vector Store.
    """
    from apps.integrations.supabase_client import supabase_client

    # TODO: usar embeddings de Supabase en producción
    _ = supabase_client  # evitar warning de variable sin usar

    mock_knowledge = {
        "reglamento": {
            "title": "Reglamento Interno del Condominio",
            "content": """
El horario de uso de áreas comunes es:
- Piscina: 8:00 AM - 8:00 PM
- Gimnasio: 6:00 AM - 10:00 PM
- Salón de eventos: Reserva previa

Pagos de mantenimiento:
- Vencimiento: Día 5 de cada mes
- Métodos: Transferencia, efectivo, tarjeta
- Mora: 5% después del día 10
""",
            "category": "reglamento",
        },
        "pagos": {
            "title": "Política de Pagos",
            "content": """
Formas de pago:
1. Transferencia bancaria: Cuenta BCP 123-456-789
2. Efectivo en administración: Lun-Vie 9AM-5PM
3. Tarjeta en administración

Para consultar deuda: admin@condominio.com
""",
            "category": "pagos",
        },
        "mantenimiento": {
            "title": "Reporte de Problemas",
            "content": """
Para reportar fallas:
1. Emergencias (luz, agua): (01) 234-5678 (24/7)
2. Mantenimiento general: WhatsApp +51987654321
3. Administración: admin@condominio.com

Tiempo de respuesta: 24-48 horas
""",
            "category": "mantenimiento",
        },
    }

    query_lower = query.lower()
    results: list[dict] = []

    for doc_id, doc in mock_knowledge.items():
        score = 0.0

        if any(k in query_lower for k in ["horario", "piscina", "gimnasio"]):
            if doc_id == "reglamento":
                score = 0.9
        if any(k in query_lower for k in ["pago", "deuda", "debo"]):
            if doc_id == "pagos":
                score = 0.95
        if any(k in query_lower for k in ["problema", "falla", "elevador", "luz"]):
            if doc_id == "mantenimiento":
                score = 0.92

        if score > 0:
            results.append(
                {
                    "title": doc["title"],
                    "content": doc["content"],
                    "category": doc["category"],
                    "relevance_score": score,
                }
            )

    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_k]


@tool
def create_trello_card(
    title: str,
    description: str,
    category: str,
    priority: str = "MEDIUM",
    labels: Optional[list[str]] = None,
) -> dict:
    """
    Crear ticket en Trello con formato completo.
    """
    from apps.integrations.trello_client import trello_client

    logger.info("📋 Creando ticket Trello: %s", title)

    emoji_map = {
        "consulta_deuda": "💳",
        "solicitud_documento": "📄",
        "reporte_problema": "🔧",
        "intervencion_requerida": "🚨",
    }
    emoji = emoji_map.get(category, "📋")
    full_title = f"{emoji} {title}"

    result = trello_client.create_card(
        title=full_title,
        description=description,
        priority=priority,
        labels=labels or [category, priority.lower()],
    )

    logger.info("✅ Ticket creado: %s", result.get("id", "mock-id"))
    return result


@tool
def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> dict:
    """
    Enviar mensaje por Telegram Bot API.
    """
    from apps.integrations.telegram_client import telegram_client

    logger.info("📱 Enviando mensaje Telegram a chat %s", chat_id)
    result = telegram_client.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
    logger.info("✅ Mensaje Telegram enviado: %s", result.get("message_id"))
    return result


@tool
def send_whatsapp_message(phone: str, text: str) -> dict:
    """
    Enviar mensaje por WhatsApp Business API.
    """
    from apps.integrations.whatsapp_client import whatsapp_client

    logger.info("💬 Enviando mensaje WhatsApp a %s", phone)

    if not whatsapp_client.enabled:
        logger.info("ℹ️ WhatsApp en modo mock (desarrollo)")
        return {
            "success": True,
            "message_id": f"mock-wa-{phone}",
            "status": "mock_sent",
        }

    result = whatsapp_client.send_message(phone=phone, text=text)
    logger.info("✅ Mensaje WhatsApp enviado: %s", result.get("message_id"))
    return result


@tool
def create_gmail_draft(to: str, subject: str, body: str) -> dict:
    """
    ⚠️ CRÍTICO: Crear borrador de email - NUNCA enviar automáticamente.
    """
    from apps.integrations.gmail_client import gmail_client

    logger.info("📧 Creando borrador Gmail para %s", to)
    logger.warning("⚠️ MODO BORRADOR: Email NO será enviado automáticamente")

    if not gmail_client.enabled:
        logger.info("ℹ️ Gmail en modo mock (desarrollo)")
        return {
            "draft_id": f"mock-draft-{to}",
            "url": "https://mail.google.com/mail/u/0/#drafts/mock",
            "is_draft": True,
            "sent": False,
            "status": "mock_draft_created",
        }

    result = gmail_client.create_draft(to=to, subject=subject, body=body)
    logger.info("✅ Borrador creado: %s", result.get("draft_id"))
    return result


@tool
def process_multimedia_with_gemini(
    file_path_or_url: str,
    file_type: str,
    prompt: str = "Analiza este archivo en el contexto de gestión de condominios",
) -> dict:
    """
    Procesar archivo multimedia con Gemini.

    Soporta: audio, imagen, video, PDF.
    """
    import requests
    import google.generativeai as genai

    logger.info("🎬 Procesando %s: %s", file_type, file_path_or_url)

    # Cargar archivo
    if file_path_or_url.startswith("http"):
        response = requests.get(file_path_or_url, timeout=60)
        response.raise_for_status()
        file_data = response.content
        mime_type = response.headers.get("Content-Type", "application/octet-stream")
    else:
        with open(file_path_or_url, "rb") as f:
            file_data = f.read()
        mime_map = {
            "audio": "audio/ogg",
            "image": "image/jpeg",
            "video": "video/mp4",
            "pdf": "application/pdf",
        }
        mime_type = mime_map.get(file_type, "application/octet-stream")

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if file_type == "audio":
        response = model.generate_content(
            [
                f"{prompt}\n\nTranscribe este audio a texto:",
                {"mime_type": mime_type, "data": file_data},
            ]
        )
        transcription = response.text
        logger.info("🎤 Audio transcrito: %s caracteres", len(transcription))
        return {
            "transcription": transcription,
            "analysis": f"Audio transcrito exitosamente ({len(transcription)} chars)",
        }

    if file_type == "image":
        response = model.generate_content(
            [
                f"{prompt}\n\n¿Qué contiene esta imagen? Si hay texto, transcríbelo.",
                {"mime_type": mime_type, "data": file_data},
            ]
        )
        analysis = response.text
        logger.info("🖼️ Imagen analizada: %s caracteres", len(analysis))
        return {"analysis": analysis, "detected_text": analysis}

    if file_type == "pdf":
        response = model.generate_content(
            [
                f"{prompt}\n\nExtrae y resume el contenido de este PDF:",
                {"mime_type": mime_type, "data": file_data},
            ]
        )
        extracted = response.text
        logger.info("📄 PDF procesado: %s caracteres", len(extracted))
        return {"analysis": extracted, "extracted_text": extracted}

    if file_type == "video":
        response = model.generate_content(
            [
                f"{prompt}\n\nAnaliza este video (contenido visual + audio):",
                {"mime_type": mime_type, "data": file_data},
            ]
        )
        analysis = response.text
        logger.info("🎥 Video analizado: %s caracteres", len(analysis))
        return {"transcription": analysis, "analysis": analysis}

    raise ValueError(f"Tipo de archivo no soportado: {file_type}")


def format_trello_ticket_complete(
    state: AgentState, category: str, priority: str
) -> tuple[str, str]:
    """
    Generar ticket Trello con formato empresarial completo.
    """
    from datetime import datetime

    client = state["client_data"]

    emoji_map = {
        "consulta_deuda": "💳",
        "solicitud_documento": "📄",
        "reporte_problema": "🔧",
        "intervencion_requerida": "🚨",
    }
    emoji = emoji_map.get(category, "📋")

    title = (
        f"{emoji} {client['name']} - Unidad {client['unit_number']} - "
        f"{category.replace('_', ' ').title()}"
    )

    description = f"""
╔══════════════════════════════════════════════════════════════╗
║              {emoji} TICKET AUTOMÁTICO - FRAN BOT                 ║
╚══════════════════════════════════════════════════════════════╝

📋 INFORMACIÓN DEL CLIENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Nombre Completo:     {client['name']}
🏢 Unidad:              {client['unit_number']}
🏗️ Edificio:            {client.get('building', 'N/A')}
🔢 Piso:                {client.get('floor', 'N/A')}
🆔 DNI/Pasaporte:       {client.get('dni', 'No registrado')}

📞 DATOS DE CONTACTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Teléfono:            {client['phone']}
📧 Email:               {client.get('email', 'No registrado')}
✅ Método Preferido:    {client.get('preferred_contact_method', 'WhatsApp').upper()}

💰 ESTADO FINANCIERO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deuda Pendiente:        {"SÍ - S/ " + str(client['debt_amount']) if client['has_debt'] else "NO - Al día"}
{("Último Pago:           " + str(client.get('last_payment_date'))) if client.get('last_payment_date') else ""}

📝 CONTEXTO DE LA CONVERSACIÓN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Canal Original:         {state['channel'].upper()}
Mensaje del Cliente:    "{state['user_message']}"
Intención Detectada:    {state['detected_intent'].replace('_', ' ').title()}
{f"Archivos Adjuntos:     {len(state['attachments'])} archivo(s)" if state.get('attachments') else "Sin archivos adjuntos"}
{f"Razón Fallback:       {state.get('fallback_reason')}" if state.get('used_fallback') else ""}
{f"Quality Score:        {state.get('quality_score', 0):.2f}/1.00" if state.get('quality_score') is not None else ""}

🔗 DATOS TÉCNICOS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conversación ID:        {state['conversation_id']}
Mensaje ID:             {state['message_id']}
Historial Previo:       {len(state.get('conversation_history', []))} mensajes
Timestamp:              {state.get('timestamp')}
Tiempo Procesamiento:   {state.get('execution_time_seconds', 0):.2f} segundos
Nodos Ejecutados:       {" → ".join(state.get('nodes_executed', []))}

⚡ ACCIÓN SUGERIDA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{get_suggested_action(category, state)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Ticket generado automáticamente por Fran Bot
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (America/Lima)
""".strip()

    return title, description


def get_suggested_action(category: str, state: AgentState) -> str:
    """Acción sugerida según categoría."""
    client = state["client_data"]
    channel_str = client.get("preferred_contact_method", "teléfono").upper()

    actions = {
        "consulta_deuda": f"""
1. ✅ Verificar saldo actual en sistema contable
2. 📧 Generar estado de cuenta actualizado
3. 📤 Enviar por {channel_str} a: {client.get('email', client['phone'])}
4. 📞 Llamar si deuda > S/ 1000
""",
        "solicitud_documento": f"""
1. 📄 Preparar documento solicitado (estado cuenta/reglamento/recibo)
2. ✅ Verificar que esté actualizado
3. 📤 Enviar por {channel_str} a: {client.get('email', client['phone'])}
4. ✔️ Confirmar recepción con el cliente
""",
        "reporte_problema": f"""
1. 🔍 Evaluar severidad del problema reportado
2. 📋 Asignar a equipo de mantenimiento correspondiente
3. ⏱️ Establecer tiempo estimado de solución
4. 📞 Notificar al cliente: {client['phone']}
5. ✅ Confirmar resolución una vez solucionado
""",
        "intervencion_requerida": f"""
⚠️ URGENTE - La IA no pudo resolver esta consulta

1. 🚨 CONTACTAR AL CLIENTE EN LAS PRÓXIMAS 24 HORAS
2. 📞 Método: {channel_str}
3. 📱 Contacto: {client['phone']} {"/ " + client['email'] if client.get('email') else ""}
4. 💬 Resolver consulta que IA no pudo manejar
5. 📝 Documentar la resolución para mejorar el bot
6. ✅ Cerrar ticket una vez resuelto

Razón del escalamiento: {state.get('fallback_reason', 'No especificada')}
""",
    }

    return actions.get(category, "Revisar y actuar según corresponda").strip()

