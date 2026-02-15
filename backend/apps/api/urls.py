from django.urls import path

from . import views

urlpatterns = [
    path("telegram/webhook/", views.telegram_webhook, name="telegram-webhook"),
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp-webhook"),
    path("gmail/webhook/", views.gmail_webhook, name="gmail-webhook"),
]

