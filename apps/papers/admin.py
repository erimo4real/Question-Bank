from django.contrib import admin

from .models import ExamPaper, ExamPaperQuestion


class ExamPaperQuestionInline(admin.TabularInline):
    model = ExamPaperQuestion
    extra = 0
    readonly_fields = ["question", "order"]


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ["title", "subject", "class_name", "status", "created_at"]
    list_filter = ["status", "subject"]
    search_fields = ["title"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [ExamPaperQuestionInline]


@admin.register(ExamPaperQuestion)
class ExamPaperQuestionAdmin(admin.ModelAdmin):
    list_display = ["exam_paper", "question", "order", "marks_override"]
    list_filter = ["exam_paper"]
