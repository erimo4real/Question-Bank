from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
)
from django.contrib.auth.tokens import default_token_generator
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlsafe_base64_decode
from django.views import View
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.forms import (
    LoginForm,
    PasswordChangeForm,
    RegisterForm,
    SettingsForm,
    UserForm,
)
from apps.accounts.permissions import AdminRequiredMixin, IsAdmin
from apps.schools.models import School
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class RootRedirectView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return redirect("login")


# ─── Template Views ───────────────────────────────────────────────

class LoginTemplateView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = LoginForm()
        return render(request, "accounts/login.html", {"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            remember_me = form.cleaned_data.get("remember_me")
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                return redirect("dashboard")
        messages.error(request, "Invalid email or password.")
        return render(request, "accounts/login.html", {"form": form})


class RegisterTemplateView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = RegisterForm()
        return render(request, "accounts/register.html", {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = "teacher"
            user.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("dashboard")
        messages.error(request, "Please correct the errors below.")
        return render(request, "accounts/register.html", {"form": form})


class LogoutTemplateView(View):
    def get(self, request):
        logout(request)
        return redirect("login")


class ProfileTemplateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "accounts/profile.html")


class SettingsTemplateView(LoginRequiredMixin, View):
    def get(self, request):
        form = SettingsForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
        return render(request, "accounts/settings.html", {"form": form, "password_form": password_form})

    def post(self, request):
        form = SettingsForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get("remove_avatar"):
                if user.avatar:
                    user.avatar.delete(save=False)
                    user.avatar = None
            user.save()
            messages.success(request, "Profile updated!")
            return redirect("settings")
        password_form = PasswordChangeForm(user=request.user)
        return render(request, "accounts/settings.html", {"form": form, "password_form": password_form})


class ProfilePasswordChangeView(LoginRequiredMixin, View):
    def post(self, request):
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password changed successfully!")
            return redirect("settings")
        messages.error(request, "Please correct the errors below.")
        settings_form = SettingsForm(instance=request.user)
        return render(request, "accounts/settings.html", {"form": settings_form, "password_form": form})


class PasswordResetRequestView(View):
    def get(self, request):
        return render(request, "accounts/password_reset.html")

    def post(self, request):
        email = request.POST.get("email", "")
        users = User.objects.filter(email__iexact=email)
        if users.exists():
            for user in users:
                token = default_token_generator.make_token(user)
                uid = user.pk
                reset_url = request.build_absolute_uri(
                    f"/api/auth/password-reset/confirm/{uid}/{token}/"
                )
                print(f"\n{'='*60}")
                print(f"PASSWORD RESET LINK for {user.email}:")
                print(f"{reset_url}")
                print(f"{'='*60}\n")
            messages.success(request, "If an account exists with that email, a reset link has been sent.")
        else:
            messages.success(request, "If an account exists with that email, a reset link has been sent.")
        return redirect("password-reset-done")


class PasswordResetDoneView(View):
    def get(self, request):
        return render(request, "accounts/password_reset_done.html", {"dev_mode": True})


class PasswordResetConfirmView(View):
    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is not None and default_token_generator.check_token(user, token):
            return render(request, "accounts/password_reset_confirm.html", {"validlink": True, "uidb64": uidb64, "token": token})
        return render(request, "accounts/password_reset_confirm.html", {"validlink": False})

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        if user is None or not default_token_generator.check_token(user, token):
            return render(request, "accounts/password_reset_confirm.html", {"validlink": False})
        from apps.accounts.forms import PasswordChangeForm
        form = PasswordChangeForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect("password-reset-complete")
        messages.error(request, "Please correct the errors below.")
        return render(request, "accounts/password_reset_confirm.html", {
            "validlink": True, "uidb64": uidb64, "token": token, "form": form,
        })


class PasswordResetCompleteView(View):
    def get(self, request):
        return render(request, "accounts/password_reset_complete.html")


# ─── Admin User Management ──────────────────────────────────────

class UserListView(AdminRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            users = User.objects.all().select_related("school").order_by("-created_at")
        else:
            users = User.objects.filter(school=request.user.school).select_related("school").order_by("-created_at")

        q = request.GET.get("q", "")
        role_filter = request.GET.get("role", "")

        if q:
            users = users.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        if role_filter:
            users = users.filter(role=role_filter)

        paginator = Paginator(users, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return render(request, "accounts/user_list.html", {
            "users": page_obj, "page_obj": page_obj, "q": q, "role_filter": role_filter,
            "role_choices": User.ROLE_CHOICES,
        })


class UserCreateView(AdminRequiredMixin, View):
    def get(self, request):
        from apps.subjects.models import Subject
        form = UserForm()
        if request.user.is_super_admin_role:
            schools = School.objects.all().order_by("name")
            subjects = Subject.objects.all().order_by("name")
        else:
            schools = School.objects.filter(pk=request.user.school_id)
            subjects = Subject.objects.filter(school=request.user.school)
        return render(request, "accounts/user_form.html", {
            "edit_user": None, "form": form, "schools": schools, "subjects": subjects,
        })

    def post(self, request):
        from apps.subjects.models import Subject
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if not request.user.is_super_admin_role and not user.school:
                user.school = request.user.school
            user.save()
            form.save_m2m()
            if user.role == "teacher" and form.cleaned_data.get("subjects"):
                user.subjects.set(form.cleaned_data["subjects"])
            messages.success(request, f'User "{user.email}" created.')
            return redirect("user-list")
        if request.user.is_super_admin_role:
            schools = School.objects.all().order_by("name")
            subjects = Subject.objects.all().order_by("name")
        else:
            schools = School.objects.filter(pk=request.user.school_id)
            subjects = Subject.objects.filter(school=request.user.school)
        return render(request, "accounts/user_form.html", {
            "edit_user": None, "form": form, "schools": schools, "subjects": subjects,
        })


class UserEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        from apps.subjects.models import Subject
        edit_user = get_object_or_404(User, pk=pk)
        if not request.user.is_super_admin_role and edit_user.school != request.user.school:
            messages.error(request, "You cannot edit users from other schools.")
            return redirect("user-list")
        form = UserForm(instance=edit_user, is_edit=True)
        if request.user.is_super_admin_role:
            schools = School.objects.all().order_by("name")
            subjects = Subject.objects.all().order_by("name")
        else:
            schools = School.objects.filter(pk=request.user.school_id)
            subjects = Subject.objects.filter(school=request.user.school)
        return render(request, "accounts/user_form.html", {
            "edit_user": edit_user, "form": form, "schools": schools, "subjects": subjects,
        })

    def post(self, request, pk):
        from apps.subjects.models import Subject
        edit_user = get_object_or_404(User, pk=pk)
        if not request.user.is_super_admin_role and edit_user.school != request.user.school:
            messages.error(request, "You cannot edit users from other schools.")
            return redirect("user-list")
        form = UserForm(request.POST, instance=edit_user, is_edit=True)
        if form.is_valid():
            user = form.save(commit=False)
            if not request.user.is_super_admin_role and not user.school:
                user.school = request.user.school
            user.save()
            form.save_m2m()
            if user.role == "teacher" and form.cleaned_data.get("subjects"):
                user.subjects.set(form.cleaned_data["subjects"])
            else:
                user.subjects.clear()
            messages.success(request, f'User "{user.email}" updated.')
            return redirect("user-list")
        if request.user.is_super_admin_role:
            schools = School.objects.all().order_by("name")
            subjects = Subject.objects.all().order_by("name")
        else:
            schools = School.objects.filter(pk=request.user.school_id)
            subjects = Subject.objects.filter(school=request.user.school)
        return render(request, "accounts/user_form.html", {
            "edit_user": edit_user, "form": form, "schools": schools, "subjects": subjects,
        })


class UserDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if not request.user.is_super_admin_role and user.school != request.user.school:
            messages.error(request, "You cannot delete users from other schools.")
            return redirect("user-list")
        if user.pk == request.user.pk:
            messages.error(request, "You cannot delete your own account.")
            return redirect("user-list")
        email = user.email
        user.delete()
        messages.success(request, f'User "{email}" deleted.')
        return redirect("user-list")


# ─── API Views (unchanged) ───────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
            }
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"message": "Password changed"})


class UserListAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    queryset = User.objects.all()
    search_fields = ["email", "first_name", "last_name"]
    filterset_fields = ["role"]
