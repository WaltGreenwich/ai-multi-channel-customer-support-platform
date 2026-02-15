from .base import get_base_system_prompt


def get_email_prompt() -> str:
    """
    Prompt específico para emails (borradores Gmail).

    Tono formal empresarial, con saludos y cierre adecuados.
    """

    base = get_base_system_prompt()
    return (
        base
        + "\nCanal: EMAIL.\n"
        "- Usa un tono formal y profesional.\n"
        "- Incluye un saludo inicial (por ejemplo: 'Estimado(a),').\n"
        "- Redacta en formato de carta breve con introducción, desarrollo y cierre.\n"
        "- No envíes firmas automáticas; solo un cierre simple como "
        "'Saludos cordiales, Administración del condominio'.\n"
    )

