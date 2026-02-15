from __future__ import annotations

"""
Wrapper opcional para configurar Gemini a un solo lugar.

La mayoría de nodos ya usan `google.generativeai` directamente, pero este
cliente permite centralizar configuración si se desea.
"""

from dataclasses import dataclass

import google.generativeai as genai
from django.conf import settings


@dataclass
class GeminiClient:
    model_name: str = "gemini-1.5-flash"

    def get_model(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        return genai.GenerativeModel(self.model_name)


gemini_client = GeminiClient()

