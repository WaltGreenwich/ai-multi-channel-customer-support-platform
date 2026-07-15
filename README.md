# AI Multi-Channel Customer Support Platform

AI Multi-Channel Customer Support Platform is an AI-powered backend platform designed to automate customer support across multiple communication channels. It orchestrates LLM workflows using LangGraph, processes multimedia inputs, integrates with external business systems, and delivers context-aware responses through a modular and scalable architecture

## 🎯 Business Problem

- Organizations receive customer requests from multiple communication channels including messaging platforms, email, and web forms.

Traditional support teams spend considerable time answering repetitive questions, classifying requests, creating tickets, and managing context across disconnected systems.

As customer volume grows, operational costs increase while response consistency decreases.

An AI-driven orchestration platform can automate a significant portion of these interactions while maintaining business rules, integrating with existing operational systems, and escalating only when necessary.

## 🚀 Solution Overview

- receives customer messages
- normalizes incoming requests
- processes multimedia content
- retrieves contextual information
- executes AI workflows
- interacts with external services
- stores conversation history
- returns structured responses

## Public Target

- ✅ SaaS companies
- ✅ Customer Support teams
- ✅ Property Management
- ✅ Healthcare
- ✅ Logistics
- ✅ Insurance
- ✅ Education

### Paso 1: Configurar WSL2 (Si no lo tienes)
```powershell
# En PowerShell como Administrador:
wsl --install -d Ubuntu-22.04

# Reiniciar PC si es necesario

# Configurar como default:
wsl --set-default Ubuntu-22.04

# Entrar a Ubuntu:
wsl

# Instalar make:
sudo apt update
sudo apt install make -y
```

### Paso 2: Clonar y Abrir Proyecto en WSL
```bash
# En Ubuntu (WSL):
cd /mnt/c/Users/TU_USUARIO/Documents  # O donde esté tu proyecto

# Si ya clonaste en Windows, accede desde WSL:
cd /mnt/c/ruta/a/fran-bot-langgraph

# Abrir en VS Code (modo WSL):
code .
```

### Paso 3: Configurar Credenciales
```bash
# 1. Crear cuenta en ngrok: https://ngrok.com
# 2. Copiar tu authtoken de: https://dashboard.ngrok.com/get-started/your-authtoken

# 3. Copiar .env.example
cp backend/.env.example backend/.env

# 4. Editar backend/.env con tus credenciales:
nano backend/.env  # O usa VS Code

# Completar OBLIGATORIAMENTE:
# - NGROK_AUTHTOKEN=tu_token_de_ngrok
# - GOOGLE_API_KEY=tu_api_key_de_gemini
# - TELEGRAM_BOT_TOKEN=tu_token_de_telegram

# IMPORTANTE: ALLOWED_HOSTS debe incluir dominios ngrok para que el webhook funcione.
# Si no está, agrega: .ngrok-free.dev,.ngrok.io
# Ejemplo: ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,.ngrok-free.dev,.ngrok.io

# Guardar (Ctrl+X, Y, Enter en nano)
```

### Paso 4: Configurar Telegram Bot
```bash
# Ejecutar script interactivo:
python scripts/setup_telegram_bot.py

# El script te guiará para:
# 1. Crear bot con @BotFather
# 2. Obtener token
# 3. Guardar automáticamente en .env
```

### Paso 5: Levantar Servicios
```bash
# Instalar (build + DB + migraciones):
make setup

# Levantar todos los servicios (incluyendo ngrok):
make up

# ✅ Servicios activos:
# - Django: http://localhost:8000
# - Celery Flower: http://localhost:5555
# - Ngrok Dashboard: http://localhost:4040
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### Paso 6: Configurar Webhook Automáticamente
```bash
# Obtener URL pública de ngrok:
make ngrok-url

# Salida esperada:
# 🌐 Obteniendo URL de ngrok...
# https://abc123.ngrok.io

# Configurar webhook automáticamente:
make ngrok-setup

# ✅ El webhook se configura automáticamente
```

### Paso 7: Probar el Bot
```bash
# 1. Abrir Telegram
# 2. Buscar: @tu_bot (el que creaste)
# 3. Enviar: /start
# 4. Enviar: Hola, ¿cuál es el horario de la piscina?

# Ver logs en tiempo real (Ctrl+C para salir SIN detener el servidor):
make logs

# Cargar datos de prueba (requiere migraciones aplicadas):
make load-fixtures
```

---

## 📋 Comandos Útiles (Makefile)
```bash
make help           # Ver todos los comandos disponibles
make setup          # Instalar todo (solo primera vez)
make up             # Levantar servicios
make down           # Detener servicios
make restart        # Reiniciar servicios
make logs           # Ver logs en tiempo real

# Ngrok (webhooks)
make ngrok-url      # Ver URL pública de ngrok
make ngrok-setup    # Configurar webhook automáticamente

# Base de datos
make migrate        # Aplicar migraciones (crea/actualiza tablas en la DB)
make makemigrations # Crear archivos de migración (solo si cambias modelos)
make load-fixtures  # Cargar datos de prueba
```

**¿Qué son las migraciones?** Son archivos que crean o modifican las tablas en la base de datos (Client, Conversation, Message, etc.). `make migrate` las aplica. Si el bot no responde o load-fixtures falla con "relation clients does not exist", ejecuta `make migrate`.

```bash
# Desarrollo
make shell          # Shell interactivo Django
make test           # Ejecutar tests
make ps             # Ver estado de servicios

# Limpieza
make clean          # Limpiar todo (DB + containers)
```

---

## 🌐 Ngrok Integrado (Sin Instalación Externa)

### ¿Qué es Ngrok?

Ngrok crea un **túnel público** que permite que Telegram (o WhatsApp) envíe mensajes a tu servidor local.
```
Internet (Telegram) → Ngrok → Tu PC (Django)
```

### Ventajas de tenerlo en Docker

✅ **No necesitas instalarlo** en tu PC  
✅ **Funciona para todo el equipo** sin configuración individual  
✅ **Se levanta automáticamente** con `make up`  
✅ **URL pública gratis** para desarrollo  

### Flujo de Trabajo con Ngrok
```bash
# 1. Levantar servicios
make up

# 2. Ver URL pública
make ngrok-url
# Output: https://abc123.ngrok.io

# 3. Configurar webhook automáticamente
make ngrok-setup

# 4. Probar en Telegram
# El bot ya está listo para recibir mensajes
```

### ¿Qué pasa si reinicio el servidor?
```bash
# La URL de ngrok CAMBIA cada vez que reinicias
# Solución automática:

make up           # Levanta servicios (nueva URL)
make ngrok-url    #Obtener URL de ngrok
make ngrok-setup  # Reconfigura webhook automáticamente
```

### Ngrok Dashboard

Abrir en navegador: **http://localhost:4040**

Aquí puedes ver:
- ✅ URL pública actual
- ✅ Todas las peticiones HTTP en tiempo real
- ✅ Headers, body, responses
- ✅ Útil para debugging

---

## 🧪 Testing
```bash
# Ejecutar todos los tests:
make test

# Ver logs durante las pruebas:
make logs

# Cargar datos de prueba:
make load-fixtures
```

### 10 Escenarios de Prueba Incluidos

1. ✅ FAQ simple → Direct Response
2. ✅ Consulta deuda → RAG + Gemini
3. ✅ Audio → Transcripción
4. ✅ Imagen → OCR + análisis
5. ✅ PDF → Extracción de texto
6. ✅ Reporte problema → Ticket Trello
7. ✅ Mensaje confuso → Fallback
8. ✅ Solicitud documento → Ticket
9. ✅ Video → Análisis
10. ✅ Multi-turn → Mantiene contexto

---

## 🔧 Troubleshooting

### 1. "make: command not found"
```bash
# Estás en Windows CMD/PowerShell
# Solución: Usar Ubuntu en WSL2

# En PowerShell:
wsl

# Ahora estás en Ubuntu:
cd /mnt/c/ruta/a/tu/proyecto
make up
```

### 2. "Cannot connect to Docker daemon"
```bash
# Verificar Docker Desktop está corriendo
# En Windows: Abrir Docker Desktop

# En Ubuntu:
docker ps

# Si falla, reiniciar Docker Desktop
```

### 3. Ngrok no muestra URL
```bash
# Verificar que el contenedor ngrok esté corriendo:
docker ps | grep ngrok

# Ver logs de ngrok:
docker logs fran-bot-ngrok

# Verificar NGROK_AUTHTOKEN en .env:
cat backend/.env | grep NGROK_AUTHTOKEN

# Si falta, agregar y reiniciar:
make down
make up
```

### 4. Bot no responde en Telegram
```bash
# 1. Verificar webhook:
make ngrok-setup

# 2. Verificar ALLOWED_HOSTS en backend/.env (debe incluir .ngrok-free.dev,.ngrok.io):
# Si falta, agregar: ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,.ngrok-free.dev,.ngrok.io
# Luego: make restart

# 3. Aplicar migraciones (crea tablas del bot: clients, conversations, messages):
make migrate

# 4. Ver logs:
make logs

# 5. Verificar variables en .env:
cat backend/.env | grep TELEGRAM_BOT_TOKEN
```

### 5. "relation clients does not exist" o load-fixtures falla
```bash
# Las migraciones crean las tablas en la base de datos.
# Si faltan tablas, ejecuta:
make migrate

# Luego vuelve a intentar:
make load-fixtures
```

### 6. Error de permisos en WSL
```bash
# Cambiar propietario del proyecto:
sudo chown -R $USER:$USER /mnt/c/ruta/a/fran-bot-langgraph

# Volver a intentar:
make up
```

---

## 🚀 Migración a Producción

Cuando estés listo para producción:

1. **Desactivar ngrok** (no es para producción)
2. **Configurar dominio real** (ej: bot.tucondominio.com)
3. **Activar WhatsApp + Gmail**
4. **Usar Supabase** para DB y Storage

Ver documentación completa en: `docs/PRODUCCION.md`

---

## 📊 Monitoreo

- **Celery Dashboard**: http://localhost:5555
- **Django Admin**: http://localhost:8000/admin (admin/admin123)
- **Ngrok Dashboard**: http://localhost:4040
- **Logs en tiempo real**: `make logs` (Ctrl+C para salir; el servidor sigue corriendo)

---

## 🤝 Contribuir

1. Fork del repositorio
2. Crear branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

---

## 📄 Licencia

MIT License

---

**¡Construido con ❤️ usando LangGraph + Gemini + Django!**
