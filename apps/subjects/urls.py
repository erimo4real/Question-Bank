from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as tv

router = DefaultRouter()
router.register("subjects", tv.SubjectViewSet, basename="subject-api")
router.register("topics", tv.TopicViewSet, basename="topic-api")

urlpatterns = [
    # Subject template views
    path("", tv.SubjectListView.as_view(), name="subject-list"),
    path("create/", tv.SubjectCreateView.as_view(), name="subject-create"),
    path("<uuid:pk>/edit/", tv.SubjectEditView.as_view(), name="subject-edit"),
    path("<uuid:pk>/delete/", tv.SubjectDeleteView.as_view(), name="subject-delete"),
    # Inline topic actions (from subject list)
    path("<uuid:subject_pk>/topics/create/", tv.TopicCreateView.as_view(), name="topic-inline-create"),
    path("<uuid:subject_pk>/topics/<uuid:pk>/delete/", tv.TopicDeleteView.as_view(), name="topic-inline-delete"),
    # Standalone topic CRUD
    path("topics/", tv.TopicListView.as_view(), name="topic-list"),
    path("topics/create/", tv.TopicCreateStandaloneView.as_view(), name="topic-create"),
    path("topics/<uuid:pk>/edit/", tv.TopicEditView.as_view(), name="topic-edit"),
    path("topics/<uuid:pk>/delete/", tv.TopicDeleteStandaloneView.as_view(), name="topic-delete"),
    # JSON endpoint for chained dropdowns
    path("topics-by-subject/", tv.TopicsBySubjectView.as_view(), name="topics-by-subject"),
]
