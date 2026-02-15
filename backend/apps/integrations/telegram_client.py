from __future__ import annotations

"""
Cliente para Telegram Bot API.

En desarrollo se usa el token configurado en `.env`.
"""

from dataclasses import dataclass
from typing import Any, Dict

import requests
from django.conf import settings


@dataclass
class TelegramClient:
    token: str

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    @property
    def base_url(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    def send_message(
        self, chat_id: str, text: str, parse_mode: str = "Markdown"
    ) -> Dict[str, Any]:
        if not self.enabled:
            # Modo mock
            return {
                "success": True,
                "message_id": f"mock-tg-{chat_id}",
                "status": "mock_sent",
            }

        url = f"{self.base_url}/sendMessage"
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "success": True,
            "message_id": data.get("result", {}).get("message_id"),
            "raw": data,
        }


telegram_client = TelegramClient(token=settings.TELEGRAM_BOT_TOKEN)

