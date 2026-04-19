import warnings
import sys
import os

# Add the current directory to the path so we can import Django
sys.path.insert(0, os.path.abspath('.'))

# Import the Media class directly
from django.forms.widgets import Media, MediaOrderConflictWarning

def debug_merge_function():
    """Debug the merge function step by step."""
    
    # Test the merge function directly
    list_1 = ['color-picker.js', 'text-editor.js']
    list_2 = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
    
    print(f"Merging list_1: {list_1}")
    print(f"With list_2: {list_2}")
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        result = Media.merge(list_1, list_2)
        print(f"Result: {result}")
        
        # Check warnings
        media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
        print(f"Warnings: {len(media_warnings)}")
        for warning in media_warnings:
            print(f"Warning: {warning.message}")


if __name__ == "__main__":
    debug_merge_function()