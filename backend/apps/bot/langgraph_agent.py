from __future__ import annotations

"""
Definición del grafo de estados de LangGraph para Fran Bot.
Optimizado para ahorro de tokens (greetings bypass) y manejo de estados.
"""

from typing import Callable
from langgraph.graph import StateGraph, END
from apps.bot.state import AgentState
from apps.bot import nodes

def _route_from_router(state: AgentState) -> str:
    """
    Decide si el flujo debe ir a RAG o saltar directo al Action Planner.
    Si es un saludo, no necesitamos procesar RAG ni Gemini.
    """
    if state.get("is_greeting", False):
        return "action_planner"
    return "rag"

def _route_after_quality(state: AgentState) -> str:
    """
    Si la calidad es insuficiente, redirige al nodo de fallback.
    """
    return "action_planner" if state.get("quality_passed", False) else "fallback"

def build_agent_graph() -> Callable[[AgentState], AgentState]:
    workflow: StateGraph[AgentState] = StateGraph(AgentState)

    # 1. Registro de Nodos
    workflow.add_node("entry", nodes.entry_node)
    workflow.add_node("router", nodes.router_node)
    workflow.add_node("rag", nodes.rag_node)
    workflow.add_node("gemini", nodes.gemini_processor_node)
    workflow.add_node("quality_check", nodes.quality_check_node)
    workflow.add_node("fallback", nodes.fallback_node)
    workflow.add_node("action_planner", nodes.action_planner_node)

    # 2. Definición del Flujo
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "router")

    # ATAJO DE SALUDOS: Condicional para ahorrar API
    workflow.add_conditional_edges(
        "router",
        _route_from_router,
        {
            "action_planner": "action_planner", # Bypass total si es saludo
            "rag": "rag"                        # Flujo normal si requiere análisis
        }
    )

    # Flujo Estándar de Procesamiento
    workflow.add_edge("rag", "gemini")
    workflow.add_edge("gemini", "quality_check")

    # CONTROL DE CALIDAD: Decide si la respuesta de la IA es válida
    workflow.add_conditional_edges(
        "quality_check",
        _route_after_quality,
        {
            "fallback": "fallback",
            "action_planner": "action_planner"
        }
    )

    # Cierre de hilos
    workflow.add_edge("fallback", "action_planner")
    workflow.add_edge("action_planner", END)

    app = workflow.compile()
    
    def runner(initial_state: AgentState) -> AgentState:
        # El runner invoca el grafo compilado
        return app.invoke(initial_state)

    return runner