"""
Paquete raíz para las apps de Django.

La estructura queda:
- apps.bot          → Núcleo del agente (modelos, LangGraph, tasks)
- apps.integrations → Clientes de terceros (Telegram, Trello, etc.)
- apps.api          → Webhooks de entrada (Telegram, WhatsApp, Gmail)
"""
