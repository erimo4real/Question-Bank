from rest_framework import serializers

from .models import ExamPaper, ExamPaperQuestion


class ExamPaperQuestionSerializer(serializers.ModelSerializer):
    question_text = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
    marks = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    topic_name = serializers.SerializerMethodField()

    class Meta:
        model = ExamPaperQuestion
        fields = [
            "id", "question", "order", "marks_override",
            "question_text", "question_type", "options",
            "correct_answer", "explanation", "marks",
            "difficulty", "topic_name",
        ]
        read_only_fields = ["id"]

    def get_question_text(self, obj):
        return obj.question.question_text if obj.question else None

    def get_question_type(self, obj):
        return obj.question.question_type if obj.question else None

    def get_options(self, obj):
        return obj.question.options if obj.question else []

    def get_correct_answer(self, obj):
        return obj.question.correct_answer if obj.question else []

    def get_explanation(self, obj):
        return obj.question.explanation if obj.question else ""

    def get_marks(self, obj):
        if obj.marks_override is not None:
            return obj.marks_override
        return obj.question.marks if obj.question else 0

    def get_difficulty(self, obj):
        return obj.question.difficulty if obj.question else None

    def get_topic_name(self, obj):
        if obj.question and obj.question.topic:
            return obj.question.topic.name
        return None


class ExamPaperSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    computed_total_marks = serializers.IntegerField(read_only=True)
    created_by_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()

    class Meta:
        model = ExamPaper
        fields = [
            "id", "title", "subject", "subject_name", "class_name",
            "academic_session", "term", "duration_minutes", "total_marks",
            "instructions", "school", "created_by", "created_by_name",
            "status", "question_count", "computed_total_marks",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_question_count(self, obj):
        return obj.paper_questions.count()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None

    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None


class ExamPaperDetailSerializer(serializers.ModelSerializer):
    questions = ExamPaperQuestionSerializer(many=True, read_only=True, source="paper_questions")
    created_by_name = serializers.SerializerMethodField()
    subject_name = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()
    computed_total_marks = serializers.IntegerField(read_only=True)

    class Meta:
        model = ExamPaper
        fields = [
            "id", "title", "subject", "subject_name", "class_name",
            "academic_session", "term", "duration_minutes", "total_marks",
            "instructions", "school", "created_by", "created_by_name",
            "status", "question_count", "computed_total_marks", "questions",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None

    def get_subject_name(self, obj):
        return obj.subject.name if obj.subject else None

    def get_question_count(self, obj):
        return obj.paper_questions.count()
