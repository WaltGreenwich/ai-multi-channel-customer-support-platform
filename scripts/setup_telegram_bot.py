"""
Script interactivo para configurar Telegram Bot con BotFather.

Uso:
    python scripts/setup_telegram_bot.py
"""

import os
import sys


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

# Asegurar que Django esté en el path por si queremos usarlo después
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def print_header(text: str) -> None:
    print(f"\n{'═' * 70}")
    print(f"  {text}")
    print(f"{'═' * 70}\n")


def print_step(number: int, title: str) -> None:
    print(f"\n{'─' * 70}")
    print(f"  PASO {number}: {title}")
    print(f"{'─' * 70}\n")


def wait_for_enter(message: str = "Presiona ENTER cuando estés listo...") -> None:
    input(f"\n💡 {message}\n")


def main() -> None:
    print_header("🤖 CONFIGURACIÓN DE TELEGRAM BOT - FRAN BOT")

    print(
        """
Este asistente te guiará para crear y configurar un bot de Telegram
usando BotFather. El proceso toma aproximadamente 5 minutos.

Requisitos:
✅ Tener Telegram instalado (móvil o escritorio)
✅ Tener una cuenta de Telegram activa
✅ Conexión a internet

Comencemos...
"""
    )

    wait_for_enter("Presiona ENTER para comenzar")

    # PASO 1
    print_step(1, "Abrir Telegram")
    print(
        """
1. Abre la aplicación de Telegram en tu dispositivo.
2. Puedes usar:
   • Telegram móvil (iOS/Android)
   • Telegram Desktop (Windows/Mac/Linux)
   • Telegram Web (web.telegram.org)
"""
    )
    wait_for_enter()

    # PASO 2
    print_step(2, "Buscar y contactar a BotFather")
    print(
        """
1. En la barra de búsqueda de Telegram, escribe: @BotFather
2. Selecciona el bot oficial "BotFather" (tiene verificación azul ✅)
3. Presiona "START" o envía el comando: /start
4. BotFather te mostrará una lista de comandos disponibles
"""
    )
    wait_for_enter()

    # PASO 3
    print_step(3, "Crear nuevo bot")
    print(
        """
1. Envía el comando: /newbot
2. BotFather te preguntará: "Alright, a new bot. How are we going to call it?"
3. Envía el nombre de tu bot, por ejemplo: Fran Bot Desarrollo
   (Este es el nombre que verán los usuarios)
4. BotFather te pedirá un username para el bot
5. Envía, por ejemplo: fran_condominio_dev_bot
   (Debe terminar en 'bot' y ser único)

Si el username ya está tomado, prueba variaciones hasta que BotFather lo acepte.
"""
    )
    wait_for_enter()

    # PASO 4
    print_step(4, "Obtener el token de acceso")
    print(
        """
BotFather te enviará un mensaje como este:

    Done! Congratulations on your new bot. You will find it at
    t.me/tu_bot. You can now add a description...

    Use this token to access the HTTP API:
    1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-1234567890

El token es la línea que empieza con números y contiene dos puntos (:)
Ejemplo: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
"""
    )

    print("\n" + "─" * 70)
    print("  Por favor, COPIA el token que BotFather te envió")
    print("─" * 70 + "\n")

    token = input("📝 Pega aquí el token: ").strip()

    # Validar formato
    if not token or ":" not in token:
        print("\n❌ ERROR: El token no parece válido.")
        print("   Debe tener este formato: 1234567890:ABCdefGHIjklMNOpqrs...")
        sys.exit(1)

    parts = token.split(":")
    if len(parts) != 2 or not parts[0].isdigit():
        print("\n❌ ERROR: El formato del token es incorrecto.")
        print(f"   Recibido: {token[:20]}...")
        print("\n🔄 Verifica que hayas copiado el token completo.")
        sys.exit(1)

    print("\n✅ Token validado correctamente!")

    # PASO 5: Guardar en backend/.env
    print_step(5, "Guardar configuración en backend/.env")

    env_path = os.path.join(BACKEND_DIR, ".env")
    print(f"Guardando token en: {env_path}")

    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            env_content = f.read()

    # Limpiar config previa de Telegram si existiera
    lines = env_content.splitlines()
    filtered = [
        line
        for line in lines
        if not line.startswith("USE_TELEGRAM")
        and not line.startswith("TELEGRAM_BOT_TOKEN")
    ]
    env_content = "\n".join(filtered)

    if not env_content.endswith("\n"):
        env_content += "\n"

    env_content += "# Telegram Bot (Desarrollo)\n"
    env_content += "USE_TELEGRAM=true\n"
    env_content += f"TELEGRAM_BOT_TOKEN={token}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n✅ Token guardado exitosamente en backend/.env")

    # PASO 6: Sugerir configuración de webhook
    print_step(6, "Configurar webhook (opcional)")
    print(
        """
Para que el bot reciba mensajes automáticamente, necesitas un webhook.

Opción recomendada en desarrollo:
1. Instalar ngrok: https://ngrok.com/download
2. Ejecutar en otra terminal:

   ngrok http 8000

3. Copiar la URL pública que muestra ngrok (https://xxxx.ngrok.io)
4. Con los contenedores levantados (`make up`), ejecuta:

   docker-compose exec web python manage.py setup_telegram_webhook https://xxxx.ngrok.io
"""
    )

    # Resumen final
    print_header("✅ CONFIGURACIÓN COMPLETADA")
    print(
        f"""
Tu bot de Telegram está configurado.

Próximos pasos:

1. Levantar servicios:
   make up

2. Configurar webhook (opcional, recomendado):
   ngrok http 8000
   docker-compose exec web python manage.py setup_telegram_webhook https://xxxx.ngrok.io

3. Probar el bot en Telegram:
   • Busca tu username configurado en BotFather
   • Envía: /start
   • Envía: Hola

Usuario admin por defecto:
  - Usuario: admin
  - Contraseña: admin123
"""
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Configuración cancelada por el usuario.")
        sys.exit(0)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"\n\n❌ ERROR: {exc}")
        sys.exit(1)

