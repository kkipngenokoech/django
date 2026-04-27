import warnings
import sys
import os

# Add the current directory to the path so we can import Django
sys.path.insert(0, os.path.abspath('.'))

# Import the Media class directly
from django.forms.widgets import Media, MediaOrderConflictWarning

def test_issue_reproduction():
    """Test that merging 3+ media objects throws unnecessary MediaOrderConflictWarning."""
    
    # Create media objects that represent the widgets
    color_picker_media = Media(js=['color-picker.js'])
    simple_text_media = Media(js=['text-editor.js'])
    fancy_text_media = Media(js=['text-editor.js', 'text-editor-extras.js', 'color-picker.js'])
    
    # This should not produce a MediaOrderConflictWarning
    # The expected order should be: text-editor.js, text-editor-extras.js, color-picker.js
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Simulate the form media merging process
        media = color_picker_media + simple_text_media + fancy_text_media
        
        # Check if MediaOrderConflictWarning was raised (it shouldn't be)
        media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
        
        print(f"Media warnings: {len(media_warnings)}")
        if media_warnings:
            print(f"Warning message: {media_warnings[0].message}")
        
        print(f"Final JS order: {media._js}")
        
        # This assertion will FAIL on the current buggy code because it does produce the warning
        if len(media_warnings) > 0:
            print(f"FAILED: Unexpected MediaOrderConflictWarning: {media_warnings[0].message}")
            return False
        
        # Verify the final JS order is correct
        expected_js = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
        if media._js != expected_js:
            print(f"FAILED: Expected {expected_js}, got {media._js}")
            return False
            
        return True


if __name__ == "__main__":
    if test_issue_reproduction():
        print("Test passed!")
    else:
        print("Test failed!")
        sys.exit(1)