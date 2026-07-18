from django.contrib import admin

from .models import Subject, Topic


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "school", "created_at"]
    list_filter = ["school"]
    search_fields = ["name", "code"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "subject", "created_at"]
    list_filter = ["subject"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
