from django import forms

from .models import SuggestionFeedback


class SuggestionFeedbackForm(forms.ModelForm):
    class Meta:
        model = SuggestionFeedback
        fields = ["rating", "failure_tag", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 3}),
        }
