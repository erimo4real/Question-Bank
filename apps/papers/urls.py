from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views as pv

router = DefaultRouter()
router.register("", pv.ExamPaperViewSet, basename="paper")

urlpatterns = [
    # Template views
    path("", pv.PaperListView.as_view(), name="paper-list"),
    path("create/", pv.PaperCreateView.as_view(), name="paper-create"),
    path("<uuid:pk>/", pv.PaperDetailView.as_view(), name="paper-detail"),
    path("<uuid:pk>/edit/", pv.PaperEditView.as_view(), name="paper-edit"),
    path("<uuid:pk>/delete/", pv.PaperDeleteView.as_view(), name="paper-delete"),
    path("<uuid:pk>/add-question/", pv.PaperAddQuestionView.as_view(), name="paper-add-question"),
    path("<uuid:pk>/bulk-add/", pv.PaperBulkAddView.as_view(), name="paper-bulk-add"),
    path("<uuid:paper_pk>/questions/<uuid:pk>/remove/", pv.PaperRemoveQuestionView.as_view(), name="paper-remove-question"),
    path("<uuid:pk>/auto-fill/", pv.PaperAutoFillView.as_view(), name="paper-auto-fill"),
    path("<uuid:pk>/reorder/", pv.PaperReorderView.as_view(), name="paper-reorder"),
    path("<uuid:pk>/export-pdf/", pv.PaperExportPdfView.as_view(), name="paper-export-pdf"),
    path("<uuid:pk>/export-docx/", pv.PaperExportDocxView.as_view(), name="paper-export-docx"),
    path("<uuid:pk>/print-view/", pv.PaperPrintView.as_view(), name="paper-print-view"),
    # DRF API endpoints
    path("api/", include(router.urls)),
]
