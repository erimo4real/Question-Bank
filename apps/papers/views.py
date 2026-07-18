import random

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrTeacher
from apps.questions.models import Question
from apps.schools.models import ClassLevel
from apps.subjects.models import Subject

from .forms import PaperForm
from .models import ExamPaper, ExamPaperQuestion
from .serializers import (
    ExamPaperDetailSerializer,
    ExamPaperQuestionSerializer,
    ExamPaperSerializer,
)


# ─── Template Views ───────────────────────────────────────────────

class PaperListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.is_super_admin_role:
            papers = ExamPaper.objects.all().select_related("subject").order_by("-created_at")
            subjects = Subject.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            papers = ExamPaper.objects.filter(school=request.user.school).select_related("subject").order_by("-created_at")
            subjects = Subject.objects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)
        else:
            papers = ExamPaper.objects.filter(school=request.user.school).select_related("subject").order_by("-created_at")
            papers = papers.filter(subject__in=request.user.subjects.all())
            subjects = request.user.subjects.filter(school=request.user.school)
            class_levels = ClassLevel.objects.filter(school=request.user.school)

        q = request.GET.get("q", "")
        subject_filter = request.GET.get("subject", "")
        class_level_filter = request.GET.get("class_level", "")

        if q:
            papers = papers.filter(title__icontains=q)
        if subject_filter:
            papers = papers.filter(subject_id=subject_filter)
        if class_level_filter:
            papers = papers.filter(class_level_id=class_level_filter)

        paginator = Paginator(papers, 20)
        page = request.GET.get("page")
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return render(request, "papers/list.html", {
            "papers": page_obj, "page_obj": page_obj, "subjects": subjects,
            "class_levels": class_levels,
            "q": q, "subject_filter": subject_filter, "class_level_filter": class_level_filter,
        })


class PaperCreateView(LoginRequiredMixin, View):
    def _get_school(self, request):
        if request.user.is_super_admin_role:
            return request.user.school
        return request.user.school

    def _get_context(self, request):
        school = self._get_school(request)
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            subjects = Subject.objects.filter(school=school)
            class_levels = ClassLevel.objects.filter(school=school)
        else:
            subjects = request.user.subjects.filter(school=school)
            class_levels = ClassLevel.objects.filter(school=school)
        return {"subjects": subjects, "class_levels": class_levels}

    def get(self, request):
        school = self._get_school(request)
        form = PaperForm(school=school)
        ctx = self._get_context(request)
        return render(request, "papers/form.html", {"paper": None, "form": form, **ctx})

    def post(self, request):
        school = self._get_school(request)
        form = PaperForm(request.POST, school=school)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            if not request.user.is_super_admin_role and subject.school != request.user.school:
                messages.error(request, "Subject not found.")
                return redirect("paper-create")
            if request.user.is_teacher_role and subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-create")
            paper = form.save(commit=False)
            paper.school = subject.school
            paper.created_by = request.user
            paper.save()
            messages.success(request, f'Paper "{paper.title}" created. Now add questions!')
            return redirect("paper-detail", pk=paper.pk)
        ctx = self._get_context(request)
        return render(request, "papers/form.html", {"paper": None, "form": form, **ctx})


class PaperDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        pqs = paper.paper_questions.select_related("question__topic").order_by("order")
        if request.user.is_super_admin_role:
            available_questions = Question.objects.filter(
                school=paper.school,
                subject=paper.subject,
                status="published",
            ).exclude(id__in=pqs.values_list("question_id", flat=True))
            subjects = Subject.objects.all()
        else:
            available_questions = Question.objects.filter(
                school=request.user.school,
                subject=paper.subject,
                status="published",
            ).exclude(id__in=pqs.values_list("question_id", flat=True))
            if request.user.is_teacher_role:
                available_questions = available_questions.filter(subject__in=request.user.subjects.all())
            if request.user.is_school_admin_role:
                subjects = Subject.objects.filter(school=request.user.school)
            else:
                subjects = request.user.subjects.filter(school=request.user.school)
        return render(request, "papers/detail.html", {
            "paper": paper,
            "paper_questions": pqs,
            "available_questions": available_questions,
            "subjects": subjects,
        })


class PaperEditView(LoginRequiredMixin, View):
    def _get_school(self, request):
        if request.user.is_super_admin_role:
            return request.user.school
        return request.user.school

    def _get_context(self, request):
        school = self._get_school(request)
        if request.user.is_super_admin_role:
            subjects = Subject.objects.all()
            class_levels = ClassLevel.objects.all()
        elif request.user.is_school_admin_role:
            subjects = Subject.objects.filter(school=school)
            class_levels = ClassLevel.objects.filter(school=school)
        else:
            subjects = request.user.subjects.filter(school=school)
            class_levels = ClassLevel.objects.filter(school=school)
        return {"subjects": subjects, "class_levels": class_levels}

    def get(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        school = paper.school
        form = PaperForm(instance=paper, school=school)
        ctx = self._get_context(request)
        return render(request, "papers/form.html", {"paper": paper, "form": form, **ctx})

    def post(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
        school = paper.school
        form = PaperForm(request.POST, instance=paper, school=school)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            if not request.user.is_super_admin_role and subject.school != request.user.school:
                messages.error(request, "Subject not found.")
                return redirect("paper-list")
            if request.user.is_teacher_role and subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
            form.save()
            messages.success(request, "Paper updated!")
            return redirect("paper-detail", pk=paper.pk)
        ctx = self._get_context(request)
        return render(request, "papers/form.html", {"paper": paper, "form": form, **ctx})


class PaperDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        paper.delete()
        messages.success(request, "Paper deleted.")
        return redirect("paper-list")


class PaperAddQuestionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        question_id = request.POST.get("question_id")
        if request.user.is_super_admin_role:
            question = get_object_or_404(Question, pk=question_id)
        else:
            question = get_object_or_404(Question, pk=question_id, school=request.user.school)
        order = paper.paper_questions.count() + 1
        ExamPaperQuestion.objects.get_or_create(
            exam_paper=paper, question=question, defaults={"order": order}
        )
        question.times_used += 1
        question.save(update_fields=["times_used"])
        messages.success(request, "Question added to paper.")
        return redirect("paper-detail", pk=paper.pk)


class PaperBulkAddView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        ids = request.POST.getlist("question_ids")
        order = paper.paper_questions.count()
        added = 0
        for qid in ids:
            try:
                if request.user.is_super_admin_role:
                    question = Question.objects.get(id=qid)
                else:
                    question = Question.objects.get(id=qid, school=request.user.school)
                _, created = ExamPaperQuestion.objects.get_or_create(
                    exam_paper=paper, question=question, defaults={"order": order + 1}
                )
                if created:
                    order += 1
                    added += 1
                    question.times_used += 1
                    question.save(update_fields=["times_used"])
            except Question.DoesNotExist:
                continue
        messages.success(request, f"Added {added} questions to paper.")
        return redirect("paper-detail", pk=paper.pk)


class PaperRemoveQuestionView(LoginRequiredMixin, View):
    def post(self, request, paper_pk, pk):
        if request.user.is_super_admin_role:
            pq = get_object_or_404(ExamPaperQuestion, pk=pk)
        else:
            pq = get_object_or_404(ExamPaperQuestion, pk=pk, exam_paper__school=request.user.school)
            if request.user.is_teacher_role and pq.exam_paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        pq.delete()
        messages.success(request, "Question removed from paper.")
        return redirect("paper-detail", pk=paper_pk)


class PaperAutoFillView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        easy = int(request.POST.get("easy", 0))
        medium = int(request.POST.get("medium", 0))
        hard = int(request.POST.get("hard", 0))
        existing_ids = ExamPaperQuestion.objects.filter(exam_paper=paper).values_list("question_id", flat=True)
        order = paper.paper_questions.count()
        added = 0
        for diff, count in [("easy", easy), ("medium", medium), ("hard", hard)]:
            if count <= 0:
                continue
            qs = Question.objects.filter(
                school=paper.school, subject=paper.subject,
                status="published", difficulty=diff,
            ).exclude(id__in=existing_ids).order_by("times_used", "?")
            for q in qs[:count]:
                ExamPaperQuestion.objects.create(exam_paper=paper, question=q, order=order + 1)
                order += 1
                q.times_used += 1
                q.save(update_fields=["times_used"])
                added += 1
        messages.success(request, f"Auto-filled {added} questions.")
        return redirect("paper-detail", pk=paper.pk)


class PaperReorderView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        for pq in paper.paper_questions.all():
            new_order = request.POST.get(f"order_{pq.pk}")
            if new_order is not None:
                pq.order = int(new_order)
                pq.save(update_fields=["order"])
        messages.success(request, "Questions reordered.")
        return redirect("paper-detail", pk=paper.pk)


class PaperExportPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        from .export import generate_paper_pdf
        return generate_paper_pdf(paper)


class PaperExportDocxView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        from .export import generate_paper_docx
        return generate_paper_docx(paper)


class PaperPrintView(LoginRequiredMixin, View):
    def get(self, request, pk):
        if request.user.is_super_admin_role:
            paper = get_object_or_404(ExamPaper, pk=pk)
        else:
            paper = get_object_or_404(ExamPaper, pk=pk, school=request.user.school)
            if request.user.is_teacher_role and paper.subject not in request.user.subjects.all():
                messages.error(request, "You are not assigned to this subject.")
                return redirect("paper-list")
        from .export import generate_paper_html
        return generate_paper_html(paper)


# ─── DRF API ViewSets ────────────────────────────────────────────

class ExamPaperViewSet(viewsets.ModelViewSet):
    serializer_class = ExamPaperSerializer
    permission_classes = [IsAdminOrTeacher]
    search_fields = ["title", "class_name", "academic_session"]
    ordering_fields = ["created_at", "total_marks", "duration_minutes"]
    ordering = ["-created_at"]
    filterset_fields = ["subject", "status", "school", "class_name", "term"]

    queryset = ExamPaper.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return ExamPaper.objects.none()
        user = self.request.user
        if user.is_super_admin_role:
            return ExamPaper.objects.all()
        if user.school:
            return ExamPaper.objects.filter(school=user.school)
        return ExamPaper.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ExamPaperDetailSerializer
        return ExamPaperSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, school=self.request.user.school)

    @action(detail=True, methods=["post"], url_path="add-question")
    def add_question(self, request, pk=None):
        paper = self.get_object()
        question_id = request.data.get("question_id")
        order = request.data.get("order", paper.paper_questions.count() + 1)
        marks_override = request.data.get("marks_override")
        try:
            question = Question.objects.get(id=question_id, school=paper.school)
        except Question.DoesNotExist:
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
        pq, created = ExamPaperQuestion.objects.get_or_create(
            exam_paper=paper, question=question,
            defaults={"order": order, "marks_override": marks_override},
        )
        if not created:
            return Response({"error": "Already in paper"}, status=status.HTTP_400_BAD_REQUEST)
        question.times_used += 1
        question.save(update_fields=["times_used"])
        return Response(ExamPaperQuestionSerializer(pq).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="add-questions-bulk")
    def add_questions_bulk(self, request, pk=None):
        paper = self.get_object()
        question_ids = request.data.get("question_ids", [])
        added = 0
        order = paper.paper_questions.count()
        for qid in question_ids:
            try:
                q = Question.objects.get(id=qid, school=paper.school)
                _, created = ExamPaperQuestion.objects.get_or_create(
                    exam_paper=paper, question=q, defaults={"order": order + 1}
                )
                if created:
                    order += 1
                    added += 1
                    q.times_used += 1
                    q.save(update_fields=["times_used"])
            except Question.DoesNotExist:
                continue
        return Response({"added": added})

    @action(detail=True, methods=["post"], url_path="remove-question")
    def remove_question(self, request, pk=None):
        paper = self.get_object()
        question_id = request.data.get("question_id")
        deleted, _ = ExamPaperQuestion.objects.filter(exam_paper=paper, question_id=question_id).delete()
        if deleted:
            return Response({"message": "Removed"})
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"], url_path="reorder")
    def reorder(self, request, pk=None):
        paper = self.get_object()
        for item in request.data.get("orders", []):
            ExamPaperQuestion.objects.filter(exam_paper=paper, question_id=item["question_id"]).update(order=item["order"])
        return Response({"message": "Reordered"})

    @action(detail=True, methods=["get"], url_path="random-questions")
    def random_questions(self, request, pk=None):
        paper = self.get_object()
        count = int(request.query_params.get("count", 10))
        difficulty = request.query_params.get("difficulty")
        topic = request.query_params.get("topic")
        qs = Question.objects.filter(school=paper.school, subject=paper.subject, status="published")
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if topic:
            qs = qs.filter(topic_id=topic)
        existing = ExamPaperQuestion.objects.filter(exam_paper=paper).values_list("question_id", flat=True)
        qs = qs.exclude(id__in=existing)
        questions = list(qs.order_by("?")[:count])
        return Response([{"id": str(q.id), "question_text": q.question_text, "question_type": q.question_type, "difficulty": q.difficulty, "marks": q.marks} for q in questions])

    @action(detail=True, methods=["post"], url_path="auto-fill")
    def auto_fill(self, request, pk=None):
        paper = self.get_object()
        easy_count = int(request.data.get("easy", 0))
        medium_count = int(request.data.get("medium", 0))
        hard_count = int(request.data.get("hard", 0))
        added = 0
        order = paper.paper_questions.count()
        existing = ExamPaperQuestion.objects.filter(exam_paper=paper).values_list("question_id", flat=True)
        for diff, count in [("easy", easy_count), ("medium", medium_count), ("hard", hard_count)]:
            if count <= 0:
                continue
            qs = Question.objects.filter(school=paper.school, subject=paper.subject, status="published", difficulty=diff).exclude(id__in=existing).order_by("times_used", "?")
            for q in qs[:count]:
                ExamPaperQuestion.objects.create(exam_paper=paper, question=q, order=order + 1)
                order += 1
                q.times_used += 1
                q.save(update_fields=["times_used"])
                added += 1
        return Response({"added": added})

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        paper = self.get_object()
        pqs = paper.paper_questions.select_related("question")
        type_bd = {}
        diff_bd = {}
        total = 0
        for pq in pqs:
            q = pq.question
            m = pq.marks_override if pq.marks_override is not None else q.marks
            total += m
            type_bd[q.question_type] = type_bd.get(q.question_type, 0) + 1
            diff_bd[q.difficulty] = diff_bd.get(q.difficulty, 0) + 1
        return Response({"title": paper.title, "question_count": pqs.count(), "total_marks": total, "type_breakdown": type_bd, "difficulty_breakdown": diff_bd})

    @action(detail=True, methods=["get"], url_path="export-pdf", url_name="export-pdf")
    def export_pdf(self, request, pk=None):
        from .export import generate_paper_pdf
        return generate_paper_pdf(self.get_object())

    @action(detail=True, methods=["get"], url_path="export-docx", url_name="export-docx")
    def export_docx(self, request, pk=None):
        from .export import generate_paper_docx
        return generate_paper_docx(self.get_object())

    @action(detail=True, methods=["get"], url_path="print-view", url_name="print-view")
    def print_view(self, request, pk=None):
        from .export import generate_paper_html
        return generate_paper_html(self.get_object())
