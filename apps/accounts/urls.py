from django.urls import include, path

from . import views

api_urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="api-register"),
    path("login/", views.LoginAPIView.as_view(), name="api-login"),
    path("profile/", views.ProfileView.as_view(), name="api-profile"),
    path("change-password/", views.ChangePasswordView.as_view(), name="api-change-password"),
    path("users/", views.UserListAPIView.as_view(), name="api-user-list"),
]

template_urlpatterns = [
    path("login/", views.LoginTemplateView.as_view(), name="login"),
    path("register/", views.RegisterTemplateView.as_view(), name="register"),
    path("logout/", views.LogoutTemplateView.as_view(), name="logout"),
    path("profile/", views.ProfileTemplateView.as_view(), name="profile"),
    path("settings/", views.SettingsTemplateView.as_view(), name="settings"),
    path("settings/change-password/", views.ProfilePasswordChangeView.as_view(), name="settings-change-password"),
    path("password-reset/", views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/done/", views.PasswordResetDoneView.as_view(), name="password-reset-done"),
    path("password-reset/confirm/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("password-reset/complete/", views.PasswordResetCompleteView.as_view(), name="password-reset-complete"),
    # Admin user management
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/create/", views.UserCreateView.as_view(), name="user-create"),
    path("users/<uuid:pk>/edit/", views.UserEditView.as_view(), name="user-edit"),
    path("users/<uuid:pk>/delete/", views.UserDeleteView.as_view(), name="user-delete"),
]

urlpatterns = [
    path("", include(template_urlpatterns)),
    path("api/", include(api_urlpatterns)),
]
