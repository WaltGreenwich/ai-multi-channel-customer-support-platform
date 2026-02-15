from __future__ import annotations

from typing import TypedDict, Literal, Optional


class AgentState(TypedDict, total=False):
    """Estado global del agente que fluye por los 8 nodos."""

    # Identificación
    conversation_id: str
    message_id: str

    # Datos del cliente
    client_data: dict

    # Canal y mensaje
    channel: Literal["telegram", "whatsapp", "email"]
    user_message: str
    attachments: list[dict]

    # IDs específicos del canal
    telegram_chat_id: Optional[str]
    telegram_message_id: Optional[int]
    whatsapp_message_id: Optional[str]
    gmail_message_id: Optional[str]

    # Contexto conversacional
    conversation_history: list[dict]

    # Flujo de decisión
    detected_intent: str
    needs_rag: bool
    rag_results: list[dict]

    # Respuesta IA
    ai_response: str
    quality_passed: bool
    quality_score: float
    quality_fail_reason: str

    # Fallback
    used_fallback: bool
    fallback_reason: str

    # Salida final
    final_response: str
    actions_taken: list[dict]

    # Trello
    trello_ticket_created: bool
    trello_ticket_data: Optional[dict]

    # Metadata y timing
    metadata: dict
    timestamp: str
    execution_time_seconds: float
    nodes_executed: list[str]
