import warnings
from django.forms.formsets import ManagementForm
from django.utils.deprecation import RemovedInDjango50Warning

def test_issue_reproduction():
    """Test that ManagementForm does not raise deprecation warning for default.html template."""
    # Create a ManagementForm instance
    management_form = ManagementForm()
    management_form.template_name = "django/forms/default.html"
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")
        
        # Render the management form - this should NOT raise a deprecation warning
        # since management forms only contain hidden inputs and template choice is irrelevant
        str(management_form)
        
        # Check if any RemovedInDjango50Warning was raised
        django_warnings = [w for w in warning_list if issubclass(w.category, RemovedInDjango50Warning)]
        
        # This assertion will FAIL on current code because the warning IS raised
        # but should PASS after the fix when ManagementForm is special-cased
        assert len(django_warnings) == 0, f"ManagementForm should not raise deprecation warning, but got: {[str(w.message) for w in django_warnings]}"