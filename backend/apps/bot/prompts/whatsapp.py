from .base import get_base_system_prompt


def get_whatsapp_prompt() -> str:
    """
    Prompt específico para WhatsApp.

    Conversacional, directo y fácil de leer en móvil.
    """

    base = get_base_system_prompt()
    return (
        base
        + "\nCanal: WHATSAPP.\n"
        "- Escribe mensajes breves y directos.\n"
        "- Usa listas numeradas y viñetas para explicar pasos.\n"
        "- Evita párrafos muy largos; separa ideas clave en líneas distintas.\n"
    )

