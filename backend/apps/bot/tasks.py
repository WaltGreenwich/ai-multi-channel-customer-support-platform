from __future__ import annotations

import logging
from datetime import datetime, timezone as dt_timezone
from typing import Any

from celery import shared_task

from apps.bot.langgraph_agent import build_agent_graph
from apps.bot.state import AgentState

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="process_message")
def process_message_task(self, state_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Tarea Celery principal que ejecuta el agente LangGraph.

    `state_payload` debe seguir la estructura de `AgentState`.
    """
    logger.info("🚀 Iniciando tarea process_message (%s)", self.request.id)
    started = datetime.now(tz=dt_timezone.utc)

    state: AgentState = AgentState(**state_payload)  # type: ignore[call-arg]
    state["timestamp"] = started.isoformat()
    state.setdefault("execution_time_seconds", 0.0)
    state.setdefault("nodes_executed", [])
    state["metadata"] = state.get("metadata", {})
    state["metadata"]["celery_task_id"] = self.request.id

    runner = build_agent_graph()
    final_state = runner(state)

    finished = datetime.now(tz=dt_timezone.utc)
    final_state["execution_time_seconds"] = (
        finished - started
    ).total_seconds()

    logger.info("✅ Tarea process_message completada (%s)", self.request.id)
    return dict(final_state)

