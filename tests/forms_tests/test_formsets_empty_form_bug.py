import pytest
from django.forms import Form, CharField
from django.forms.formsets import formset_factory


def test_issue_reproduction():
    """Test that accessing empty_form with empty_permitted in form_kwargs raises TypeError."""
    
    class TestForm(Form):
        name = CharField()
    
    # Create formset with empty_permitted in form_kwargs
    TestFormSet = formset_factory(TestForm)
    formset = TestFormSet(form_kwargs={'empty_permitted': True})
    
    # This should raise TypeError due to duplicate empty_permitted keyword argument
    with pytest.raises(TypeError, match="got multiple values for keyword argument 'empty_permitted'"):
        _ = formset.empty_form