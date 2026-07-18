import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "super_admin")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("admin", "Admin"),
        ("teacher", "Teacher"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = None
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="teacher")
    school = models.ForeignKey(
        "schools.School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    subjects = models.ManyToManyField(
        "subjects.Subject",
        blank=True,
        related_name="assigned_teachers",
        help_text="Subjects this teacher is assigned to (teachers only)",
    )
    phone = models.CharField(max_length=20, blank=True, default="")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["role"], name="user_role_idx"),
            models.Index(fields=["school"], name="user_school_idx"),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.email}"

    @property
    def is_super_admin_role(self):
        return self.role == "super_admin"

    @property
    def is_admin_role(self):
        return self.role in ("admin", "super_admin")

    @property
    def is_teacher_role(self):
        return self.role == "teacher"

    @property
    def is_school_admin_role(self):
        return self.role == "admin"
