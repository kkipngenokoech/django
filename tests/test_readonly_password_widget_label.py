import pytest
from django.contrib.auth.forms import ReadOnlyPasswordHashWidget, ReadOnlyPasswordHashField
from django.forms import Form
from django.forms.boundfield import BoundField


def test_issue_reproduction():
    """Test that ReadOnlyPasswordHashWidget label doesn't have 'for' attribute."""
    
    class TestForm(Form):
        password = ReadOnlyPasswordHashField()
    
    form = TestForm()
    bound_field = form['password']
    
    # Generate the label tag
    label_html = bound_field.label_tag()
    
    # The issue: label should not have 'for' attribute since the widget
    # renders non-labelable elements, but currently it does
    assert 'for=' not in label_html, f"Label should not have 'for' attribute but got: {label_html}"