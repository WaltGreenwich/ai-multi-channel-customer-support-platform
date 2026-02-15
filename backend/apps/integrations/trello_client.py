from __future__ import annotations

"""
Cliente sencillo para la API de Trello.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

import requests
from django.conf import settings


@dataclass
class TrelloClient:
    api_key: str
    token: str
    board_id: str
    list_id: str

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.token and self.list_id)

    def create_card(
        self,
        title: str,
        description: str,
        priority: str = "MEDIUM",
        labels: List[str] | None = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "id": "mock-card-id",
                "url": "https://trello.com/c/mock",
                "status": "mock_created",
            }

        url = "https://api.trello.com/1/cards"
        params = {
            "key": self.api_key,
            "token": self.token,
            "idList": self.list_id,
            "name": title,
            "desc": description,
        }
        resp = requests.post(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Etiquetas como parte de la descripción (simple).
        if labels:
            data["labels_used"] = labels
        data["priority"] = priority
        return data


trello_client = TrelloClient(
    api_key=settings.TRELLO_API_KEY,
    token=settings.TRELLO_TOKEN,
    board_id=settings.TRELLO_BOARD_ID,
    list_id=settings.TRELLO_LIST_ID,
)

