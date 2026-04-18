import os
import tempfile
import unittest
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.forms import FilePathField as FormFilePathField
from django.test import TestCase


class CallableFilePathFieldTest(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(self.test_file, 'w') as f:
            f.write('test content')
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def get_temp_path(self):
        """Callable that returns the temp directory path"""
        return self.temp_dir
    
    def test_callable_path_in_form_field(self):
        """Test that FilePathField accepts callable path in forms"""
        field = FormFilePathField(path=self.get_temp_path)
        choices = list(field._get_choices())
        self.assertTrue(len(choices) > 0)
        self.assertTrue(any('test.txt' in choice[1] for choice in choices))
    
    def test_string_path_still_works(self):
        """Test backward compatibility with string paths"""
        field = FormFilePathField(path=self.temp_dir)
        choices = list(field._get_choices())
        self.assertTrue(len(choices) > 0)
        self.assertTrue(any('test.txt' in choice[1] for choice in choices))
    
    def test_callable_path_evaluated_each_time(self):
        """Test that callable path is evaluated each time choices are accessed"""
        call_count = 0
        
        def counting_path():
            nonlocal call_count
            call_count += 1
            return self.temp_dir
        
        field = FormFilePathField(path=counting_path)
        
        # Access choices multiple times
        list(field._get_choices())
        list(field._get_choices())
        
        self.assertEqual(call_count, 2)
    
    def test_model_field_with_callable_path(self):
        """Test that model FilePathField works with callable path"""
        class TestModel(models.Model):
            file_path = models.FilePathField(path=self.get_temp_path)
            
            class Meta:
                app_label = 'test'
        
        # Test that the field can be created
        field = TestModel._meta.get_field('file_path')
        self.assertEqual(field.path, self.get_temp_path)
    
    def test_model_field_deconstruction_with_callable(self):
        """Test that model field deconstruction works with callable paths"""
        field = models.FilePathField(path=self.get_temp_path)
        name, path, args, kwargs = field.deconstruct()
        
        # The callable should be preserved in kwargs
        self.assertEqual(kwargs['path'], self.get_temp_path)
        self.assertTrue(callable(kwargs['path']))
    
    def test_formfield_creation_with_callable_path(self):
        """Test that formfield() method works with callable paths"""
        model_field = models.FilePathField(path=self.get_temp_path)
        form_field = model_field.formfield()
        
        self.assertIsInstance(form_field, FormFilePathField)
        self.assertEqual(form_field.path, self.get_temp_path)
        
        # Test that choices are generated correctly
        choices = list(form_field._get_choices())
        self.assertTrue(len(choices) > 0)
    
    def test_callable_path_with_nonexistent_directory(self):
        """Test behavior when callable returns nonexistent directory"""
        def nonexistent_path():
            return '/nonexistent/directory'
        
        field = FormFilePathField(path=nonexistent_path)
        choices = list(field._get_choices())
        
        # Should return empty list when directory doesn't exist
        self.assertEqual(choices, [])
    
    def test_callable_path_with_recursive_option(self):
        """Test callable path works with recursive=True"""
        # Create a subdirectory with a file
        subdir = os.path.join(self.temp_dir, 'subdir')
        os.makedirs(subdir)
        subfile = os.path.join(subdir, 'subfile.txt')
        with open(subfile, 'w') as f:
            f.write('sub content')
        
        field = FormFilePathField(path=self.get_temp_path, recursive=True)
        choices = list(field._get_choices())
        
        # Should include files from subdirectories
        choice_values = [choice[0] for choice in choices]
        self.assertTrue(any('subfile.txt' in value for value in choice_values))
    
    def test_callable_path_with_match_pattern(self):
        """Test callable path works with match pattern"""
        # Create files with different extensions
        txt_file = os.path.join(self.temp_dir, 'test.txt')
        py_file = os.path.join(self.temp_dir, 'test.py')
        
        with open(py_file, 'w') as f:
            f.write('# python file')
        
        field = FormFilePathField(path=self.get_temp_path, match=r'.*\.py$')
        choices = list(field._get_choices())
        
        # Should only include .py files
        self.assertTrue(len(choices) > 0)
        self.assertTrue(all('.py' in choice[1] for choice in choices))
    
    @mock.patch('os.listdir')
    def test_callable_path_os_error_handling(self, mock_listdir):
        """Test that OSError is handled gracefully with callable paths"""
        mock_listdir.side_effect = OSError("Permission denied")
        
        field = FormFilePathField(path=self.get_temp_path)
        choices = list(field._get_choices())
        
        # Should return empty list when OSError occurs
        self.assertEqual(choices, [])
