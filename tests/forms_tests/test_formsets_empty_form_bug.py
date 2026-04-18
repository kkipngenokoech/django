import pytest
from django.forms import formset_factory, Form, CharField


class TestForm(Form):
    test_field = CharField()


def test_issue_reproduction():
    """Test that accessing empty_form with empty_permitted in form_kwargs raises KeyError."""
    # Create a formset with empty_permitted in form_kwargs
    FormSet = formset_factory(TestForm)
    formset = FormSet(form_kwargs={'empty_permitted': True})
    
    # This should raise a TypeError due to duplicate empty_permitted keyword argument
    with pytest.raises(TypeError, match="got multiple values for keyword argument 'empty_permitted'"):
        _ = formset.empty_form