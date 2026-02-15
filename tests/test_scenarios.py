import uuid
from unittest.mock import MagicMock, patch

from apps.bot.langgraph_agent import build_agent_graph
from apps.bot.state import AgentState


def _base_state() -> AgentState:
    return AgentState(
        conversation_id=str(uuid.uuid4()),
        message_id=str(uuid.uuid4()),
        channel="telegram",
        user_message="",
        attachments=[],
        client_data={
            "id": 0,
            "name": "Juan Pérez",
            "phone": "+51987654321",
            "email": "juan@example.com",
            "dni": "12345678",
            "unit_number": "101",
            "building": "Torre A",
            "floor": 5,
            "has_debt": True,
            "debt_amount": 500.0,
            "last_payment_date": "2024-01-15",
            "preferred_contact_method": "whatsapp",
        },
        telegram_chat_id="123",
        telegram_message_id=1,
        whatsapp_message_id=None,
        gmail_message_id=None,
        conversation_history=[],
        detected_intent="desconocido",
        needs_rag=False,
        rag_results=[],
        ai_response="",
        quality_passed=False,
        quality_score=0.0,
        quality_fail_reason="",
        used_fallback=False,
        fallback_reason="",
        final_response="",
        actions_taken=[],
        trello_ticket_created=False,
        trello_ticket_data=None,
        metadata={},
        timestamp="",
        execution_time_seconds=0.0,
        nodes_executed=[],
    )


def test_faq_simple_goes_through_direct_response(db):  # noqa: PT004
    state = _base_state()
    state["user_message"] = "¿Cuál es el horario de la piscina?"

    with patch("apps.bot.nodes.send_telegram_message") as mock_send:
        mock_send.invoke = MagicMock(return_value={"message_id": 123, "success": True})
        agent = build_agent_graph()
        final_state = agent(state)

    assert "direct_response" in final_state["nodes_executed"]
    assert "Piscina" in final_state["ai_response"] or "piscina" in final_state["ai_response"].lower()


def test_unknown_question_triggers_fallback(db):  # noqa: PT004
    state = _base_state()
    state["user_message"] = "asdasdasd 123123"

    mock_response = MagicMock()
    mock_response.text = "Respuesta de prueba para consulta compleja."
    with patch("apps.bot.nodes.send_telegram_message") as mock_send:
        mock_send.invoke = MagicMock(return_value={"message_id": 456, "success": True})
        with patch(
            "google.generativeai.GenerativeModel",
            return_value=MagicMock(generate_content=MagicMock(return_value=mock_response)),
        ):
            agent = build_agent_graph()
            final_state = agent(state)

    assert "quality_check" in final_state["nodes_executed"]
    assert "gemini" in final_state["nodes_executed"]

