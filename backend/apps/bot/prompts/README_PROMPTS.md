# Prompts de Fran Bot

Este directorio contiene los **prompts del sistema** que controlan el estilo
y comportamiento de Fran Bot en cada canal.

## Archivos principales

- `base.py`: Prompt común para todos los canales.
- `telegram.py`: Estilo más conversacional y cercano.
- `whatsapp.py`: Mensajes breves y fáciles de leer en móvil.
- `email.py`: Redacción formal para correos electrónicos.

## ¿Cómo editar los prompts?

1. Abre el archivo del canal que quieras ajustar. Ejemplos:
   - `telegram.py`
   - `whatsapp.py`
   - `email.py`

2. Dentro de cada archivo encontrarás una función:

   - `get_telegram_prompt()`
   - `get_whatsapp_prompt()`
   - `get_email_prompt()`

   Edita **solo el texto del `return`** (las comillas) respetando que el
   contenido esté en español.

3. Guarda el archivo.

4. Reinicia el backend (si estás usando Docker):

   ```bash
   make restart
   ```

5. Envía mensajes de prueba por el canal correspondiente para validar el tono.

## Buenas prácticas

- Mantén el idioma siempre en **español**.
- Explica al modelo:
  - Tono deseado (formal, casual, etc.).
  - Uso de emojis (permitidos o no, pocos o muchos).
  - Longitud aproximada de las respuestas.
  - Formato preferido (listas, párrafos cortos, etc.).
- No incluyas datos sensibles (tokens, claves, etc.) dentro de los prompts.

## Ejemplo sencillo (Telegram)

```python
def get_telegram_prompt() -> str:
    base = get_base_system_prompt()
    return (
        base
        + "\\nCanal: TELEGRAM.\\n"
        + "- Usa un tono muy amigable y cercano.\\n"
        + "- Puedes agregar 1 o 2 emojis en cada respuesta.\\n"
    )
```

Con esto, cualquier persona del equipo (aunque no programe) puede ajustar la
voz de Fran Bot sin tocar la lógica del agente.

