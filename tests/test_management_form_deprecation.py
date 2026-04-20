import warnings
from django.forms.formsets import ManagementForm
from django.utils.deprecation import RemovedInDjango50Warning


def test_issue_reproduction():
    """Test that ManagementForm rendering raises deprecation warning for default.html template."""
    # Create a ManagementForm instance
    management_form = ManagementForm({
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000'
    }, prefix='form')
    
    # Capture warnings when rendering the management form
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")
        # Render the management form - this should trigger deprecation warning
        str(management_form)
    
    # Check if deprecation warning was raised
    deprecation_warnings = [
        w for w in warning_list 
        if issubclass(w.category, RemovedInDjango50Warning)
        and 'default.html' in str(w.message)
    ]
    
    # This assertion should FAIL on current code (warning is raised)
    # and PASS after fix (no warning for ManagementForm)
    assert len(deprecation_warnings) == 0, f"ManagementForm should not raise deprecation warning, but got: {[str(w.message) for w in deprecation_warnings]}"