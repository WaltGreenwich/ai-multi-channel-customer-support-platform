from .base import get_base_system_prompt


def get_telegram_prompt() -> str:
    """
    Prompt específico para Telegram.

    Estilo un poco más cercano y con algunos emojis suaves.
    """

    base = get_base_system_prompt()
    return (
        base
        + "\nCanal: TELEGRAM.\n"
        "- Usa un tono conversacional, cercano y empático.\n"
        "- Puedes usar algunos emojis, pero no abuses (máximo 2–3 por mensaje).\n"
        "- Mantén las respuestas claras y relativamente cortas, "
        "divididas en párrafos y listas cuando ayude.\n"
    )
