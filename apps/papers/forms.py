from django import forms

from apps.schools.models import ClassLevel
from apps.subjects.models import Subject

from .models import ExamPaper


SELECT_ATTRS = "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200"


class PaperForm(forms.ModelForm):
    title = forms.CharField(
        max_length=300,
        widget=forms.TextInput(
            attrs={
                "class": SELECT_ATTRS,
                "placeholder": "Paper title (e.g. First Term Mathematics Exam)",
            }
        ),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        empty_label="Select subject",
        widget=forms.Select(attrs={"class": SELECT_ATTRS}),
    )
    class_level = forms.ModelChoiceField(
        queryset=ClassLevel.objects.all(),
        required=False,
        empty_label="Select class level (optional)",
        widget=forms.Select(attrs={"class": SELECT_ATTRS}),
    )
    class_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": SELECT_ATTRS,
                "placeholder": "e.g. JSS 1A",
            }
        ),
        label="Class",
    )
    academic_session = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": SELECT_ATTRS,
                "placeholder": "e.g. 2024/2025",
            }
        ),
        label="Academic Session",
    )
    term = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": SELECT_ATTRS,
                "placeholder": "e.g. First Term",
            }
        ),
    )
    duration_minutes = forms.IntegerField(
        min_value=1,
        initial=60,
        widget=forms.NumberInput(
            attrs={
                "class": SELECT_ATTRS,
                "min": "1",
            }
        ),
        label="Duration (minutes)",
    )
    total_marks = forms.IntegerField(
        min_value=1,
        initial=100,
        widget=forms.NumberInput(
            attrs={
                "class": SELECT_ATTRS,
                "min": "1",
            }
        ),
    )
    instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200 resize-none",
                "rows": 4,
                "placeholder": "Exam instructions (optional)",
            }
        ),
    )
    status = forms.ChoiceField(
        choices=ExamPaper.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": SELECT_ATTRS}),
    )

    def __init__(self, *args, school=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school:
            self.fields["class_level"].queryset = ClassLevel.objects.filter(school=school)
        else:
            self.fields["class_level"].queryset = ClassLevel.objects.all()

    class Meta:
        model = ExamPaper
        fields = [
            "title", "subject", "class_level", "class_name", "academic_session", "term",
            "duration_minutes", "total_marks", "instructions", "status",
        ]

    def clean_title(self):
        title = self.cleaned_data.get("title")
        if title:
            title = title.strip()
        return title

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get("duration_minutes")
        if duration is not None and duration < 1:
            raise forms.ValidationError("Duration must be at least 1 minute.")
        return duration

    def clean_total_marks(self):
        marks = self.cleaned_data.get("total_marks")
        if marks is not None and marks < 1:
            raise forms.ValidationError("Total marks must be at least 1.")
        return marks
