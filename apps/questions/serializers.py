from rest_framework import serializers

from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "question_type",
            "options",
            "correct_answer",
            "explanation",
            "marks",
            "difficulty",
            "subject",
            "topic",
            "image",
            "tags",
            "status",
            "times_used",
            "last_used",
            "school",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "times_used", "last_used", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None


class QuestionPreviewSerializer(serializers.ModelSerializer):
    """Used by students — hides correct answers and explanations."""
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "question_type",
            "options",
            "marks",
            "difficulty",
            "subject",
            "topic",
            "image",
            "tags",
            "times_used",
            "created_by_name",
            "created_at",
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None


class BulkActionSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)


class BulkStatusSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    status = serializers.ChoiceField(choices=Question.STATUS_CHOICES)


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), min_length=1)
