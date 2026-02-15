"""
Prompts del sistema separados por canal.

Cada archivo expone una función `get_system_prompt(channel: str) -> str`
para que el nodo de Gemini arme el contexto correcto sin que los
no-programadores tengan que tocar Python en otros módulos.
"""

from .base import get_base_system_prompt
from .telegram import get_telegram_prompt
from .whatsapp import get_whatsapp_prompt
from .email import get_email_prompt

__all__ = [
    "get_base_system_prompt",
    "get_telegram_prompt",
    "get_whatsapp_prompt",
    "get_email_prompt",
]
