import json
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone
from django.views import View

from apps.papers.models import ExamPaper
from apps.questions.models import Question
from apps.schools.models import School
from apps.subjects.models import Subject, Topic


class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        ctx = {}

        if user.is_super_admin_role:
            questions = Question.objects.all()
            papers = ExamPaper.objects.all()
            subjects = Subject.objects.all()
            total_schools = School.objects.count()
            ctx["total_schools"] = total_schools
        elif user.school:
            questions = Question.objects.filter(school=user.school)
            papers = ExamPaper.objects.filter(school=user.school)
            subjects = Subject.objects.filter(school=user.school)
        else:
            return render(request, "dashboard/index.html", ctx)

        if user.is_teacher_role:
            questions = questions.filter(subject__in=user.subjects.all())
            papers = papers.filter(subject__in=user.subjects.all())
            subjects = subjects.filter(assigned_teachers=user)

        six_months_ago = timezone.now() - timedelta(days=180)

        type_bd = dict(
            questions.values_list("question_type")
            .annotate(c=Count("id"))
            .values_list("question_type", "c")
        )
        diff_bd = dict(
            questions.values_list("difficulty")
            .annotate(c=Count("id"))
            .values_list("difficulty", "c")
        )
        subject_bd = list(
            questions.values("subject__name")
            .annotate(c=Count("id"))
            .order_by("-c")[:8]
        )
        monthly_q = list(
            questions.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month").annotate(c=Count("id")).order_by("month")
        )
        monthly_p = list(
            papers.filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth("created_at"))
            .values("month").annotate(c=Count("id")).order_by("month")
        )

        ctx.update({
            "total_questions": questions.count(),
            "published_questions": questions.filter(status="published").count(),
            "draft_questions": questions.filter(status="draft").count(),
            "total_papers": papers.count(),
            "draft_papers": papers.filter(status="draft").count(),
            "finalized_papers": papers.filter(status="finalized").count(),
            "total_subjects": subjects.count(),
            "total_topics": Topic.objects.filter(subject__in=subjects).count(),
            "type_breakdown": type_bd,
            "difficulty_breakdown": diff_bd,
            "recent_questions": questions.order_by("-created_at")[:10],
            "recent_papers": papers.order_by("-created_at")[:5],
            "chart_data": json.dumps({
                "monthly_labels": [item["month"].strftime("%b %Y") for item in monthly_q],
                "monthly_questions": [item["c"] for item in monthly_q],
                "monthly_papers": [item["c"] for item in monthly_p],
                "status": {
                    "published": questions.filter(status="published").count(),
                    "draft": questions.filter(status="draft").count(),
                    "archived": questions.filter(status="archived").count(),
                },
                "type": {"labels": list(type_bd.keys()), "data": list(type_bd.values())},
                "difficulty": {"labels": [k.replace("_", " ").title() for k in diff_bd.keys()], "data": list(diff_bd.values())},
                "subject": {"labels": [s["subject__name"] for s in subject_bd], "data": [s["c"] for s in subject_bd]},
            }),
        })
        return render(request, "dashboard/index.html", ctx)
