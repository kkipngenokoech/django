import unittest
import warnings
from django.forms import widgets
from django.forms.widgets import Media, MediaOrderConflictWarning


class MediaMergeTests(unittest.TestCase):
    def test_merge_three_media_objects_no_false_conflicts(self):
        """
        Test that merging 3+ media objects doesn't produce false conflict warnings
        when dependencies can be satisfied without conflicts.
        """
        # Simulate the scenario from the issue:
        # ColorPicker: ['color-picker.js']
        # SimpleTextWidget: ['text-editor.js']
        # FancyTextWidget: ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
        
        color_picker_media = Media(js=['color-picker.js'])
        simple_text_media = Media(js=['text-editor.js'])
        fancy_text_media = Media(js=['text-editor.js', 'text-editor-extras.js', 'color-picker.js'])
        
        # This should not produce any warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined_media = color_picker_media + simple_text_media + fancy_text_media
            
            # Check that no MediaOrderConflictWarning was raised
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0, 
                           f"Unexpected MediaOrderConflictWarning: {[str(w.message) for w in media_warnings]}")
            
            # Verify the final order is correct
            expected_order = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
            self.assertEqual(combined_media._js, expected_order)
    
    def test_merge_with_real_conflicts(self):
        """
        Test that real conflicts still produce warnings.
        """
        # Create a scenario with a real conflict
        media1 = Media(js=['a.js', 'b.js'])
        media2 = Media(js=['b.js', 'a.js'])  # Opposite order - real conflict
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined_media = media1 + media2
            
            # This should still produce a warning for the real conflict
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 1)
    
    def test_complex_dependency_chain(self):
        """
        Test a more complex scenario with multiple dependencies.
        """
        # base.js <- jquery.js <- widget.js <- app.js
        media1 = Media(js=['base.js'])
        media2 = Media(js=['jquery.js', 'base.js'])
        media3 = Media(js=['widget.js', 'jquery.js'])
        media4 = Media(js=['app.js', 'widget.js', 'jquery.js', 'base.js'])
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined_media = media1 + media2 + media3 + media4
            
            # Should not produce warnings as dependencies can be satisfied
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            # Verify a valid dependency order
            js_files = combined_media._js
            base_idx = js_files.index('base.js')
            jquery_idx = js_files.index('jquery.js')
            widget_idx = js_files.index('widget.js')
            app_idx = js_files.index('app.js')
            
            # base.js should come before jquery.js
            self.assertLess(base_idx, jquery_idx)
            # jquery.js should come before widget.js
            self.assertLess(jquery_idx, widget_idx)
            # widget.js should come before app.js
            self.assertLess(widget_idx, app_idx)
