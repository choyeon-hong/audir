from django import forms
from .models import Image, Project

class HandImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ['file']

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project']