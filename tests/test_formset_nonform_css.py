import pytest
from django import forms
from django.forms import formset_factory
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that FormSets add 'nonform' CSS class for non-form errors."""
    
    class TestForm(forms.Form):
        name = forms.CharField()
    
    class TestFormSet(forms.BaseFormSet):
        def clean(self):
            # Raise a non-form error to trigger the issue
            raise ValidationError("This is a non-form error")
    
    FormSet = formset_factory(TestForm, formset=TestFormSet)
    
    # Create formset with valid form data but trigger non-form error in clean()
    data = {
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-0-name': 'test',
    }
    
    formset = FormSet(data=data)
    formset.is_valid()  # This will trigger full_clean() and the non-form error
    
    # Get the non-form errors
    non_form_errors = formset.non_form_errors()
    
    # Check that the ErrorList has the 'nonform' CSS class
    # This should pass once the issue is fixed, but currently fails
    assert hasattr(non_form_errors, 'error_class')
    assert 'nonform' in non_form_errors.error_class, "FormSet non-form errors should have 'nonform' CSS class"