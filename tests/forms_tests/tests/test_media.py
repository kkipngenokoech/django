import unittest
import warnings
from django import forms
from django.forms.widgets import Media, MediaOrderConflictWarning


class MediaMergeTests(unittest.TestCase):
    """
    Test cases for Media merging functionality, specifically addressing
    the issue where merging 3+ media objects throws unnecessary warnings.
    """

    def test_three_media_merge_no_conflict_warning(self):
        """
        Test that merging three media objects with independent files
        doesn't produce unnecessary MediaOrderConflictWarnings.
        
        This reproduces the exact scenario from the GitHub issue.
        """
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

        # This should not raise any warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            media = MyForm().media
            
            # Check that no MediaOrderConflictWarning was raised
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0, 
                           f"Unexpected MediaOrderConflictWarning: {[str(warning.message) for warning in media_warnings]}")
            
            # Verify the final order is correct
            expected_js = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
            self.assertEqual(media._js, expected_js)

    def test_real_conflict_still_warns(self):
        """
        Test that real ordering conflicts still produce warnings.
        """
        media1 = Media(js=['a.js', 'b.js'])
        media2 = Media(js=['b.js', 'a.js'])
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined = media1 + media2
            
            # This should still produce a warning for real conflicts
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 1)

    def test_no_conflict_different_files(self):
        """
        Test that files appearing in different positions but without
        actual dependencies don't cause warnings.
        """
        media1 = Media(js=['a.js'])
        media2 = Media(js=['b.js'])
        media3 = Media(js=['a.js', 'c.js', 'b.js'])
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined = media1 + media2 + media3
            
            # Should not produce warnings since there's no actual conflict
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            # Verify reasonable ordering
            self.assertIn('a.js', combined._js)
            self.assertIn('b.js', combined._js)
            self.assertIn('c.js', combined._js)

    def test_complex_merge_scenario(self):
        """
        Test a more complex scenario with multiple widgets and dependencies.
        """
        media1 = Media(js=['jquery.js'])
        media2 = Media(js=['widget1.js'])
        media3 = Media(js=['jquery.js', 'plugin.js', 'widget1.js'])
        media4 = Media(js=['widget2.js'])
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined = media1 + media2 + media3 + media4
            
            # Should not produce warnings for this scenario
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            # Verify that jquery comes before plugin, and dependencies are maintained
            js_list = combined._js
            jquery_index = js_list.index('jquery.js')
            plugin_index = js_list.index('plugin.js')
            self.assertLess(jquery_index, plugin_index, "jquery.js should come before plugin.js")

    def test_preserve_dependency_order(self):
        """
        Test that actual dependencies are preserved in the merge.
        """
        # This represents the scenario where text-editor-extras.js depends on text-editor.js
        media1 = Media(js=['text-editor.js', 'text-editor-extras.js'])
        media2 = Media(js=['color-picker.js'])
        media3 = Media(js=['text-editor.js'])
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            combined = media1 + media2 + media3
            
            # Should not produce warnings
            media_warnings = [warning for warning in w if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            # Verify dependency order is maintained
            js_list = combined._js
            text_editor_index = js_list.index('text-editor.js')
            text_editor_extras_index = js_list.index('text-editor-extras.js')
            self.assertLess(text_editor_index, text_editor_extras_index, 
                          "text-editor.js should come before text-editor-extras.js")
