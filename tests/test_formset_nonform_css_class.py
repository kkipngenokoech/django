import pytest
from django.forms import Form, CharField, formsets
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError


def test_issue_reproduction():
    """Test that FormSets add 'nonform' CSS class for non-form errors."""
    
    class TestForm(Form):
        name = CharField()
    
    class TestFormSet(formsets.BaseFormSet):
        def clean(self):
            # Raise a non-form error to trigger the issue
            raise ValidationError("This is a non-form error")
    
    # Create a formset factory
    FormSet = formsets.formset_factory(TestForm, formset=TestFormSet)
    
    # Create formset with valid data to trigger clean() method
    data = {
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-0-name': 'test',
    }
    
    formset = FormSet(data=data)
    
    # Trigger validation which will call clean() and create non-form errors
    formset.is_valid()
    
    # Get the non-form errors
    non_form_errors = formset.non_form_errors()
    
    # Check that the ErrorList has the 'nonform' CSS class
    # This should fail on current code since 'nonform' class is not added
    assert hasattr(non_form_errors, 'error_class')
    assert 'nonform' in non_form_errors.error_class