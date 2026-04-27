import warnings
from django import forms
from django.forms.widgets import MediaOrderConflictWarning
from django.test import TestCase


class MediaOrderConflictTests(TestCase):
    """
    Tests for MediaOrderConflictWarning when merging multiple media objects.
    """

    def test_three_media_objects_no_false_conflict(self):
        """
        Test that merging 3 media objects doesn't produce false conflicts.
        This reproduces the issue described in the bug report.
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

        # This should not raise any MediaOrderConflictWarning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            media = MyForm().media
            
            # Check that no MediaOrderConflictWarning was raised
            media_warnings = [warning for warning in w 
                            if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0, 
                           f"Unexpected MediaOrderConflictWarning: {[str(warning.message) for warning in media_warnings]}")
            
            # Verify the correct order is maintained
            expected_order = ['text-editor.js', 'text-editor-extras.js', 'color-picker.js']
            self.assertEqual(media._js, expected_order)

    def test_legitimate_conflict_still_warns(self):
        """
        Test that legitimate ordering conflicts still produce warnings.
        """
        class Widget1(forms.Widget):
            class Media:
                js = ['a.js', 'b.js']

        class Widget2(forms.Widget):
            class Media:
                js = ['b.js', 'a.js']  # Opposite order - this should warn

        class TestForm(forms.Form):
            field1 = forms.CharField(widget=Widget1())
            field2 = forms.CharField(widget=Widget2())

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            media = TestForm().media
            
            # This should still produce a warning for legitimate conflicts
            media_warnings = [warning for warning in w 
                            if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 1)

    def test_complex_dependency_resolution(self):
        """
        Test complex dependency resolution with multiple widgets.
        """
        class BaseWidget(forms.Widget):
            class Media:
                js = ['base.js']

        class ExtensionWidget(forms.Widget):
            class Media:
                js = ['base.js', 'extension.js']

        class UtilityWidget(forms.Widget):
            class Media:
                js = ['utility.js']

        class ComplexWidget(forms.Widget):
            class Media:
                js = ['base.js', 'extension.js', 'utility.js', 'complex.js']

        class ComplexForm(forms.Form):
            base_field = forms.CharField(widget=BaseWidget())
            extension_field = forms.CharField(widget=ExtensionWidget())
            utility_field = forms.CharField(widget=UtilityWidget())
            complex_field = forms.CharField(widget=ComplexWidget())

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            media = ComplexForm().media
            
            # Should not produce any warnings
            media_warnings = [warning for warning in w 
                            if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            # Verify correct dependency order
            js_files = media._js
            base_idx = js_files.index('base.js')
            extension_idx = js_files.index('extension.js')
            complex_idx = js_files.index('complex.js')
            
            # base.js should come before extension.js and complex.js
            self.assertLess(base_idx, extension_idx)
            self.assertLess(base_idx, complex_idx)
            # extension.js should come before complex.js
            self.assertLess(extension_idx, complex_idx)

    def test_independent_files_no_conflict(self):
        """
        Test that independent files don't create false conflicts.
        """
        class Widget1(forms.Widget):
            class Media:
                js = ['independent1.js']

        class Widget2(forms.Widget):
            class Media:
                js = ['independent2.js']

        class Widget3(forms.Widget):
            class Media:
                js = ['independent1.js', 'independent2.js']

        class TestForm(forms.Form):
            field1 = forms.CharField(widget=Widget1())
            field2 = forms.CharField(widget=Widget2())
            field3 = forms.CharField(widget=Widget3())

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            media = TestForm().media
            
            # Should not produce any warnings
            media_warnings = [warning for warning in w 
                            if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            # Both files should be present
            self.assertIn('independent1.js', media._js)
            self.assertIn('independent2.js', media._js)

    def test_empty_media_lists(self):
        """
        Test handling of empty media lists.
        """
        class EmptyWidget(forms.Widget):
            class Media:
                js = []

        class NonEmptyWidget(forms.Widget):
            class Media:
                js = ['test.js']

        class TestForm(forms.Form):
            empty_field = forms.CharField(widget=EmptyWidget())
            non_empty_field = forms.CharField(widget=NonEmptyWidget())

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            media = TestForm().media
            
            # Should not produce any warnings
            media_warnings = [warning for warning in w 
                            if issubclass(warning.category, MediaOrderConflictWarning)]
            self.assertEqual(len(media_warnings), 0)
            
            self.assertEqual(media._js, ['test.js'])
