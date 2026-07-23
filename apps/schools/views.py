import json

from django.contrib import messages as dj_messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from rest_framework import viewsets

from apps.accounts.forms import SchoolForm
from apps.accounts.permissions import AdminRequiredMixin, IsAdminOrTeacher, SuperAdminRequiredMixin

from .forms import ClassLevelForm
from .models import ClassLevel, School
from .serializers import SchoolSerializer


def _htmx_messages(request):
    """Return X-Messages header dict for HTMX responses."""
    msgs = [{"text": str(m), "tag": m.tags} for m in dj_messages.get_messages(request)]
    return {"X-Messages": json.dumps(msgs)}


def _htmx_render(request, template, ctx=None, **kwargs):
    response = render(request, template, ctx, **kwargs)
    for key, val in _htmx_messages(request).items():
        response[key] = val
    return response


class SchoolListView(SuperAdminRequiredMixin, View):
    def get(self, request):
        schools = School.objects.all().order_by("name")

        q = request.GET.get("q", "")
        if q:
            schools = schools.filter(name__icontains=q)

        paginator = Paginator(schools, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        ctx = {"schools": page_obj, "page_obj": page_obj, "q": q}
        template = "schools/_list_content.html" if request.headers.get("HX-Request") else "schools/list.html"
        return render(request, template, ctx)


class SchoolCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        form = SchoolForm()
        template = "schools/_form_content.html" if request.headers.get("HX-Request") else "schools/form.html"
        return render(request, template, {"school": None, "form": form})

    def post(self, request):
        form = SchoolForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            dj_messages.success(request, "School created!")
            if request.headers.get("HX-Request"):
                return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("school-list")})
            return redirect("school-list")
        template = "schools/_form_content.html" if request.headers.get("HX-Request") else "schools/form.html"
        return _htmx_render(request, template, {"school": None, "form": form})


class SchoolEditView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        form = SchoolForm(instance=school)
        template = "schools/_form_content.html" if request.headers.get("HX-Request") else "schools/form.html"
        return render(request, template, {"school": school, "form": form})

    def post(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        form = SchoolForm(request.POST, request.FILES, instance=school)
        if form.is_valid():
            form.save()
            dj_messages.success(request, "School updated!")
            if request.headers.get("HX-Request"):
                return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("school-list")})
            return redirect("school-list")
        template = "schools/_form_content.html" if request.headers.get("HX-Request") else "schools/form.html"
        return _htmx_render(request, template, {"school": school, "form": form})


class SchoolDeleteView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        school.delete()
        dj_messages.success(request, "School deleted.")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers=_htmx_messages(request))
        return redirect("school-list")


class SchoolViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolSerializer
    queryset = School.objects.all()
    search_fields = ["name"]
    permission_classes = [IsAdminOrTeacher]


# ─── Class Level Views ──────────────────────────────────────────

class ClassLevelListView(AdminRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            class_levels = ClassLevel.objects.select_related("school").order_by("school__name", "order", "name")
        else:
            class_levels = ClassLevel.objects.filter(school=request.user.school).select_related("school").order_by("order", "name")

        q = request.GET.get("q", "")
        school_filter = request.GET.get("school", "")
        if q:
            class_levels = class_levels.filter(name__icontains=q)
        if school_filter:
            class_levels = class_levels.filter(school_id=school_filter)

        paginator = Paginator(class_levels, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        from apps.schools.models import School  # noqa: F811
        if request.user.is_super_admin_role:
            schools = School.objects.all()
        else:
            schools = School.objects.filter(pk=request.user.school_id)

        ctx = {
            "class_levels": page_obj, "page_obj": page_obj, "q": q, "school_filter": school_filter,
            "schools": schools,
        }
        template = "schools/_classlevel_list_content.html" if request.headers.get("HX-Request") else "schools/classlevel_list.html"
        return render(request, template, ctx)


class ClassLevelCreateView(AdminRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            school_queryset = School.objects.all()
        else:
            school_queryset = School.objects.filter(pk=request.user.school_id)
        form = ClassLevelForm(school_queryset=school_queryset)
        template = "schools/_classlevel_form_content.html" if request.headers.get("HX-Request") else "schools/classlevel_form.html"
        return render(request, template, {"class_level": None, "form": form})

    def post(self, request):
        if request.user.is_super_admin_role:
            school_queryset = School.objects.all()
        else:
            school_queryset = School.objects.filter(pk=request.user.school_id)
        form = ClassLevelForm(request.POST, school_queryset=school_queryset)
        if form.is_valid():
            form.save()
            dj_messages.success(request, f'Class level "{form.cleaned_data["name"]}" created!')
            if request.headers.get("HX-Request"):
                return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("classlevel-list")})
            return redirect("classlevel-list")
        template = "schools/_classlevel_form_content.html" if request.headers.get("HX-Request") else "schools/classlevel_form.html"
        return _htmx_render(request, template, {"class_level": None, "form": form})


class ClassLevelEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            class_level = get_object_or_404(ClassLevel, pk=pk)
            school_queryset = School.objects.all()
        else:
            class_level = get_object_or_404(ClassLevel, pk=pk, school=request.user.school)
            school_queryset = School.objects.filter(pk=request.user.school_id)
        form = ClassLevelForm(instance=class_level, school_queryset=school_queryset)
        template = "schools/_classlevel_form_content.html" if request.headers.get("HX-Request") else "schools/classlevel_form.html"
        return render(request, template, {"class_level": class_level, "form": form})

    def post(self, request, pk):
        if request.user.is_super_admin_role:
            class_level = get_object_or_404(ClassLevel, pk=pk)
            school_queryset = School.objects.all()
        else:
            class_level = get_object_or_404(ClassLevel, pk=pk, school=request.user.school)
            school_queryset = School.objects.filter(pk=request.user.school_id)
        form = ClassLevelForm(request.POST, instance=class_level, school_queryset=school_queryset)
        if form.is_valid():
            form.save()
            dj_messages.success(request, f'Class level "{class_level.name}" updated!')
            if request.headers.get("HX-Request"):
                return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("classlevel-list")})
            return redirect("classlevel-list")
        template = "schools/_classlevel_form_content.html" if request.headers.get("HX-Request") else "schools/classlevel_form.html"
        return _htmx_render(request, template, {"class_level": class_level, "form": form})


class ClassLevelDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            class_level = get_object_or_404(ClassLevel, pk=pk)
        else:
            class_level = get_object_or_404(ClassLevel, pk=pk, school=request.user.school)
        name = class_level.name
        class_level.delete()
        dj_messages.success(request, f'Class level "{name}" deleted.')
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers=_htmx_messages(request))
        return redirect("classlevel-list")
