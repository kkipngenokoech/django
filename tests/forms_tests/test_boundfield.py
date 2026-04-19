import pytest
from django import forms
from django.forms.widgets import CheckboxSelectMultiple


def test_issue_reproduction():
    """Test that BoundWidget.id_for_label uses the ID from widget attrs."""
    
    class TestForm(forms.Form):
        choices = forms.MultipleChoiceField(
            choices=[('option1', 'Option 1'), ('option2', 'Option 2')],
            widget=CheckboxSelectMultiple
        )
    
    # Create form with custom auto_id format
    form = TestForm(auto_id='custom_%s')
    
    # Get the subwidgets (BoundWidget instances)
    subwidgets = form['choices'].subwidgets
    
    # The first subwidget should have an ID that follows the custom auto_id format
    first_widget = subwidgets[0]
    
    # Check what ID is actually set in the widget's attrs
    expected_id = first_widget.data['attrs']['id']  # Should be 'custom_choices_0'
    
    # The bug: id_for_label ignores the attrs ID and generates its own
    actual_id = first_widget.id_for_label
    
    # This assertion will FAIL on the current buggy code because
    # id_for_label returns 'id_choices_0' instead of 'custom_choices_0'
    assert actual_id == expected_id, f"Expected {expected_id}, got {actual_id}"