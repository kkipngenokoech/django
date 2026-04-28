import pytest
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import ModelForm
from django.test import TestCase


class TestModel(models.Model):
    array_field = ArrayField(
        models.CharField(max_length=42),
        default=list,
    )
    
    class Meta:
        app_label = 'test'


class TestModelForm(ModelForm):
    def clean(self):
        raise ValidationError("validation error")
    
    class Meta:
        model = TestModel
        fields = ['array_field']


def test_issue_reproduction():
    """Test that ModelForm fields with callable defaults don't bypass validation on resubmission."""
    # First submission with data that will cause validation error
    form_data = {'array_field': ['test_value']}
    form1 = TestModelForm(data=form_data)
    
    # Form should be invalid due to clean() raising ValidationError
    assert not form1.is_valid()
    assert 'validation error' in str(form1.errors)
    
    # Second submission with same data - this should also fail validation
    # but currently passes due to the bug with hidden initial inputs
    form2 = TestModelForm(data=form_data)
    
    # This assertion should pass but currently fails due to the bug
    # The bug causes validation to be bypassed on the second submission
    assert not form2.is_valid()
    assert 'validation error' in str(form2.errors)