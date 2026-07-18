from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("", views.SchoolViewSet, basename="school-api")

urlpatterns = [
    path("", views.SchoolListView.as_view(), name="school-list"),
    path("create/", views.SchoolCreateView.as_view(), name="school-create"),
    path("<uuid:pk>/edit/", views.SchoolEditView.as_view(), name="school-edit"),
    path("<uuid:pk>/delete/", views.SchoolDeleteView.as_view(), name="school-delete"),
]
