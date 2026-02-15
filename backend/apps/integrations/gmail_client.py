from __future__ import annotations

"""
Cliente mínimo para Gmail API (solo creación de borradores).

En este proyecto NUNCA se envían correos automáticamente; solo se crean drafts.
"""

from dataclasses import dataclass
from typing import Any, Dict

from django.conf import settings


@dataclass
class GmailClient:
    client_id: str
    client_secret: str
    refresh_token: str
    enabled: bool

    def create_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Implementación placeholder / mock.

        La integración real con Gmail puede montarse encima sin cambiar
        la interfaz pública.
        """
        if not self.enabled:
            return {
                "draft_id": f"mock-draft-{to}",
                "url": "https://mail.google.com/mail/u/0/#drafts/mock",
                "is_draft": True,
                "sent": False,
                "status": "mock_draft_created",
            }

        # Aquí se podría usar google-api-python-client para crear el draft real.
        # Por ahora mantenemos la misma estructura que el mock.
        return {
            "draft_id": f"draft-{to}",
            "url": "https://mail.google.com/mail/u/0/#drafts",
            "is_draft": True,
            "sent": False,
        }


gmail_client = GmailClient(
    client_id=settings.GMAIL_CLIENT_ID,
    client_secret=settings.GMAIL_CLIENT_SECRET,
    refresh_token=settings.GMAIL_REFRESH_TOKEN,
    enabled=settings.USE_GMAIL,
)

