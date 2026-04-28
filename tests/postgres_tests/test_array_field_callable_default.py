import pytest
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.forms import ModelForm
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that ArrayField with callable default doesn't create hidden initial inputs."""
    
    # Create a model with ArrayField having callable default
    class TestModel(models.Model):
        array_field = ArrayField(
            models.CharField(max_length=42),
            default=list,  # callable default
        )
        
        class Meta:
            app_label = 'test'
    
    # Create a form for the model
    class TestModelForm(ModelForm):
        class Meta:
            model = TestModel
            fields = ['array_field']
    
    # Create form instance
    form = TestModelForm()
    
    # Get the formfield for the ArrayField
    array_formfield = form.fields['array_field']
    
    # The bug: ArrayField with callable default should have show_hidden_initial=False
    # but currently it doesn't, so this assertion will fail
    assert array_formfield.show_hidden_initial == False, (
        "ArrayField with callable default should have show_hidden_initial=False "
        "to prevent hidden initial inputs that bypass validation on resubmission"
    )