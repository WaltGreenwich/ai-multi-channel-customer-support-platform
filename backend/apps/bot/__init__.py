"""
App principal del bot conversacional.

Contiene:
- Modelos de dominio (Client, Conversation, Message)
- Estado compartido del agente (AgentState)
- Nodos de LangGraph y herramientas (tools)
- Tarea Celery que ejecuta el grafo
"""

default_app_config = "apps.bot.apps.BotConfig"
