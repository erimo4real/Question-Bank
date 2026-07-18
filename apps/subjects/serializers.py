from rest_framework import serializers

from .models import Subject, Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "name", "subject", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubjectSerializer(serializers.ModelSerializer):
    topic_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ["id", "name", "code", "description", "school", "created_by", "topic_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_topic_count(self, obj):
        return obj.topics.count()


class SubjectDetailSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = Subject
        fields = ["id", "name", "code", "description", "school", "created_by", "topics", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
