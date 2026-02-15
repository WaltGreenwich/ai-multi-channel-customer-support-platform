"""
Configuración de Celery para Fran Bot
"""
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('fran_bot')

# Cargar config desde Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tasks
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
