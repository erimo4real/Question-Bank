import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class ExamPaper(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("finalized", "Finalized"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300)
    subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.CASCADE,
        related_name="exam_papers",
    )
    class_name = models.CharField(max_length=100, blank=True, default="")
    class_level = models.ForeignKey(
        "schools.ClassLevel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exam_papers",
    )
    academic_session = models.CharField(max_length=50, blank=True, default="")
    term = models.CharField(max_length=50, blank=True, default="")
    duration_minutes = models.PositiveIntegerField(default=60)
    total_marks = models.PositiveIntegerField(default=100)
    instructions = models.TextField(blank=True, default="")
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="exam_papers",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_papers",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="paper_status_idx"),
            models.Index(fields=["subject"], name="paper_subject_idx"),
            models.Index(fields=["school"], name="paper_school_idx"),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.title or not self.title.strip():
            raise ValidationError({"title": "Paper title is required."})
        if self.duration_minutes and self.duration_minutes < 1:
            raise ValidationError({"duration_minutes": "Duration must be at least 1 minute."})
        if self.total_marks and self.total_marks < 1:
            raise ValidationError({"total_marks": "Total marks must be at least 1."})

    @property
    def computed_total_marks(self):
        total = 0
        for pq in self.paper_questions.select_related("question"):
            if pq.marks_override is not None:
                total += pq.marks_override
            else:
                total += pq.question.marks
        return total

    @property
    def question_count(self):
        return self.paper_questions.count()


class ExamPaperQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_paper = models.ForeignKey(
        ExamPaper,
        on_delete=models.CASCADE,
        related_name="paper_questions",
    )
    question = models.ForeignKey(
        "questions.Question",
        on_delete=models.CASCADE,
        related_name="paper_links",
    )
    order = models.PositiveIntegerField(default=0)
    marks_override = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["exam_paper", "question"]
        constraints = [
            models.UniqueConstraint(
                fields=["exam_paper", "order"],
                name="unique_paper_question_order",
            ),
        ]

    def __str__(self):
        return f"{self.exam_paper.title} - Q{self.order}"

    def clean(self):
        super().clean()
        if self.order < 1:
            raise ValidationError({"order": "Order must be at least 1."})
        if self.marks_override is not None and self.marks_override < 1:
            raise ValidationError({"marks_override": "Marks override must be at least 1."})
