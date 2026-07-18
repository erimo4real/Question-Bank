import uuid

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.exceptions import ValidationError
from django.db import models


class Question(models.Model):
    TYPE_CHOICES = [
        ("mcq", "Multiple Choice"),
        ("true_false", "True / False"),
        ("fill_blank", "Fill in the Blank"),
        ("essay", "Essay"),
        ("matching", "Matching"),
        ("ordering", "Ordering / Sequence"),
        ("image", "Image-based"),
    ]

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True, default="")
    marks = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    subject = models.ForeignKey(
        "subjects.Subject",
        on_delete=models.CASCADE,
        related_name="questions",
    )
    topic = models.ForeignKey(
        "subjects.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
    )
    image = models.ImageField(upload_to="questions/", blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    times_used = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(null=True, blank=True)
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.CASCADE,
        related_name="questions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_questions",
    )
    search_vector = SearchVectorField(null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            GinIndex(fields=["search_vector"], name="question_search_idx"),
            models.Index(fields=["question_type"], name="question_type_idx"),
            models.Index(fields=["difficulty"], name="question_difficulty_idx"),
            models.Index(fields=["status"], name="question_status_idx"),
            models.Index(fields=["subject"], name="question_subject_idx"),
            models.Index(fields=["school"], name="question_school_idx"),
        ]

    def __str__(self):
        return f"[{self.get_question_type_display()}] {self.question_text[:80]}"

    def clean(self):
        super().clean()
        if not self.question_text or not self.question_text.strip():
            raise ValidationError({"question_text": "Question text is required."})
        if self.question_type == "mcq":
            if not self.options or len(self.options) < 2:
                raise ValidationError({"options": "MCQ requires at least 2 options."})
            if not self.correct_answer:
                raise ValidationError({"correct_answer": "MCQ requires a correct answer."})
        elif self.question_type == "true_false":
            valid_tf = {"true", "false"}
            if self.correct_answer:
                answers = [a.lower() for a in self.correct_answer]
                for a in answers:
                    if a not in valid_tf:
                        raise ValidationError({"correct_answer": "True/False answers must be 'true' or 'false'."})
        if self.marks < 1:
            raise ValidationError({"marks": "Marks must be at least 1."})
        if self.image and self.image.size and self.image.size > 5 * 1024 * 1024:
            raise ValidationError({"image": "Image must be less than 5MB."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.contrib.postgres.search import SearchVector
        Question.objects.filter(pk=self.pk).update(
            search_vector=(
                SearchVector("question_text", weight="A")
                + SearchVector("explanation", weight="B")
            )
        )
