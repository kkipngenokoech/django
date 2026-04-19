import warnings
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
    
    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # This should not produce a MediaOrderConflictWarning
        # because a valid ordering exists: text-editor.js, text-editor-extras.js, color-picker.js
        media = MyForm().media
        
        # Check if any MediaOrderConflictWarning was raised
        conflict_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
        
        # This assertion will FAIL on the current buggy code because it throws unnecessary warnings
        assert len(conflict_warnings) == 0, f"Unexpected MediaOrderConflictWarning raised: {[str(warning.message) for warning in conflict_warnings]}"
        
        # Verify the final JS order is correct
        expected_js = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
        actual_js = media._js
        
        # The JS should be in a valid dependency order
        assert 'text-editor.js' in actual_js
        assert 'text-editor-extras.js' in actual_js  
        assert 'color-picker.js' in actual_js
        
        # text-editor.js should come before text-editor-extras.js
        text_editor_idx = actual_js.index('text-editor.js')
        text_editor_extras_idx = actual_js.index('text-editor-extras.js')
        assert text_editor_idx < text_editor_extras_idx, f"text-editor.js should come before text-editor-extras.js, got: {actual_js}"