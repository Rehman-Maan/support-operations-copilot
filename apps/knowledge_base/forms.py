from django import forms

from .models import KnowledgeDocument, Macro


class KnowledgeDocumentForm(forms.ModelForm):
    class Meta:
        model = KnowledgeDocument
        fields = ["title", "document_type", "file"]


class MacroForm(forms.ModelForm):
    class Meta:
        model = Macro
        fields = ["name", "intent", "body", "active"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 5}),
        }
