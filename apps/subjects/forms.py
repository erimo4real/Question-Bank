from django import forms

from .models import Subject, Topic


class SubjectForm(forms.ModelForm):
    name = forms.CharField(
        max_length=300,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "placeholder": "Subject name",
            }
        ),
    )
    code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "placeholder": "e.g. MATH101",
            }
        ),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200 resize-none",
                "rows": 3,
                "placeholder": "Brief description of the subject",
            }
        ),
    )

    class Meta:
        model = Subject
        fields = ["name", "code", "description"]

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
        return name

    def clean_code(self):
        code = self.cleaned_data.get("code")
        if code:
            code = code.strip().upper()
        return code


class TopicForm(forms.ModelForm):
    name = forms.CharField(
        max_length=300,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "placeholder": "Topic name",
            }
        ),
    )

    class Meta:
        model = Topic
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
        return name


class TopicCreateForm(forms.ModelForm):
    name = forms.CharField(
        max_length=300,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "placeholder": "Topic name",
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

    class Meta:
        model = Topic
        fields = ["name", "subject"]

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
        return name
