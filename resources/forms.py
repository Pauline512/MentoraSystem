from django import forms
from .models import Resource

class ResourceUploadForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'description', 'file', 'link']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
