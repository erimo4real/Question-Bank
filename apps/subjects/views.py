from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from rest_framework import viewsets

from apps.accounts.permissions import IsAdminOrTeacher
from apps.schools.models import ClassLevel, School

from .forms import SubjectForm, TopicCreateForm, TopicForm
from .models import Subject, Topic
from .serializers import SubjectDetailSerializer, SubjectSerializer, TopicSerializer


def generate_subject_code(name, school):
    base = name[:4].upper().strip()
    if not Subject.objects.filter(code=base, school=school).exists():
        return base
    for i in range(2, 100):
        candidate = f"{base}{i}"
        if not Subject.objects.filter(code=candidate, school=school).exists():
            return candidate
    return base


class SubjectListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all().prefetch_related("topics").order_by("name")
        elif request.user.is_school_admin_role:
            subjects = Subject.objects.filter(school=request.user.school).prefetch_related("topics").order_by("name")
        else:
            subjects = request.user.subjects.filter(school=request.user.school).prefetch_related("topics").order_by("name")

        q = request.GET.get("q", "")
        class_level_filter = request.GET.get("class_level", "")
        if q:
            subjects = subjects.filter(name__icontains=q)
        if class_level_filter:
            subjects = subjects.filter(class_level_id=class_level_filter)

        paginator = Paginator(subjects, 12)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        if request.user.is_super_admin_role:
            class_levels = ClassLevel.objects.all()
        else:
            class_levels = ClassLevel.objects.filter(school=request.user.school)

        return render(request, "subjects/list.html", {
            "subjects": page_obj, "page_obj": page_obj, "q": q,
            "class_level_filter": class_level_filter, "class_levels": class_levels,
        })


class SubjectCreateView(LoginRequiredMixin, View):
    def get(self, request):
        school = self._get_school(request)
        form = SubjectForm(school=school)
        class_levels = ClassLevel.objects.filter(school=school) if school else ClassLevel.objects.all()
        return render(request, "subjects/form.html", {"subject": None, "form": form, "class_levels": class_levels})

    def post(self, request):
        school = self._get_school(request)
        form = SubjectForm(request.POST, school=school)
        if form.is_valid():
            if not school:
                messages.error(request, "No school assigned to your account.")
                return render(request, "subjects/form.html", {"subject": None, "form": form})
            subject = form.save(commit=False)
            subject.school = school
            subject.created_by = request.user
            if not subject.code:
                subject.code = generate_subject_code(subject.name, school)
            subject.save()
            messages.success(request, f'Subject "{subject.name}" created.')
            return redirect("subject-list")
        class_levels = ClassLevel.objects.filter(school=school) if school else ClassLevel.objects.all()
        return render(request, "subjects/form.html", {"subject": None, "form": form, "class_levels": class_levels})

    def _get_school(self, request):
        if request.user.is_super_admin_role:
            school_id = request.POST.get("school") or request.GET.get("school")
            if school_id:
                return get_object_or_404(School, pk=school_id)
            return request.user.school
        return request.user.school


class SubjectEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            subject = get_object_or_404(Subject, pk=pk)
            school = subject.school
        else:
            subject = get_object_or_404(Subject, pk=pk, school=request.user.school)
            school = request.user.school
        form = SubjectForm(instance=subject, school=school)
        class_levels = ClassLevel.objects.filter(school=school) if school else ClassLevel.objects.all()
        return render(request, "subjects/form.html", {"subject": subject, "form": form, "class_levels": class_levels})

    def post(self, request, pk):
        if request.user.is_super_admin_role:
            subject = get_object_or_404(Subject, pk=pk)
            school = subject.school
        else:
            subject = get_object_or_404(Subject, pk=pk, school=request.user.school)
            school = request.user.school
        form = SubjectForm(request.POST, instance=subject, school=school)
        if form.is_valid():
            updated = form.save(commit=False)
            if not updated.code:
                updated.code = generate_subject_code(updated.name, updated.school)
            updated.save()
            messages.success(request, f'Subject "{updated.name}" updated.')
            return redirect("subject-list")
        class_levels = ClassLevel.objects.filter(school=school) if school else ClassLevel.objects.all()
        return render(request, "subjects/form.html", {"subject": subject, "form": form, "class_levels": class_levels})


class SubjectDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            subject = get_object_or_404(Subject, pk=pk)
        else:
            subject = get_object_or_404(Subject, pk=pk, school=request.user.school)
        name = subject.name
        subject.delete()
        messages.success(request, f'Subject "{name}" deleted.')
        return redirect("subject-list")


# ─── Topic Template Views (standalone + inline) ──────────────────

class TopicListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            topics = (
                Topic.objects.all()
                .select_related("subject", "class_level")
                .annotate(question_count=Count("questions"))
                .order_by("subject__name", "name")
            )
        else:
            topics = (
                Topic.objects.filter(subject__school=request.user.school)
                .select_related("subject", "class_level")
                .annotate(question_count=Count("questions"))
                .order_by("subject__name", "name")
            )
            if request.user.is_teacher_role:
                topics = topics.filter(subject__in=request.user.subjects.all())

        q = request.GET.get("q", "")
        subject_filter = request.GET.get("subject", "")
        class_level_filter = request.GET.get("class_level", "")

        if q:
            topics = topics.filter(name__icontains=q)
        if subject_filter:
            topics = topics.filter(subject_id=subject_filter)
        if class_level_filter:
            topics = topics.filter(class_level_id=class_level_filter)

        paginator = Paginator(topics, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        from apps.subjects.models import Subject
        if request.user.is_super_admin_role:
            all_subjects = Subject.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            all_subjects = Subject.objects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        else:
            all_subjects = request.user.subjects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)

        return render(request, "subjects/topic_list.html", {
            "topics": page_obj, "page_obj": page_obj, "q": q, "subject_filter": subject_filter,
            "class_level_filter": class_level_filter, "class_levels": class_levels,
            "all_subjects": all_subjects,
        })


class TopicCreateStandaloneView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all().order_by("name")
            class_levels = ClassLevel.objects.all()
        else:
            subjects = Subject.objects.filter(school=request.user.school).order_by("name")
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        form = TopicCreateForm()
        return render(request, "subjects/topic_form.html", {"topic": None, "subjects": subjects, "class_levels": class_levels, "form": form})

    def post(self, request):
        if request.user.is_super_admin_role:
            class_levels = ClassLevel.objects.all()
        else:
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        form = TopicCreateForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            if not request.user.is_super_admin_role:
                if subject.school != request.user.school:
                    messages.error(request, "Subject not found.")
                    return redirect("topic-create")
            topic = form.save()
            messages.success(request, f'Topic "{topic.name}" created under {subject.name}.')
            return redirect("topic-list")
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all().order_by("name")
        else:
            subjects = Subject.objects.filter(school=request.user.school).order_by("name")
        return render(request, "subjects/topic_form.html", {"topic": None, "subjects": subjects, "class_levels": class_levels, "form": form})


class TopicEditView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            topic = get_object_or_404(Topic, pk=pk)
            subjects = Subject.objects.all().order_by("name")
            class_levels = ClassLevel.objects.all()
        else:
            topic = get_object_or_404(Topic, pk=pk, subject__school=request.user.school)
            subjects = Subject.objects.filter(school=request.user.school).order_by("name")
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        form = TopicCreateForm(instance=topic)
        return render(request, "subjects/topic_form.html", {"topic": topic, "subjects": subjects, "class_levels": class_levels, "form": form})

    def post(self, request, pk):
        if request.user.is_super_admin_role:
            topic = get_object_or_404(Topic, pk=pk)
            class_levels = ClassLevel.objects.all()
        else:
            topic = get_object_or_404(Topic, pk=pk, subject__school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        form = TopicCreateForm(request.POST, instance=topic)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            if not request.user.is_super_admin_role and subject.school != request.user.school:
                messages.error(request, "Subject not found.")
                return redirect("topic-list")
            form.save()
            messages.success(request, f'Topic "{topic.name}" updated.')
            return redirect("topic-list")
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all().order_by("name")
        else:
            subjects = Subject.objects.filter(school=request.user.school).order_by("name")
        return render(request, "subjects/topic_form.html", {"topic": topic, "subjects": subjects, "class_levels": class_levels, "form": form})


class TopicDeleteStandaloneView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            topic = get_object_or_404(Topic, pk=pk)
        else:
            topic = get_object_or_404(Topic, pk=pk, subject__school=request.user.school)
        name = topic.name
        topic.delete()
        messages.success(request, f'Topic "{name}" deleted.')
        return redirect("topic-list")


class TopicCreateView(LoginRequiredMixin, View):
    def post(self, request, subject_pk):
        if request.user.is_super_admin_role:
            subject = get_object_or_404(Subject, pk=subject_pk)
        else:
            subject = get_object_or_404(Subject, pk=subject_pk, school=request.user.school)
        name = request.POST.get("name", "").strip()
        if name:
            Topic.objects.create(name=name, subject=subject)
            messages.success(request, f'Topic "{name}" added to {subject.name}.')
        return redirect("subject-list")


class TopicDeleteView(LoginRequiredMixin, View):
    def post(self, request, subject_pk, pk):
        if request.user.is_super_admin_role:
            topic = get_object_or_404(Topic.objects.filter(subject_id=subject_pk), pk=pk)
        else:
            topic = get_object_or_404(Topic.objects.filter(subject__school=request.user.school), pk=pk, subject_id=subject_pk)
        topic.delete()
        messages.success(request, "Topic deleted.")
        return redirect("subject-list")


class TopicsBySubjectView(LoginRequiredMixin, View):
    def get(self, request):
        subject_id = request.GET.get("subject_id")
        if not subject_id:
            return JsonResponse([], safe=False)
        if request.user.is_super_admin_role:
            topics = Topic.objects.filter(subject_id=subject_id).order_by("name")
        else:
            topics = Topic.objects.filter(subject_id=subject_id, subject__school=request.user.school).order_by("name")
        data = [{"id": str(t.id), "name": t.name} for t in topics]
        return JsonResponse(data, safe=False)


# ─── DRF API ViewSets ────────────────────────────────────────────

class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminOrTeacher]
    search_fields = ["name", "code"]
    filterset_fields = ["school"]

    queryset = Subject.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Subject.objects.none()
        user = self.request.user
        if user.is_super_admin_role:
            return Subject.objects.all()
        if user.school:
            return Subject.objects.filter(school=user.school)
        return Subject.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubjectDetailSerializer
        return SubjectSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsAdminOrTeacher]
    search_fields = ["name"]
    filterset_fields = ["subject"]

    queryset = Topic.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Topic.objects.none()
        user = self.request.user
        if user.is_super_admin_role:
            return Topic.objects.all()
        if user.school:
            return Topic.objects.filter(subject__school=user.school)
        return Topic.objects.none()
