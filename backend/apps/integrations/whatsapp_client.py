from __future__ import annotations

"""
Cliente para WhatsApp Business Cloud API.

En desarrollo normalmente estará deshabilitado y operará en modo mock.
"""

from dataclasses import dataclass
from typing import Any, Dict

import requests
from django.conf import settings


@dataclass
class WhatsAppClient:
    phone_id: str
    token: str
    enabled: bool

    @property
    def api_url(self) -> str:
        return f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"

    def send_message(self, phone: str, text: str) -> Dict[str, Any]:
        if not self.enabled or not self.phone_id or not self.token:
            # Modo mock
            return {
                "success": True,
                "message_id": f"mock-wa-{phone}",
                "status": "mock_sent",
            }

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone.replace("+", ""),
            "type": "text",
            "text": {"body": text},
        }
        resp = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "message_id": data.get("messages", [{}])[0].get("id"),
            "raw": data,
        }


whatsapp_client = WhatsAppClient(
    phone_id=settings.WHATSAPP_PHONE_ID,
    token=settings.WHATSAPP_TOKEN,
    enabled=settings.USE_WHATSAPP,
)

