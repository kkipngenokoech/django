import warnings
from django import forms
from django.forms.widgets import MediaOrderConflictWarning

def test_issue_reproduction():
    """Test that merging 3+ media objects doesn't throw unnecessary MediaOrderConflictWarnings."""
    
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
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # This should not produce any MediaOrderConflictWarning
        # The correct order should be: text-editor.js, text-editor-extras.js, color-picker.js
        media = MyForm().media
        
        # Check that no MediaOrderConflictWarning was raised
        media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
        
        # This assertion will FAIL on the current buggy code because it raises the warning
        assert len(media_warnings) == 0, f"Unexpected MediaOrderConflictWarning: {media_warnings[0].message if media_warnings else 'None'}"
        
        # Verify the final order is correct
        expected_js = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
        assert media._js == expected_js, f"Expected {expected_js}, got {media._js}"