from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from rest_framework import viewsets

from apps.accounts.forms import SchoolForm
from apps.accounts.permissions import IsAdminOrTeacher, SuperAdminRequiredMixin

from .models import School
from .serializers import SchoolSerializer


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

        return render(request, "schools/list.html", {"schools": page_obj, "page_obj": page_obj, "q": q})


class SchoolCreateView(SuperAdminRequiredMixin, View):
    def get(self, request):
        form = SchoolForm()
        return render(request, "schools/form.html", {"school": None, "form": form})

    def post(self, request):
        form = SchoolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "School created!")
            return redirect("school-list")
        return render(request, "schools/form.html", {"school": None, "form": form})


class SchoolEditView(SuperAdminRequiredMixin, View):
    def get(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        form = SchoolForm(instance=school)
        return render(request, "schools/form.html", {"school": school, "form": form})

    def post(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, "School updated!")
            return redirect("school-list")
        return render(request, "schools/form.html", {"school": school, "form": form})


class SchoolDeleteView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        school = get_object_or_404(School, pk=pk)
        school.delete()
        messages.success(request, "School deleted.")
        return redirect("school-list")


class SchoolViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolSerializer
    queryset = School.objects.all()
    search_fields = ["name"]
    permission_classes = [IsAdminOrTeacher]
