from __future__ import annotations

"""
Cliente sencillo para Supabase.

En desarrollo normalmente estará deshabilitado y se usará Django ORM.
"""

from dataclasses import dataclass
from typing import Optional

from django.conf import settings


@dataclass
class SupabaseClient:
    url: str
    key: str
    bucket: str
    use_supabase: bool

    def get_client_by_phone(self, phone: str) -> Optional[dict]:
        """
        Buscar cliente por teléfono en Supabase.

        En esta versión de referencia solo retorna None; la integración real
        se puede implementar más adelante sin cambiar la interfaz.
        """
        if not self.use_supabase:
            return None

        # Aquí iría la llamada real a Supabase (REST o Python client).
        # Devolvemos None para no romper el flujo en desarrollo.
        return None


supabase_client = SupabaseClient(
    url=settings.SUPABASE_URL,
    key=settings.SUPABASE_KEY,
    bucket=settings.SUPABASE_BUCKET,
    use_supabase=settings.USE_SUPABASE,
)

