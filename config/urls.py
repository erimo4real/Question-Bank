from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from apps.accounts.views import RootRedirectView

urlpatterns = [
    path("", RootRedirectView.as_view(), name="root"),
    path("admin/", admin.site.urls),
    # Template views (server-rendered UI)
    path("api/auth/", include("apps.accounts.urls")),
    path("api/schools/", include("apps.schools.urls")),
    path("api/subjects/", include("apps.subjects.urls")),
    path("api/questions/", include("apps.questions.urls")),
    path("api/papers/", include("apps.papers.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    # Redirect /api/v1/ to template views
    path("api/v1/questions/", lambda r: redirect("question-list")),
    path("api/v1/papers/", lambda r: redirect("paper-list")),
    path("api/v1/schools/", lambda r: redirect("school-list")),
    path("api/v1/subjects/", lambda r: redirect("subject-list")),
    # API docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "django.views.defaults.permission_denied"
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"
