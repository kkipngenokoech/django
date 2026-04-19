import os
import tempfile
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.forms import FilePathField as FormFilePathField
from django.test import TestCase
from django.test.utils import isolate_apps


class FilePathFieldCallableTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, 'test.txt')
        with open(self.temp_file, 'w') as f:
            f.write('test content')

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_callable_path_function(self):
        """Test that FilePathField accepts a callable that returns a path."""
        def get_path():
            return self.temp_dir

        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

        field = TestModel._meta.get_field('file_path')
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_lambda(self):
        """Test that FilePathField accepts a lambda that returns a path."""
        get_path = lambda: self.temp_dir

        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

        field = TestModel._meta.get_field('file_path')
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_string_path_still_works(self):
        """Test that string paths still work as before."""
        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=self.temp_dir)

        field = TestModel._meta.get_field('file_path')
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_formfield_with_callable_path(self):
        """Test that formfield() resolves callable paths."""
        def get_path():
            return self.temp_dir

        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

        field = TestModel._meta.get_field('file_path')
        form_field = field.formfield()
        self.assertEqual(form_field._get_path(), self.temp_dir)

    def test_form_field_callable_path(self):
        """Test that form FilePathField works with callable paths."""
        def get_path():
            return self.temp_dir

        form_field = FormFilePathField(path=get_path)
        self.assertEqual(form_field._get_path(), self.temp_dir)

    def test_form_field_choices_with_callable_path(self):
        """Test that form field choices are populated correctly with callable path."""
        def get_path():
            return self.temp_dir

        form_field = FormFilePathField(path=get_path, allow_files=True)
        choices = form_field._get_choices()
        # Should find our test file
        self.assertTrue(any(self.temp_file in choice[0] for choice in choices))

    def test_callable_path_migration_serialization(self):
        """Test that callable paths are preserved in migrations, not resolved."""
        def get_path():
            return self.temp_dir

        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

        field = TestModel._meta.get_field('file_path')
        name, path, args, kwargs = field.deconstruct()
        # The callable should be preserved in the kwargs
        self.assertEqual(kwargs['path'], get_path)
        self.assertTrue(callable(kwargs['path']))

    def test_callable_path_called_each_time(self):
        """Test that callable path is called each time it's accessed."""
        call_count = 0
        def get_path():
            nonlocal call_count
            call_count += 1
            return self.temp_dir

        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

        field = TestModel._meta.get_field('file_path')
        
        # Call _get_path multiple times
        field._get_path()
        field._get_path()
        field._get_path()
        
        self.assertEqual(call_count, 3)

    def test_callable_path_with_dynamic_value(self):
        """Test that callable path can return different values."""
        paths = [self.temp_dir, '/tmp']
        path_index = 0
        
        def get_path():
            nonlocal path_index
            result = paths[path_index % len(paths)]
            path_index += 1
            return result

        @isolate_apps('model_fields')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

        field = TestModel._meta.get_field('file_path')
        
        # First call should return temp_dir
        self.assertEqual(field._get_path(), self.temp_dir)
        # Second call should return /tmp
        self.assertEqual(field._get_path(), '/tmp')

    def test_form_field_string_path_still_works(self):
        """Test that form field string paths still work as before."""
        form_field = FormFilePathField(path=self.temp_dir)
        self.assertEqual(form_field._get_path(), self.temp_dir)

    def test_callable_returning_none_handled_gracefully(self):
        """Test that callable returning None is handled gracefully."""
        def get_path():
            return None

        form_field = FormFilePathField(path=get_path)
        # Should not raise an exception
        result = form_field._get_path()
        self.assertIsNone(result)
        
        # _get_choices should handle None path gracefully
        choices = form_field._get_choices()
        self.assertEqual(choices, [])

    def test_callable_returning_empty_string(self):
        """Test that callable returning empty string is handled."""
        def get_path():
            return ''

        form_field = FormFilePathField(path=get_path)
        result = form_field._get_path()
        self.assertEqual(result, '')
        
        # _get_choices should handle empty string path gracefully
        choices = form_field._get_choices()
        self.assertEqual(choices, [])
