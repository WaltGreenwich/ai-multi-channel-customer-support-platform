#!/usr/bin/env python
"""
Punto de entrada principal de Django.

Se mantiene lo más estándar posible para no sorprender a otros
desarrolladores del equipo.
"""
import os
import sys


def main() -> None:
    """Ejecutar tareas administrativas de Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. Asegúrate de tener las "
            "dependencias instaladas dentro del contenedor."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
