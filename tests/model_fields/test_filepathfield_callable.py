import os
import tempfile
import unittest
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.forms import FilePathField as FormFilePathField
from django.test import TestCase


class CallableFilePathFieldTests(TestCase):
    """
    Tests for FilePathField with callable path parameter.
    """

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
        """Test that FilePathField accepts a callable path."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_lambda(self):
        """Test that FilePathField accepts a lambda as path."""
        field = models.FilePathField(path=lambda: self.temp_dir)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_non_callable_path(self):
        """Test that FilePathField still works with string path."""
        field = models.FilePathField(path=self.temp_dir)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_returns_none(self):
        """Test behavior when callable path returns None."""
        field = models.FilePathField(path=lambda: None)
        self.assertIsNone(field._get_path())

    def test_callable_path_returns_empty_string(self):
        """Test behavior when callable path returns empty string."""
        field = models.FilePathField(path=lambda: '')
        self.assertEqual(field._get_path(), '')

    def test_formfield_with_callable_path(self):
        """Test that formfield() resolves callable path correctly."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        form_field = field.formfield()
        
        # The form field should have the resolved path, not the callable
        self.assertEqual(form_field.path, self.temp_dir)
        self.assertIsInstance(form_field, FormFilePathField)

    def test_deconstruct_with_callable_path(self):
        """Test that deconstruct() preserves callable path for migrations."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        name, path, args, kwargs = field.deconstruct()
        
        # The callable should be preserved in the deconstructed field
        self.assertEqual(kwargs['path'], get_path)
        self.assertTrue(callable(kwargs['path']))

    def test_callable_path_with_match_parameter(self):
        """Test callable path works with match parameter."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path, match=r'.*\.txt$')
        self.assertEqual(field._get_path(), self.temp_dir)
        self.assertEqual(field.match, r'.*\.txt$')

    def test_callable_path_with_recursive_parameter(self):
        """Test callable path works with recursive parameter."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path, recursive=True)
        self.assertEqual(field._get_path(), self.temp_dir)
        self.assertTrue(field.recursive)

    @mock.patch('os.path.isdir')
    def test_callable_path_called_during_validation(self, mock_isdir):
        """Test that callable path is called when needed."""
        mock_isdir.return_value = True
        call_count = 0
        
        def get_path():
            nonlocal call_count
            call_count += 1
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        
        # Access the path multiple times
        field._get_path()
        field._get_path()
        
        # The callable should be called each time
        self.assertEqual(call_count, 2)


class CallableFormFilePathFieldTests(TestCase):
    """
    Tests for form FilePathField with callable path parameter.
    """

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

    def test_form_field_callable_path_function(self):
        """Test that form FilePathField accepts a callable path."""
        def get_path():
            return self.temp_dir

        field = FormFilePathField(path=get_path)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_form_field_callable_path_lambda(self):
        """Test that form FilePathField accepts a lambda as path."""
        field = FormFilePathField(path=lambda: self.temp_dir)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_form_field_non_callable_path(self):
        """Test that form FilePathField still works with string path."""
        field = FormFilePathField(path=self.temp_dir)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_form_field_callable_path_returns_none(self):
        """Test behavior when callable path returns None."""
        field = FormFilePathField(path=lambda: None)
        self.assertIsNone(field._get_path())

    def test_form_field_get_choices_with_callable_path(self):
        """Test that _get_choices() works with callable path."""
        def get_path():
            return self.temp_dir

        field = FormFilePathField(path=get_path, allow_files=True)
        choices = field._get_choices()
        
        # Should find our test file
        file_choices = [choice for choice in choices if choice[0].endswith('test.txt')]
        self.assertEqual(len(file_choices), 1)

    def test_form_field_get_choices_with_none_path(self):
        """Test that _get_choices() handles None path gracefully."""
        field = FormFilePathField(path=lambda: None, allow_files=True)
        choices = field._get_choices()
        
        # Should return empty list when path is None
        self.assertEqual(choices, [])

    def test_form_field_get_choices_with_empty_path(self):
        """Test that _get_choices() handles empty string path gracefully."""
        field = FormFilePathField(path=lambda: '', allow_files=True)
        choices = field._get_choices()
        
        # Should return empty list when path is empty
        self.assertEqual(choices, [])

    @mock.patch('os.walk')
    def test_form_field_callable_path_called_in_get_choices(self, mock_walk):
        """Test that callable path is called in _get_choices()."""
        mock_walk.return_value = []
        call_count = 0
        
        def get_path():
            nonlocal call_count
            call_count += 1
            return self.temp_dir

        field = FormFilePathField(path=get_path, allow_files=True)
        field._get_choices()
        
        # The callable should be called
        self.assertEqual(call_count, 1)
        mock_walk.assert_called_once_with(self.temp_dir)
