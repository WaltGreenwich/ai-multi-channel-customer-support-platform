from __future__ import annotations

import logging
import os
from typing import Optional
from datetime import datetime

from django.conf import settings
from langchain_core.tools import tool

from apps.bot.state import AgentState

logger = logging.getLogger(__name__)


@tool
def query_client_data(phone: str) -> Optional[dict]:
    """
    Consulta los datos del cliente en la base de datos local o Supabase usando su numero de telefono.
    """
    from apps.bot.models import Client
    from apps.integrations.supabase_client import supabase_client

    if supabase_client.use_supabase:
        result = supabase_client.get_client_by_phone(phone)
        if result:
            return result

    try:
        client = Client.objects.get(phone=phone)
        return client.get_contact_info()
    except Client.DoesNotExist:
        logger.warning("Cliente no encontrado: %s", phone)
        return None


@tool
def search_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
    """
    Busca informacion en el reglamento y politicas del condominio (RAG) para responder dudas.
    """
    from apps.integrations.supabase_client import supabase_client
    _ = supabase_client  

    mock_knowledge = {
        "reglamento": {
            "title": "Reglamento Interno del Condominio",
            "content": """
El horario de uso de áreas comunes es:
- Pileta: 9:00 AM - 9:00 PM
- Gimnasio: 6:00 AM - 11:00 PM
- SUM / Salón de eventos: Reserva previa vía App.

Expensas:
- Vencimiento: Día 10 de cada mes.
- Métodos: Transferencia bancaria, Pago Mis Cuentas, Rapipago.
- Mora: Tasa activa Banco Nación después del segundo vencimiento.
""",
            "category": "reglamento",
        },
        "pagos": {
            "title": "Política de Pagos y Cobranzas",
            "content": """
Formas de pago aceptadas:
1. Transferencia: CBU 0070123456789012345678 (Banco Galicia)
2. Alias: CONDOMINIO.FRAN.BOT
3. Tarjeta de crédito/débito en oficina de administración.

Para consultar libre deuda: administracion@condominio.com.ar
""",
            "category": "pagos",
        },
        "mantenimiento": {
            "title": "Atención de Siniestros y Fallas",
            "content": """
Para reportar fallas:
1. Emergencias (Gas, Agua, Ascensores): (011) 4321-8888 (Guardia 24hs)
2. Mantenimiento general: WhatsApp +54 9 11 9876-5432
3. Administración: lunes a viernes de 10 a 17hs.

Tiempo estimado de visita técnica: 24 hs hábiles.
""",
            "category": "mantenimiento",
        },
    }

    query_lower = query.lower()
    results: list[dict] = []

    for doc_id, doc in mock_knowledge.items():
        score = 0.0
        if any(k in query_lower for k in ["horario", "pileta", "gym", "sum"]):
            if doc_id == "reglamento": score = 0.9
        if any(k in query_lower for k in ["pago", "deuda", "expensa", "cbu", "alias"]):
            if doc_id == "pagos": score = 0.95
        if any(k in query_lower for k in ["problema", "falla", "ascensor", "luz", "caño"]):
            if doc_id == "mantenimiento": score = 0.92

        if score > 0:
            results.append({
                "title": doc["title"],
                "content": doc["content"],
                "category": doc["category"],
                "relevance_score": score,
            })

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
    Crea una tarjeta en Trello para dar seguimiento a una solicitud o problema reportado.
    """
    from apps.integrations.trello_client import trello_client

    use_trello = os.getenv("USE_TRELLO", "false").lower() == "true"
    if not use_trello:
        logger.info("🚫 Trello deshabilitado. Omitiendo creación de: %s", title)
        return {"id": "mock-disabled", "url": "#", "status": "skipped"}

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
    return result


@tool
def send_telegram_message(chat_id: str, text: str, parse_mode: str = "Markdown") -> dict:
    """
    Envia un mensaje de texto al usuario a traves de Telegram.
    """
    from apps.integrations.telegram_client import telegram_client
    logger.info("📱 Enviando Telegram a %s", chat_id)
    return telegram_client.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


@tool
def send_whatsapp_message(phone: str, text: str) -> dict:
    """
    Envia un mensaje de texto al usuario a traves de WhatsApp.
    """
    from apps.integrations.whatsapp_client import whatsapp_client
    logger.info("💬 Enviando WhatsApp a %s", phone)

    if not whatsapp_client.enabled:
        return {"success": True, "message_id": f"mock-wa-{phone}", "status": "mock_sent"}

    return whatsapp_client.send_message(phone=phone, text=text)


@tool
def create_gmail_draft(to: str, subject: str, body: str) -> dict:
    """
    Crea un borrador de correo electronico en Gmail para ser revisado por administracion.
    """
    from apps.integrations.gmail_client import gmail_client
    if not gmail_client.enabled:
        return {"draft_id": f"mock-draft-{to}", "is_draft": True}
    return gmail_client.create_draft(to=to, subject=subject, body=body)


@tool
def process_multimedia_with_gemini(
    file_path_or_url: str,
    file_type: str,
    prompt: str = "Analiza este archivo en el contexto de gestión de condominios",
) -> dict:
    """
    Analiza archivos multimedia (imagenes, audio, PDF) usando el modelo Gemini para extraer informacion.
    """
    import requests
    import google.generativeai as genai

    logger.info("🎬 Procesando %s con Gemini Flash", file_type)

    if file_path_or_url.startswith("http"):
        response = requests.get(file_path_or_url, timeout=60)
        file_data = response.content
        mime_type = response.headers.get("Content-Type", "application/octet-stream")
    else:
        with open(file_path_or_url, "rb") as f:
            file_data = f.read()
        mime_map = {"audio": "audio/ogg", "image": "image/jpeg", "video": "video/mp4", "pdf": "application/pdf"}
        mime_type = mime_map.get(file_type, "application/octet-stream")

    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-flash-latest")

    response = model.generate_content([
        f"{prompt}",
        {"mime_type": mime_type, "data": file_data},
    ])
    
    return {"analysis": response.text, "transcription": response.text}

# --- Las funciones de abajo no llevan @tool, asi que no necesitan docstring obligatorio ---

def format_trello_ticket_complete(
    state: AgentState, category: str, priority: str
) -> tuple[str, str]:
    """Generar ticket Trello con formato para Argentina."""
    client = state["client_data"]
    emoji_map = {"consulta_deuda": "💳", "solicitud_documento": "📄", "reporte_problema": "🔧", "intervencion_requerida": "🚨"}
    emoji = emoji_map.get(category, "📋")

    title = f"{emoji} {client['name']} - UF {client['unit_number']} - {category.replace('_', ' ').title()}"

    description = f"""
╔══════════════════════════════════════════════════════════════╗
║              {emoji} TICKET AUTOMÁTICO - FRAN BOT              ║
╚══════════════════════════════════════════════════════════════╝

📋 INFORMACIÓN DEL PROPIETARIO/INQUILINO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Nombre: {client['name']}
🏢 Unidad Funcional: {client['unit_number']}
🆔 CUIL/DNI: {client.get('dni', 'No registrado')}

📞 CONTACTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Teléfono: {client['phone']}
📧 Email: {client.get('email', 'No registrado')}

🤖 Ticket generado automáticamente por Fran Bot
📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} (America/Argentina/Buenos_Aires)
""".strip()

    return title, description