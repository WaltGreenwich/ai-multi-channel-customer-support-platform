FROM python:3.11-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código
COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/media/uploads /app/staticfiles

# Permisos
RUN chmod +x /app/entrypoint.sh

# Exponer puerto
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]