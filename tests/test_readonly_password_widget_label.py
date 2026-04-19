import pytest
from django.contrib.auth.forms import ReadOnlyPasswordHashWidget, ReadOnlyPasswordHashField
from django.forms import Form
from django.test import SimpleTestCase


def test_issue_reproduction():
    """Test that ReadOnlyPasswordHashWidget label doesn't have 'for' attribute."""
    
    class TestForm(Form):
        password = ReadOnlyPasswordHashField()
    
    form = TestForm()
    bound_field = form['password']
    
    # Get the label HTML
    label_html = bound_field.label_tag()
    
    # The label should not have a 'for' attribute since the widget renders non-labelable content
    # This will fail on the current code because it incorrectly includes for="id_password"
    assert 'for=' not in label_html, f"Label should not have 'for' attribute, but got: {label_html}"