from django import forms

from apps.subjects.models import Subject, Topic

from .models import Question


class QuestionForm(forms.ModelForm):
    question_text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200 resize-none",
                "rows": 4,
                "placeholder": "Enter the question text",
            }
        ),
    )
    question_type = forms.ChoiceField(
        choices=Question.TYPE_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )
    explanation = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200 resize-none",
                "rows": 3,
                "placeholder": "Explanation (optional)",
            }
        ),
    )
    marks = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "min": "1",
            }
        ),
    )
    difficulty = forms.ChoiceField(
        choices=Question.DIFFICULTY_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        empty_label="Select subject",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )
    topic = forms.ModelChoiceField(
        queryset=Topic.objects.all(),
        required=False,
        empty_label="Select topic (optional)",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "placeholder": "Comma-separated tags (e.g. algebra, linear)",
            }
        ),
        label="Tags",
    )
    status = forms.ChoiceField(
        choices=Question.STATUS_CHOICES,
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )

    class Meta:
        model = Question
        fields = [
            "question_text", "question_type", "explanation", "marks",
            "difficulty", "subject", "topic", "status", "image",
        ]

    def clean_question_text(self):
        text = self.cleaned_data.get("question_text")
        if text:
            text = text.strip()
        return text

    def clean_marks(self):
        marks = self.cleaned_data.get("marks")
        if marks is not None and marks < 1:
            raise forms.ValidationError("Marks must be at least 1.")
        return marks


class QuestionImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "class": "block w-full text-sm text-gray-500 file:mr-3 file:rounded-xl file:border-0 file:bg-primary-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-primary-700 hover:file:bg-primary-100",
                "accept": ".csv",
            }
        ),
        help_text="Upload a CSV file with columns: question_text, question_type, options, correct_answer, explanation, marks, difficulty, topic, tags",
    )
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        empty_label="Select subject",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file:
            if not file.name.endswith(".csv"):
                raise forms.ValidationError("Only CSV files are allowed.")
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError("File must be less than 5MB.")
        return file
