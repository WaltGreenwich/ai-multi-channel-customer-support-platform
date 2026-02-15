from __future__ import annotations

"""
Definición del grafo de estados de LangGraph para Fran Bot.
"""

from typing import Callable

from langgraph.graph import StateGraph, END

from apps.bot.state import AgentState
from apps.bot import nodes


def _route_from_router(state: AgentState) -> str:
    intent = state.get("detected_intent", "desconocido")
    if intent == "faq_simple":
        return "direct_response"
    # todo lo demás va por RAG + Gemini
    return "rag"


def _route_after_quality(state: AgentState) -> str:
    return "action_planner" if state.get("quality_passed", False) else "fallback"


def build_agent_graph() -> Callable[[AgentState], AgentState]:
    """
    Construir el grafo de 8 nodos y devolver un runner síncrono.
    """
    workflow: StateGraph[AgentState] = StateGraph(AgentState)  # type: ignore[arg-type]

    # Nodos
    workflow.add_node("entry", nodes.entry_node)
    workflow.add_node("router", nodes.router_node)
    workflow.add_node("direct_response", nodes.direct_response_node)
    workflow.add_node("rag", nodes.rag_node)
    workflow.add_node("gemini", nodes.gemini_processor_node)
    workflow.add_node("quality_check", nodes.quality_check_node)
    workflow.add_node("fallback", nodes.fallback_node)
    workflow.add_node("action_planner", nodes.action_planner_node)

    # Flujo principal
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "router")

    # Router → direct / rag
    workflow.add_conditional_edges(
        "router",
        _route_from_router,
        {
            "direct_response": "direct_response",
            "rag": "rag",
        },
    )

    # Direct response salta a quality_check (sin RAG/Gemini)
    workflow.add_edge("direct_response", "quality_check")

    # RAG → Gemini → Quality
    workflow.add_edge("rag", "gemini")
    workflow.add_edge("gemini", "quality_check")

    # Quality → fallback / action_planner → END
    workflow.add_conditional_edges(
        "quality_check",
        _route_after_quality,
        {"fallback": "fallback", "action_planner": "action_planner"},
    )
    workflow.add_edge("fallback", "action_planner")
    workflow.add_edge("action_planner", END)

    app = workflow.compile()

    def runner(initial_state: AgentState) -> AgentState:
        """Ejecutar el grafo de forma síncrona."""
        result = app.invoke(initial_state)
        return result

    return runner

