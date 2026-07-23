from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as qv

router = DefaultRouter()
router.register("", qv.QuestionViewSet, basename="question")

urlpatterns = [
    # Template views
    path("", qv.QuestionListView.as_view(), name="question-list"),
    path("create/", qv.QuestionCreateView.as_view(), name="question-create"),
    path("<uuid:pk>/edit/", qv.QuestionEditView.as_view(), name="question-edit"),
    path("<uuid:pk>/delete/", qv.QuestionDeleteView.as_view(), name="question-delete"),
    path("<uuid:pk>/preview/", qv.QuestionPreviewView.as_view(), name="question-preview"),
    path("import/", qv.QuestionImportView.as_view(), name="question-import"),
    path("bulk-delete/", qv.QuestionBulkDeleteView.as_view(), name="question-bulk-delete"),
    path("bulk-status/", qv.QuestionBulkStatusView.as_view(), name="question-bulk-status"),
    # DRF API endpoints
    path("api/", include(router.urls)),
]
