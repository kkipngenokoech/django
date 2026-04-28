import warnings
from django.forms import formset_factory, Form
from django.forms.fields import CharField
from django.test import TestCase


class SimpleForm(Form):
    name = CharField()


def test_issue_reproduction():
    """Test that ManagementForm raises deprecation warning when rendered."""
    FormSet = formset_factory(SimpleForm)
    formset = FormSet()
    
    # Capture warnings during management form rendering
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Render the management form - this should trigger the deprecation warning
        str(formset.management_form)
        
        # Check if any deprecation warnings were raised
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        
        # The test should fail because currently ManagementForm triggers deprecation warnings
        # when it shouldn't since it only produces hidden inputs
        assert len(deprecation_warnings) == 0, f"ManagementForm should not raise deprecation warnings, but got: {[str(w.message) for w in deprecation_warnings]}"