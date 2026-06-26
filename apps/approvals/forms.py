from django import forms


class ApprovalDecisionForm(forms.Form):
    decision_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
