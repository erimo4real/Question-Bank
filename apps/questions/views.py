import csv
import io
import json

from django.contrib import messages as dj_messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrTeacher
from apps.schools.models import ClassLevel

from .models import Question
from .forms import QuestionForm
from .serializers import (
    BulkDeleteSerializer,
    BulkStatusSerializer,
    QuestionPreviewSerializer,
    QuestionSerializer,
)


def _htmx_messages(request):
    msgs = [{"text": str(m), "tag": m.tags} for m in dj_messages.get_messages(request)]
    return {"X-Messages": json.dumps(msgs)}


# ─── Template Views ───────────────────────────────────────────────

class QuestionListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            qs = Question.objects.all().select_related("subject", "topic").order_by("-created_at")
        elif request.user.is_school_admin_role:
            qs = Question.objects.filter(school=request.user.school).select_related("subject", "topic").order_by("-created_at")
        else:
            qs = Question.objects.filter(school=request.user.school).select_related("subject", "topic").order_by("-created_at")
            qs = qs.filter(subject__in=request.user.subjects.all())

        # Filters
        q = request.GET.get("q", "")
        q_type = request.GET.get("type", "")
        difficulty = request.GET.get("difficulty", "")
        status_filter = request.GET.get("status", "")
        subject = request.GET.get("subject", "")
        class_level_filter = request.GET.get("class_level", "")

        if q:
            search_query = SearchQuery(q)
            qs = qs.filter(
                Q(search_vector=search_query)
                | Q(question_text__icontains=q)
                | Q(explanation__icontains=q)
            ).annotate(
                rank=SearchRank("search_vector", search_query)
            ).order_by("-rank")
        if q_type:
            qs = qs.filter(question_type=q_type)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if subject:
            qs = qs.filter(subject_id=subject)
        if class_level_filter:
            qs = qs.filter(class_level_id=class_level_filter)

        from apps.subjects.models import Subject
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            subjects = Subject.objects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        else:
            subjects = request.user.subjects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)

        published_count = qs.filter(status="published").count()
        draft_count = qs.filter(status="draft").count()

        paginator_obj = Paginator(qs, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator_obj.page(page)
        except PageNotAnInteger:
            page_obj = paginator_obj.page(1)
        except EmptyPage:
            page_obj = paginator_obj.page(paginator_obj.num_pages)

        ctx = {
            "questions": page_obj,
            "page_obj": page_obj,
            "subjects": subjects,
            "class_levels": class_levels,
            "filters": {"q": q, "type": q_type, "difficulty": difficulty, "status": status_filter, "subject": subject, "class_level": class_level_filter},
            "type_choices": Question.TYPE_CHOICES,
            "difficulty_choices": Question.DIFFICULTY_CHOICES,
            "status_choices": Question.STATUS_CHOICES,
            "published_count": published_count,
            "draft_count": draft_count,
            "paginator": paginator_obj,
        }
        template = "questions/_list_content.html" if request.headers.get("HX-Request") else "questions/list.html"
        return render(request, template, ctx)


class QuestionCreateView(LoginRequiredMixin, View):
    def _get_context(self, request):
        from apps.subjects.models import Subject, Topic
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all()
            topics = Topic.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            subjects = Subject.objects.filter(school=request.user.school)
            topics = Topic.objects.filter(subject__school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        else:
            subjects = request.user.subjects.filter(school=request.user.school)
            topics = Topic.objects.filter(subject__school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        return {"subjects": subjects, "topics": topics, "class_levels": class_levels}

    def _get_school(self, request):
        if request.user.is_super_admin_role:
            return request.POST.get("school_id") or (request.user.school.pk if request.user.school else None)
        return request.user.school

    def get(self, request):
        ctx = self._get_context(request)
        school = self._get_school(request)
        form = QuestionForm(school=school)
        template = "questions/_form_content.html" if request.headers.get("HX-Request") else "questions/form.html"
        return render(request, template, {
            "question": None, "form": form, **ctx,
            "type_choices": Question.TYPE_CHOICES,
            "difficulty_choices": Question.DIFFICULTY_CHOICES,
        })

    def post(self, request):
        school = self._get_school(request)
        form = QuestionForm(request.POST, request.FILES, school=school)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            if not request.user.is_super_admin_role and subject.school != request.user.school:
                dj_messages.error(request, "Subject not found.")
                if request.headers.get("HX-Request"):
                    return HttpResponse("", headers=_htmx_messages(request))
                return redirect("question-create")
            if request.user.is_teacher_role and subject not in request.user.subjects.all():
                dj_messages.error(request, "You are not assigned to this subject.")
                if request.headers.get("HX-Request"):
                    return HttpResponse("", headers=_htmx_messages(request))
                return redirect("question-create")
            options = [o.strip() for o in request.POST.getlist("options") if o.strip()]
            correct_answer = [a.strip() for a in request.POST.getlist("correct_answer") if a.strip()]
            tags = [t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()]
            q = form.save(commit=False)
            q.options = options
            q.correct_answer = correct_answer
            q.tags = tags
            q.school = subject.school
            q.created_by = request.user
            q.save()
            dj_messages.success(request, "Question created successfully!")
            if request.headers.get("HX-Request"):
                return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("question-edit", args=[q.pk])})
            return redirect("question-edit", pk=q.pk)
        ctx = self._get_context(request)
        template = "questions/_form_content.html" if request.headers.get("HX-Request") else "questions/form.html"
        return render(request, template, {
            "question": None, "form": form, **ctx,
            "type_choices": Question.TYPE_CHOICES,
            "difficulty_choices": Question.DIFFICULTY_CHOICES,
        }, headers=_htmx_messages(request))


class QuestionEditView(LoginRequiredMixin, View):
    def _get_context(self, request):
        from apps.subjects.models import Subject, Topic
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all()
            topics = Topic.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            subjects = Subject.objects.filter(school=request.user.school)
            topics = Topic.objects.filter(subject__school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        else:
            subjects = request.user.subjects.filter(school=request.user.school)
            topics = Topic.objects.filter(subject__school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        return {"subjects": subjects, "topics": topics, "class_levels": class_levels}

    def _get_school(self, request):
        if request.user.is_super_admin_role:
            return request.POST.get("school_id") or (request.user.school.pk if request.user.school else None)
        return request.user.school

    def get(self, request, pk):
        if request.user.is_super_admin_role:
            question = get_object_or_404(Question, pk=pk)
        else:
            question = get_object_or_404(Question, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and question.subject not in request.user.subjects.all():
                dj_messages.error(request, "You are not assigned to this subject.")
                return redirect("question-list")
        school = self._get_school(request)
        form = QuestionForm(instance=question, initial={"tags_input": ", ".join(question.tags or [])}, school=school)
        ctx = self._get_context(request)
        template = "questions/_form_content.html" if request.headers.get("HX-Request") else "questions/form.html"
        return render(request, template, {
            "question": question, "form": form, **ctx,
            "type_choices": Question.TYPE_CHOICES,
            "difficulty_choices": Question.DIFFICULTY_CHOICES,
        })

    def post(self, request, pk):
        if request.user.is_super_admin_role:
            question = get_object_or_404(Question, pk=pk)
        else:
            question = get_object_or_404(Question, pk=pk, school=request.user.school)
        school = self._get_school(request)
        form = QuestionForm(request.POST, request.FILES, instance=question, school=school)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            if not request.user.is_super_admin_role and subject.school != request.user.school:
                dj_messages.error(request, "Subject not found.")
                if request.headers.get("HX-Request"):
                    return HttpResponse("", headers=_htmx_messages(request))
                return redirect("question-list")
            if request.user.is_teacher_role and subject not in request.user.subjects.all():
                dj_messages.error(request, "You are not assigned to this subject.")
                if request.headers.get("HX-Request"):
                    return HttpResponse("", headers=_htmx_messages(request))
                return redirect("question-list")
            options = [o.strip() for o in request.POST.getlist("options") if o.strip()]
            correct_answer = [a.strip() for a in request.POST.getlist("correct_answer") if a.strip()]
            tags = [t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()]
            q = form.save(commit=False)
            q.options = options
            q.correct_answer = correct_answer
            q.tags = tags
            q.save()
            dj_messages.success(request, "Question updated!")
            if request.headers.get("HX-Request"):
                return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("question-edit", args=[question.pk])})
            return redirect("question-edit", pk=question.pk)
        ctx = self._get_context(request)
        template = "questions/_form_content.html" if request.headers.get("HX-Request") else "questions/form.html"
        return render(request, template, {
            "question": question, "form": form, **ctx,
            "type_choices": Question.TYPE_CHOICES,
            "difficulty_choices": Question.DIFFICULTY_CHOICES,
        }, headers=_htmx_messages(request))


class QuestionDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            question = get_object_or_404(Question, pk=pk)
        else:
            question = get_object_or_404(Question, pk=pk, school=request.user.school)
        question.delete()
        dj_messages.success(request, "Question deleted.")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers=_htmx_messages(request))
        return redirect("question-list")


class QuestionPreviewView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            question = get_object_or_404(Question, pk=pk)
        else:
            question = get_object_or_404(Question, pk=pk, school=request.user.school)
        return render(request, "questions/preview.html", {"question": question})


class QuestionImportView(LoginRequiredMixin, View):
    def get(self, request):
        template = "questions/_import_content.html" if request.headers.get("HX-Request") else "questions/import.html"
        return render(request, template)

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            dj_messages.error(request, "No file provided.")
            if request.headers.get("HX-Request"):
                return render(request, "questions/_import_content.html", headers=_htmx_messages(request))
            return redirect("question-import")

        try:
            decoded = file.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
        except Exception:
            dj_messages.error(request, "Invalid CSV file.")
            if request.headers.get("HX-Request"):
                return render(request, "questions/_import_content.html", headers=_htmx_messages(request))
            return redirect("question-import")

        created = 0
        errors = []
        for i, row in enumerate(reader, start=2):
            try:
                q_text = row.get("question_text", "")
                q_type = row.get("question_type", "mcq")
                if not q_text:
                    errors.append(f"Row {i}: missing question_text")
                    continue

                options_raw = row.get("options", "")
                options = [o.strip() for o in options_raw.split("|") if o.strip()] if options_raw else []
                answer_raw = row.get("correct_answer", "")
                correct_answer = [a.strip() for a in answer_raw.split("|") if a.strip()] if answer_raw else []
                tags_raw = row.get("tags", "")
                tags = [t.strip() for t in tags_raw.split("|") if t.strip()] if tags_raw else []

                subject = None
                subject_id = row.get("subject", "")
                if subject_id:
                    from apps.subjects.models import Subject
                    if request.user.is_super_admin_role:
                        subject = Subject.objects.get(pk=subject_id)
                    else:
                        subject = Subject.objects.get(pk=subject_id, school=request.user.school)
                if not subject:
                    dj_messages.error(request, f"Row {i}: subject not found. Import stopped.")
                    break

                Question.objects.create(
                    question_text=q_text,
                    question_type=q_type,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=row.get("explanation", ""),
                    marks=int(row.get("marks", 1)),
                    difficulty=row.get("difficulty", "medium"),
                    subject=subject,
                    tags=tags,
                    status=row.get("status", "draft"),
                    school=subject.school,
                    created_by=request.user,
                )
                created += 1
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        if created:
            dj_messages.success(request, f"Imported {created} questions.")
        if errors:
            dj_messages.warning(request, f"{len(errors)} errors: {'; '.join(errors[:5])}")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers={**_htmx_messages(request), "HX-Redirect": reverse("question-list")})
        return redirect("question-list")


class QuestionBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist("ids")
        if request.user.is_super_admin_role:
            deleted, _ = Question.objects.filter(id__in=ids).delete()
        else:
            deleted, _ = Question.objects.filter(id__in=ids, school=request.user.school).delete()
        dj_messages.success(request, f"Deleted {deleted} questions.")
        if request.headers.get("HX-Request"):
            return self._render_list(request)
        return redirect("question-list")

    def _render_list(self, request):
        """Re-render the questions list partial."""
        from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
        from apps.subjects.models import Subject
        if request.user.is_super_admin_role:
            qs = Question.objects.all().select_related("subject", "topic").order_by("-created_at")
            subjects = Subject.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            qs = Question.objects.filter(school=request.user.school).select_related("subject", "topic").order_by("-created_at")
            subjects = Subject.objects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        else:
            qs = Question.objects.filter(school=request.user.school).select_related("subject", "topic").order_by("-created_at")
            qs = qs.filter(subject__in=request.user.subjects.all())
            subjects = request.user.subjects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        q = request.GET.get("q", "")
        q_type = request.GET.get("type", "")
        difficulty = request.GET.get("difficulty", "")
        status_filter = request.GET.get("status", "")
        subject = request.GET.get("subject", "")
        class_level_filter = request.GET.get("class_level", "")
        if q:
            search_query = SearchQuery(q)
            qs = qs.filter(Q(search_vector=search_query) | Q(question_text__icontains=q) | Q(explanation__icontains=q)).annotate(rank=SearchRank("search_vector", search_query)).order_by("-rank")
        if q_type:
            qs = qs.filter(question_type=q_type)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if subject:
            qs = qs.filter(subject_id=subject)
        if class_level_filter:
            qs = qs.filter(class_level_id=class_level_filter)
        published_count = qs.filter(status="published").count()
        draft_count = qs.filter(status="draft").count()
        paginator_obj = Paginator(qs, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator_obj.page(page)
        except PageNotAnInteger:
            page_obj = paginator_obj.page(1)
        except EmptyPage:
            page_obj = paginator_obj.page(paginator_obj.num_pages)
        ctx = {
            "questions": page_obj, "page_obj": page_obj, "subjects": subjects,
            "class_levels": class_levels,
            "filters": {"q": q, "type": q_type, "difficulty": difficulty, "status": status_filter, "subject": subject, "class_level": class_level_filter},
            "type_choices": Question.TYPE_CHOICES,
            "difficulty_choices": Question.DIFFICULTY_CHOICES,
            "status_choices": Question.STATUS_CHOICES,
            "published_count": published_count, "draft_count": draft_count, "paginator": paginator_obj,
        }
        return render(request, "questions/_list_content.html", ctx, headers=_htmx_messages(request))


class QuestionBulkStatusView(LoginRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist("ids")
        new_status = request.POST.get("new_status", "published")
        valid_statuses = [choice[0] for choice in Question.STATUS_CHOICES]
        if new_status not in valid_statuses:
            dj_messages.error(request, f"Invalid status: {new_status}")
            if request.headers.get("HX-Request"):
                return QuestionBulkDeleteView()._render_list(request)
            return redirect("question-list")
        if request.user.is_super_admin_role:
            updated = Question.objects.filter(id__in=ids).update(status=new_status)
        else:
            updated = Question.objects.filter(id__in=ids, school=request.user.school).update(status=new_status)
        dj_messages.success(request, f"Updated {updated} questions to {new_status}.")
        if request.headers.get("HX-Request"):
            return QuestionBulkDeleteView()._render_list(request)
        return redirect("question-list")


# ─── DRF API ViewSets ────────────────────────────────────────────

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAdminOrTeacher]
    search_fields = ["question_text", "tags", "explanation"]
    ordering_fields = ["created_at", "updated_at", "marks", "difficulty", "times_used"]
    ordering = ["-created_at"]
    filterset_fields = ["question_type", "difficulty", "status", "subject", "topic", "school"]

    queryset = Question.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Question.objects.none()
        user = self.request.user
        if user.is_super_admin_role:
            qs = Question.objects.all()
        elif user.school:
            qs = Question.objects.filter(school=user.school)
        else:
            return Question.objects.none()
        created_by = self.request.query_params.get("created_by")
        tag = self.request.query_params.get("tag")
        min_marks = self.request.query_params.get("min_marks")
        max_marks = self.request.query_params.get("max_marks")
        if created_by:
            qs = qs.filter(created_by_id=created_by)
        if tag:
            qs = qs.filter(tags__contains=[tag])
        if min_marks:
            try:
                qs = qs.filter(marks__gte=int(min_marks))
            except (ValueError, TypeError):
                pass
        if max_marks:
            try:
                qs = qs.filter(marks__lte=int(max_marks))
            except (ValueError, TypeError):
                pass
        return qs

    def get_serializer_class(self):
        if self.action == "preview":
            return QuestionPreviewSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        question = self.get_object()
        serializer = QuestionPreviewSerializer(question)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        serializer = BulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        deleted_count, _ = Question.objects.filter(id__in=ids, school=request.user.school).delete()
        return Response({"deleted": deleted_count})

    @action(detail=False, methods=["post"], url_path="bulk-status")
    def bulk_status(self, request):
        serializer = BulkStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        new_status = serializer.validated_data["status"]
        updated_count = Question.objects.filter(id__in=ids, school=request.user.school).update(status=new_status)
        return Response({"updated": updated_count})

    @action(detail=False, methods=["get"], url_path="export")
    def export_csv(self, request):
        if not getattr(self, "swagger_fake_view", False):
            qs = self.get_queryset()
        else:
            qs = Question.objects.none()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=questions_export.csv"
        writer = csv.writer(response)
        writer.writerow(["ID", "Question", "Type", "Options", "Correct Answer", "Explanation", "Marks", "Difficulty", "Subject", "Topic", "Tags", "Status"])
        for q in qs:
            writer.writerow([str(q.id), q.question_text, q.question_type, "|".join(str(o) for o in q.options), "|".join(str(a) for a in q.correct_answer), q.explanation, q.marks, q.difficulty, str(q.subject_id), str(q.topic_id) if q.topic_id else "", "|".join(q.tags) if q.tags else "", q.status])
        return response

    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file"}, status=400)
        decoded = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        created = 0
        errors = []
        for i, row in enumerate(reader, start=2):
            try:
                q_text = row.get("question_text", "")
                if not q_text:
                    errors.append(f"Row {i}: missing question_text")
                    continue
                options = [o.strip() for o in row.get("options", "").split("|") if o.strip()]
                correct_answer = [a.strip() for a in row.get("correct_answer", "").split("|") if a.strip()]
                tags = [t.strip() for t in row.get("tags", "").split("|") if t.strip()]
                Question.objects.create(question_text=q_text, question_type=row.get("question_type", "mcq"), options=options, correct_answer=correct_answer, explanation=row.get("explanation", ""), marks=int(row.get("marks", 1)), difficulty=row.get("difficulty", "medium"), subject_id=row.get("subject"), tags=tags, status=row.get("status", "draft"), school=request.user.school, created_by=request.user)
                created += 1
            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")
        return Response({"created": created, "errors": errors})

    @action(detail=False, methods=["get"], url_path="check-duplicate")
    def check_duplicate(self, request):
        text = request.query_params.get("text", "")
        subject = request.query_params.get("subject")
        if not text:
            return Response({"error": "Provide 'text'"}, status=400)
        qs = self.get_queryset().filter(question_text__icontains=text)
        if subject:
            qs = qs.filter(subject_id=subject)
        return Response({"count": qs.count(), "duplicates": QuestionSerializer(qs[:10], many=True).data})
