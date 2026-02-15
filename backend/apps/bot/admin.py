from django.contrib import admin

from .models import Announcement, Client, Conversation, Message, Rule


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "unit_number",
        "building",
        "phone",
        "email",
        "has_debt",
        "debt_amount",
        "is_active",
    )
    list_filter = ("has_debt", "is_active", "building")
    search_fields = ("name", "phone", "email", "unit_number", "dni")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "conversation_id",
        "client",
        "channel",
        "state",
        "used_fallback",
        "trello_priority",
        "created_at",
        "resolved_at",
    )
    list_filter = ("channel", "state", "used_fallback", "trello_priority")
    search_fields = ("conversation_id", "client__name", "client__phone")
    readonly_fields = (
        "created_at",
        "updated_at",
        "resolved_at",
        "contact_snapshot",
        "context",
        "metadata",
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "conversation",
        "role",
        "short_content",
        "timestamp",
        "node_executed",
    )
    list_filter = ("role",)
    search_fields = ("conversation__conversation_id", "content")
    readonly_fields = ("timestamp",)

    def short_content(self, obj: Message) -> str:  # type: ignore[name-defined]
        text = obj.content or ""
        return text[:60] + "..." if len(text) > 60 else text

    short_content.short_description = "Contenido"  # type: ignore[attr-defined]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "target_building", "target_floor", "is_active", "created_at")
    list_filter = ("is_active", "target_building")
    search_fields = ("title", "content")


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("category", "rule_text_short", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("category", "rule_text")

    def rule_text_short(self, obj: Rule) -> str:  # type: ignore[name-defined]
        return obj.rule_text[:60] + "..." if len(obj.rule_text) > 60 else obj.rule_text

    rule_text_short.short_description = "Regla"  # type: ignore[attr-defined]
