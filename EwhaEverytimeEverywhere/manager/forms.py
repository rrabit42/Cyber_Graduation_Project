from django import forms
from .models import certPage


class certForm(forms.ModelForm):
    class Meta:
        model = certPage
        exclude = ('created_at', )

