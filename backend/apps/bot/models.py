from django.db import models
from django.utils import timezone


class Client(models.Model):
    """Cliente del condominio."""

    # Sincronización con Supabase
    supabase_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="UUID del cliente en Supabase (para sincronización)",
    )

    # Información personal
    name = models.CharField(max_length=200)
    dni = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="DNI/Pasaporte",
        help_text="Documento de identidad",
    )

    # Contacto (al menos uno obligatorio)
    phone = models.CharField(
        max_length=20,
        unique=True,
        help_text="Formato: +51987654321",
    )
    email = models.EmailField(null=True, blank=True)

    # Ubicación en el condominio
    unit_number = models.CharField(
        max_length=50, verbose_name="Número de Unidad")
    building = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Torre/Edificio",
    )
    floor = models.IntegerField(null=True, blank=True, verbose_name="Piso")

    # Estado financiero
    has_debt = models.BooleanField(default=False, verbose_name="Tiene Deuda")
    debt_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Monto de Deuda",
    )
    last_payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Última Fecha de Pago",
    )

    # Preferencias
    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("telegram", "Telegram"),
            ("whatsapp", "WhatsApp"),
            ("email", "Email"),
            ("phone_call", "Llamada Telefónica"),
        ],
        default="whatsapp",
        verbose_name="Método de Contacto Preferido",
    )

    # Metadata
    notes = models.TextField(
        blank=True, help_text="Notas internas sobre el cliente")
    is_active = models.BooleanField(
        default=True,
        help_text="Cliente activo en el sistema",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "clients"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["email"]),
            models.Index(fields=["unit_number"]),
            models.Index(fields=["has_debt"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} - Unidad {self.unit_number}"

    def get_contact_info(self) -> dict:
        """Retorna dict con info de contacto formateada."""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email or "No registrado",
            "dni": self.dni or "No registrado",
            "unit_number": self.unit_number,
            "building": self.building or "N/A",
            "floor": self.floor or "N/A",
            "has_debt": self.has_debt,
            "debt_amount": float(self.debt_amount or 0),
            "last_payment_date": (
                self.last_payment_date.isoformat() if self.last_payment_date else None
            ),
            "preferred_contact_method": self.preferred_contact_method,
        }


class Conversation(models.Model):
    """Conversación procesada por el agente IA."""

    # Identificación única
    conversation_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="UUID de la conversación",
    )

    # Relación con cliente
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    # Canal de comunicación
    channel = models.CharField(
        max_length=20,
        choices=[
            ("telegram", "Telegram"),
            ("whatsapp", "WhatsApp"),
            ("email", "Email"),
        ],
        help_text="Canal por el que se recibió el mensaje",
    )

    # Estado de la conversación
    state = models.CharField(
        max_length=20,
        choices=[
            ("waiting", "Esperando Procesamiento"),
            ("processing", "Procesando"),
            ("ai_resolved", "Resuelto por IA"),
            ("fallback", "Fallback Activado"),
            ("closed", "Cerrado"),
        ],
        default="waiting",
    )

    # Calidad y tracking
    quality_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Score de calidad de la respuesta IA (0.0 - 1.0)",
    )
    used_fallback = models.BooleanField(
        default=False,
        help_text="Si se activó el Fallback Node",
    )
    fallback_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Razón por la que se activó fallback",
    )

    # Ticket Trello asociado
    trello_card_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID de la tarjeta en Trello",
    )
    trello_card_url = models.URLField(
        null=True,
        blank=True,
        help_text="URL de la tarjeta en Trello",
    )
    trello_priority = models.CharField(
        max_length=20,
        choices=[
            ("LOW", "Baja"),
            ("MEDIUM", "Media"),
            ("HIGH", "Alta"),
            ("URGENT", "Urgente"),
        ],
        null=True,
        blank=True,
    )

    # Contexto y datos
    context = models.JSONField(
        default=dict,
        help_text="Contexto de la conversación (intención, rag_results, etc.)",
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Metadata adicional (IP, user agent, etc.)",
    )

    # Snapshot de contacto (por si el cliente cambia sus datos)
    contact_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Datos de contacto del cliente al momento de la conversación",
    )

    # Métricas de tiempo
    processing_time_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Tiempo total de procesamiento",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cuándo se resolvió la conversación",
    )

    class Meta:
        db_table = "conversations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["conversation_id"]),
            models.Index(fields=["client", "-created_at"]),
            models.Index(fields=["state"]),
            models.Index(fields=["used_fallback"]),
            models.Index(fields=["trello_card_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.conversation_id} - {self.client.name} ({self.channel})"

    def save(self, *args, **kwargs) -> None:
        # Auto-guardar snapshot de contacto en la primera vez
        if not self.pk and not self.contact_snapshot:
            self.contact_snapshot = self.client.get_contact_info()
        super().save(*args, **kwargs)


class Message(models.Model):
    """Mensaje individual dentro de una conversación."""

    # Relación con conversación
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    # Rol del mensaje
    role = models.CharField(
        max_length=20,
        choices=[
            ("user", "Usuario"),
            ("assistant", "Asistente IA"),
            ("system", "Sistema"),
        ],
    )

    # Contenido
    content = models.TextField(
        help_text="Texto del mensaje o transcripción de audio",
    )

    # ⭐ MULTIMEDIA: Archivos adjuntos
    attachments = models.JSONField(
        default=list,
        help_text="""
        Lista de archivos multimedia adjuntos.
        Formato: [
            {
                "type": "audio|image|video|pdf",
                "url": "/media/... o https://supabase...",
                "filename": "archivo.ext",
                "size_bytes": 12345,
                "mime_type": "audio/ogg",
                "transcription": "...",  # Solo para audio
                "analysis": "...",       # Para imagen/pdf
                "duration_seconds": 10   # Solo para audio/video
            }
        ]
        """,
    )

    # Tracking de procesamiento
    node_executed = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Qué nodo de LangGraph generó este mensaje",
    )
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo de procesamiento en milisegundos",
    )

    # Metadata
    telegram_message_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID del mensaje en Telegram",
    )
    whatsapp_message_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID del mensaje en WhatsApp",
    )
    gmail_message_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID del mensaje en Gmail",
    )

    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "messages"
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["conversation", "timestamp"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self) -> str:
        preview = self.content[:50] + \
            "..." if len(self.content) > 50 else self.content
        return f"{self.get_role_display()}: {preview}"

    def has_multimedia(self) -> bool:
        """Retorna True si el mensaje tiene archivos adjuntos."""
        return len(self.attachments) > 0

    def get_multimedia_summary(self) -> str:
        """Retorna resumen de archivos adjuntos."""
        if not self.has_multimedia():
            return "Sin archivos"

        types = [att.get("type", "unknown") for att in self.attachments]
        return f"{len(self.attachments)} archivo(s): {', '.join(types)}"


class Announcement(models.Model):
    """Avisos informativos para los residentes."""

    title = models.CharField(max_length=200)
    content = models.TextField()
    target_building = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Torre específica o vacío para todas",
    )
    target_floor = models.IntegerField(
        null=True,
        blank=True,
        help_text="Piso específico o vacío para todos",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "announcements"
        verbose_name = "Aviso"

    def __str__(self) -> str:
        return f"{self.title} ({self.target_building or 'Global'})"


class Rule(models.Model):
    """Reglamento del condominio (RAG para Gemini)."""

    category = models.CharField(
        max_length=100,
        help_text="Ej: Piscina, Mascotas, Ruidos",
    )
    rule_text = models.TextField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rules"
        verbose_name = "Regla"

    def __str__(self) -> str:
        return f"{self.category}: {self.rule_text[:50]}..."

