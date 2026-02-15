import json
from unittest.mock import MagicMock, patch

from django.urls import reverse


@patch("apps.api.views.process_message_task")
def test_telegram_webhook_queues_task(mock_task, client):
    mock_task.delay = MagicMock()

    payload = {
        "message": {
            "message_id": 1,
            "chat": {"id": 12345, "first_name": "Juan"},
            "text": "Hola",
        }
    }

    url = reverse("telegram-webhook")
    resp = client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert resp.status_code == 202
    assert mock_task.delay.called
    args, _ = mock_task.delay.call_args
    queued_payload = args[0]
    assert queued_payload["channel"] == "telegram"
    assert queued_payload["user_message"] == "Hola"

