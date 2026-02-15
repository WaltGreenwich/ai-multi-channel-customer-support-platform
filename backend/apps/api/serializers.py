from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedAttachment:
    type: str  # audio | image | video | pdf
    url: str
    filename: str
    size_bytes: int
    mime_type: str
    duration_seconds: Optional[float] = None


@dataclass
class NormalizedIncomingMessage:
    """
    Estructura JSON normalizada que será enviada al agente.
    """

    conversation_id: str
    message_id: str
    channel: str  # telegram | whatsapp | email
    user_message: str
    client_phone: str
    client_name: Optional[str]
    client_unit: Optional[str]
    attachments: List[Dict[str, Any]]
    raw_payload: Dict[str, Any]

