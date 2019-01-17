from .models import ESS_Idea
from django import forms

class ModelUploadForm(forms.ModelForm):
    class Meta:
        model = ESS_Idea
        fields = ('bull_thesis_model','our_thesis_model','bear_thesis_model')