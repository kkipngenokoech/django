import warnings
import sys
import os

# Add the current directory to the path so we can import Django
sys.path.insert(0, os.path.abspath('.'))

# Import the Media class directly
from django.forms.widgets import Media, MediaOrderConflictWarning

def debug_media_merging():
    """Debug the media merging process step by step."""
    
    # Create media objects that represent the widgets
    color_picker_media = Media(js=['color-picker.js'])
    simple_text_media = Media(js=['text-editor.js'])
    fancy_text_media = Media(js=['text-editor.js', 'text-editor-extras.js', 'color-picker.js'])
    
    print("Individual media objects:")
    print(f"color_picker_media._js: {color_picker_media._js}")
    print(f"simple_text_media._js: {simple_text_media._js}")
    print(f"fancy_text_media._js: {fancy_text_media._js}")
    print()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Step 1: color_picker + simple_text
        step1 = color_picker_media + simple_text_media
        print(f"Step 1 (color_picker + simple_text): {step1._js}")
        
        # Step 2: step1 + fancy_text
        step2 = step1 + fancy_text_media
        print(f"Step 2 (step1 + fancy_text): {step2._js}")
        
        # Check warnings
        media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
        print(f"Warnings: {len(media_warnings)}")
        for warning in media_warnings:
            print(f"Warning: {warning.message}")


if __name__ == "__main__":
    debug_media_merging()