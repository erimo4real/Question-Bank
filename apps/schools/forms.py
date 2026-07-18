from django import forms

from apps.accounts.forms import SchoolForm as SchoolFormBase

# Re-export for backward compatibility; the canonical SchoolForm lives in accounts/forms.py
SchoolForm = SchoolFormBase
