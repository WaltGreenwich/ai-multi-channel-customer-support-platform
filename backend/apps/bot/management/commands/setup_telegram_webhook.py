from __future__ import annotations

"""
Comando para configurar el webhook de Telegram apuntando a Django.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests


class Command(BaseCommand):
    help = "Configura el webhook de Telegram para que apunte al endpoint de Django."

    def add_arguments(self, parser):
        parser.add_argument(
            "public_url",
            type=str,
            help="URL pública base (por ejemplo, https://xxxx.ngrok.io)",
        )

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            self.stderr.write(self.style.ERROR("TELEGRAM_BOT_TOKEN no está configurado"))
            return

        base_url: str = options["public_url"].rstrip("/")
        webhook_url = f"{base_url}/api/telegram/webhook/"

        api_url = (
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"
        )
        self.stdout.write(f"Configurando webhook: {webhook_url}")
        resp = requests.post(api_url, json={"url": webhook_url}, timeout=30)
        data = resp.json()

        if data.get("ok"):
            self.stdout.write(self.style.SUCCESS("Webhook configurado correctamente"))
        else:
            self.stderr.write(self.style.ERROR(f"Error al configurar webhook: {data}"))

