import warnings
import sys
import os

# Add the parent directory to the path so we can import Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-key',
        USE_TZ=True,
    )

django.setup()

from django import forms
from django.forms.widgets import MediaOrderConflictWarning


def test_issue_reproduction():
    """Test that merging 3+ media objects throws unnecessary MediaOrderConflictWarning."""
    
    class ColorPicker(forms.Widget):
        class Media:
            js = ['color-picker.js']
    
    class SimpleTextWidget(forms.Widget):
        class Media:
            js = ['text-editor.js']
    
    class FancyTextWidget(forms.Widget):
        class Media:
            js = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
    
    class MyForm(forms.Form):
        background_color = forms.CharField(widget=ColorPicker())
        intro = forms.CharField(widget=SimpleTextWidget())
        body = forms.CharField(widget=FancyTextWidget())
    
    # This should not produce a MediaOrderConflictWarning
    # The expected order should be: text-editor.js, text-editor-extras.js, color-picker.js
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        media = MyForm().media
        
        # Check if MediaOrderConflictWarning was raised (it shouldn't be)
        media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
        
        print(f"Media warnings: {len(media_warnings)}")
        if media_warnings:
            print(f"Warning message: {media_warnings[0].message}")
        
        print(f"Final JS order: {media._js}")
        
        # This assertion will FAIL on the current buggy code because it does produce the warning
        assert len(media_warnings) == 0, f"Unexpected MediaOrderConflictWarning: {media_warnings[0].message if media_warnings else 'None'}"
        
        # Verify the final JS order is correct
        expected_js = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
        assert media._js == expected_js, f"Expected {expected_js}, got {media._js}"


if __name__ == "__main__":
    test_issue_reproduction()
    print("Test passed!")