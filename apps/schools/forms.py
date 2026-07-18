from django import forms

from apps.accounts.forms import SchoolForm as SchoolFormBase

from .models import ClassLevel

# Re-export for backward compatibility; the canonical SchoolForm lives in accounts/forms.py
SchoolForm = SchoolFormBase


class ClassLevelForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "placeholder": "e.g. JSS 1, SS 2",
            }
        ),
    )
    order = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
                "min": "0",
            }
        ),
    )
    school = forms.ModelChoiceField(
        queryset=None,
        empty_label="Select school",
        widget=forms.Select(
            attrs={
                "class": "block w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 focus:border-primary-500 focus:bg-white focus:ring-2 focus:ring-primary-500/20 transition-all duration-200",
            }
        ),
    )

    def __init__(self, *args, school_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if school_queryset is not None:
            self.fields["school"].queryset = school_queryset
        else:
            from .models import School
            self.fields["school"].queryset = School.objects.all()

    class Meta:
        model = ClassLevel
        fields = ["name", "order", "school"]

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if name:
            name = name.strip()
        return name

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        school = cleaned_data.get("school")
        if name and school:
            qs = ClassLevel.objects.filter(name__iexact=name, school=school)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({"name": "A class level with this name already exists in this school."})
        return cleaned_data
