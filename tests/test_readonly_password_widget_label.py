import pytest
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField, ReadOnlyPasswordHashWidget
from django.test import TestCase
from django.forms.widgets import Widget


def test_issue_reproduction():
    """Test that ReadOnlyPasswordHashWidget label doesn't have 'for' attribute pointing to non-labelable element."""
    
    class TestForm(forms.Form):
        password = ReadOnlyPasswordHashField(label="Password")
    
    form = TestForm()
    
    # Render the form field
    rendered_html = str(form['password'])
    
    # The widget should render without any input element that can be labeled
    # Check that there's no input element with an id that a label could reference
    assert '<input' not in rendered_html, "ReadOnlyPasswordHashWidget should not render input elements"
    
    # Now check the label rendering - this is where the bug manifests
    # The label should not have a 'for' attribute since there's no labelable element
    label_html = form['password'].label_tag()
    
    # This assertion will FAIL on buggy code because the label will have a 'for' attribute
    # pointing to an id that doesn't correspond to any labelable element
    assert 'for=' not in label_html, f"Label should not have 'for' attribute for read-only widget, but got: {label_html}"