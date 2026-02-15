# Makefile para Fran Bot

.PHONY: help setup up down restart logs shell test clean ps load-fixtures ngrok-url ngrok-setup

# Variables
COMPOSE=docker-compose
COMPOSE_FILE=docker-compose.yml
WEB_SERVICE=web

help: ## Mostrar ayuda
	@echo "╔══════════════════════════════════════════════════════════╗"
	@echo "║          🤖 FRAN BOT - COMANDOS DISPONIBLES              ║"
	@echo "╚══════════════════════════════════════════════════════════╝"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Instalar todo (build + DB + migraciones)
	@echo "🔧 Instalando Fran Bot..."
	@$(COMPOSE) down -v
	@$(COMPOSE) build --no-cache
	@$(COMPOSE) up -d db redis
	@echo "⏳ Esperando a PostgreSQL..."
	@sleep 5
	@$(COMPOSE) run --rm $(WEB_SERVICE) python manage.py migrate
	@$(COMPOSE) run --rm $(WEB_SERVICE) python manage.py collectstatic --noinput
	@echo "👤 Creando superusuario..."
	@$(COMPOSE) run --rm $(WEB_SERVICE) python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@franbot.com', 'admin123')"
	@echo "✅ Instalación completa"
	@echo ""
	@echo "Próximo paso: make up"

up: ## Levantar servicios
	@echo "🚀 Levantando servicios..."
	@$(COMPOSE) up -d
	@echo "✅ Servicios iniciados"
	@echo ""
	@echo "📊 Dashboard Celery: http://localhost:5555"
	@echo "🔧 Django Admin: http://localhost:8000/admin (admin/admin123)"
	@echo "🌐 Ngrok Dashboard: http://localhost:4040"
	@echo ""
	@echo "⏳ Esperando 5 segundos a que ngrok inicie..."
	@sleep 5
	@echo ""
	@echo "Obtener URL de ngrok: make ngrok-url"
	@echo "Configurar webhook: make ngrok-setup"

down: ## Detener servicios
	@echo "⏹️  Deteniendo servicios..."
	@$(COMPOSE) down
	@echo "✅ Servicios detenidos"

restart: ## Reiniciar servicios
	@echo "🔄 Reiniciando servicios..."
	@$(COMPOSE) restart
	@echo "✅ Servicios reiniciados"

logs: ## Ver logs (Ctrl+C para salir)
	@$(COMPOSE) logs -f --tail=100

shell: ## Shell interactivo Django
	@$(COMPOSE) exec $(WEB_SERVICE) python manage.py shell

test: ## Ejecutar tests
	@echo "🧪 Ejecutando tests..."
	@$(COMPOSE) run --rm $(WEB_SERVICE) pytest tests/ -v --tb=short
	@echo "✅ Tests completados"

clean: ## Limpiar todo (DB + containers + volumes)
	@echo "🗑️  Limpiando todo..."
	@$(COMPOSE) down -v
	@docker system prune -f
	@echo "✅ Limpieza completa"

ps: ## Ver estado de servicios
	@$(COMPOSE) ps

load-fixtures: ## Cargar datos de prueba
	@echo "📦 Cargando datos de prueba..."
	@$(COMPOSE) exec $(WEB_SERVICE) python manage.py loaddata fixtures/mock_data.json
	@echo "✅ Datos cargados"
	@echo ""
	@echo "Clientes disponibles:"
	@echo "  +51987654321 - Juan Pérez (Unidad 101)"
	@echo "  +51987654322 - María López (Unidad 202)"
	@echo "  +51987654323 - Carlos Ruiz (Unidad 303)"

ngrok-url: ## Obtener URL pública de ngrok
	@echo "🌐 Obteniendo URL de ngrok..."
	@echo ""
	@curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' || echo "⚠️  Ngrok no está activo. Ejecuta: make up"
	@echo ""

ngrok-setup: ## Configurar webhook automáticamente
	@echo "🔧 Configurando webhook de Telegram..."
	@echo ""
	@NGROK_URL=$$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -n1); \
	if [ -z "$$NGROK_URL" ]; then \
		echo "❌ No se pudo obtener URL de ngrok. ¿Está corriendo?"; \
		echo "   Ejecuta: make up"; \
		exit 1; \
	fi; \
	echo "📍 URL detectada: $$NGROK_URL"; \
	echo ""; \
	$(COMPOSE) exec $(WEB_SERVICE) python manage.py setup_telegram_webhook $$NGROK_URL; \
	echo ""; \
	echo "✅ Webhook configurado exitosamente"

migrate: ## Ejecutar migraciones
	@$(COMPOSE) exec $(WEB_SERVICE) python manage.py migrate

makemigrations: ## Crear migraciones
	@$(COMPOSE) exec $(WEB_SERVICE) python manage.py makemigrations

superuser: ## Crear superusuario
	@$(COMPOSE) exec $(WEB_SERVICE) python manage.py createsuperuser

celery-status: ## Ver estado de Celery
	@echo "🔍 Estado de Celery:"
	@$(COMPOSE) exec celery celery -A config inspect active

backup-db: ## Backup de base de datos
	@echo "💾 Creando backup..."
	@docker exec fran-bot-db pg_dump -U fran_user fran_bot_db > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup creado: backup_$(shell date +%Y%m%d_%H%M%S).sql"

restore-db: ## Restaurar base de datos (restore-db FILE=backup.sql)
	@echo "📥 Restaurando desde $(FILE)..."
	@$(COMPOSE) down
	@$(COMPOSE) up -d db
	@sleep 3
	@docker exec -i fran-bot-db psql -U fran_user fran_bot_db < $(FILE)
	@$(COMPOSE) up -d
	@echo "✅ Base de datos restaurada"