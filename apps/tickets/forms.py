from django import forms
from django.contrib.auth import get_user_model

from .models import Ticket, TicketMessage


class TicketAssignmentForm(forms.Form):
    assigned_to = forms.ModelChoiceField(queryset=None, required=False, empty_label="Unassigned")

    def __init__(self, *args, team, **kwargs):
        super().__init__(*args, **kwargs)
        user_ids = team.memberships.values_list("user_id", flat=True)
        self.fields["assigned_to"].queryset = get_user_model().objects.filter(id__in=user_ids)


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Ticket.Status.choices)


class AgentMessageForm(forms.ModelForm):
    class Meta:
        model = TicketMessage
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 4}),
        }


class SuggestionReplyForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 8}))
