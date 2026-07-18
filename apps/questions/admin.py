from django.contrib import admin

from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_text", "question_type", "difficulty", "status", "subject", "created_at"]
    list_filter = ["question_type", "difficulty", "status", "subject"]
    search_fields = ["question_text"]
    readonly_fields = ["times_used", "last_used", "created_at", "updated_at"]
