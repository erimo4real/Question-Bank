import uuid

from django.core.exceptions import ValidationError
from django.db import models


class School(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300)
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    logo = models.ImageField(upload_to="schools/logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.email and not self.email.strip():
            raise ValidationError({"email": "Email cannot be blank."})
        if self.phone and not self.phone.strip():
            raise ValidationError({"phone": "Phone cannot be blank."})


class ClassLevel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="e.g. JSS 1, SS 2")
    order = models.PositiveIntegerField(default=0, help_text="Sort order within school")
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="class_levels",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "name"]
        unique_together = ["name", "school"]

    def __str__(self):
        return f"{self.name} ({self.school.name})"

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
