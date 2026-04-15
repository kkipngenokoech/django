import os
import tempfile
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.test import SimpleTestCase, TestCase
from django.test.utils import isolate_apps


class FilePathFieldCallableTests(SimpleTestCase):
    def test_callable_path_basic(self):
        """Test that model FilePathField accepts a callable path."""
        def get_path():
            return '/test/path'
        
        field = models.FilePathField(path=get_path)
        self.assertEqual(field._get_path(), '/test/path')

    def test_callable_path_none_return(self):
        """Test that callable returning None is handled."""
        def get_path():
            return None
        
        field = models.FilePathField(path=get_path)
        self.assertIsNone(field._get_path())

    def test_string_path_backward_compatibility(self):
        """Test that string paths still work (backward compatibility)."""
        field = models.FilePathField(path='/test/path')
        self.assertEqual(field._get_path(), '/test/path')

    def test_callable_path_dynamic_evaluation(self):
        """Test that callable is evaluated each time, not cached."""
        counter = {'value': 0}
        
        def get_path():
            counter['value'] += 1
            return f'/test/path/{counter["value"]}'
        
        field = models.FilePathField(path=get_path)
        
        # Each call should increment counter
        path1 = field._get_path()
        path2 = field._get_path()
        
        self.assertEqual(path1, '/test/path/1')
        self.assertEqual(path2, '/test/path/2')
        self.assertEqual(counter['value'], 2)

    def test_formfield_uses_evaluated_path(self):
        """Test that formfield() uses the evaluated path from callable."""
        def get_path():
            return '/test/path'
        
        field = models.FilePathField(path=get_path)
        form_field = field.formfield()
        
        # The form field should get the evaluated path, not the callable
        self.assertEqual(form_field.path, '/test/path')
        self.assertFalse(callable(form_field.path))

    def test_deconstruct_preserves_callable(self):
        """Test that deconstruct() preserves callable paths for migrations."""
        def get_path():
            return '/test/path'
        
        field = models.FilePathField(path=get_path)
        name, path, args, kwargs = field.deconstruct()
        
        # The callable should be preserved in kwargs
        self.assertIs(kwargs['path'], get_path)
        self.assertTrue(callable(kwargs['path']))

    def test_deconstruct_preserves_string_path(self):
        """Test that deconstruct() preserves string paths."""
        field = models.FilePathField(path='/test/path')
        name, path, args, kwargs = field.deconstruct()
        
        # String path should be preserved
        self.assertEqual(kwargs['path'], '/test/path')
        self.assertFalse(callable(kwargs['path']))

    @isolate_apps('test_app')
    def test_model_with_callable_path_field(self):
        """Test creating a model with callable FilePathField."""
        def get_upload_path():
            return '/uploads'
        
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_upload_path)
            
            class Meta:
                app_label = 'test_app'
        
        # Field should be created successfully
        field = TestModel._meta.get_field('file_path')
        self.assertEqual(field._get_path(), '/uploads')

    def test_callable_path_with_settings_reference(self):
        """Test callable path that references Django settings (common use case)."""
        with mock.patch('django.conf.settings') as mock_settings:
            mock_settings.MEDIA_ROOT = '/media'
            
            def get_media_path():
                from django.conf import settings
                return os.path.join(settings.MEDIA_ROOT, 'uploads')
            
            field = models.FilePathField(path=get_media_path)
            self.assertEqual(field._get_path(), '/media/uploads')

    def test_callable_path_with_os_path_join(self):
        """Test callable path using os.path.join (matches the issue description)."""
        with mock.patch('django.conf.settings') as mock_settings:
            mock_settings.LOCAL_FILE_DIR = '/local/files'
            
            def get_local_file_path():
                from django.conf import settings
                return os.path.join(settings.LOCAL_FILE_DIR, 'example_dir')
            
            field = models.FilePathField(path=get_local_file_path)
            self.assertEqual(field._get_path(), '/local/files/example_dir')

    def test_field_parameters_preserved(self):
        """Test that other field parameters work with callable paths."""
        def get_path():
            return '/test/path'
        
        field = models.FilePathField(
            path=get_path,
            match=r'.*\.txt$',
            recursive=True,
            allow_files=True,
            allow_folders=False,
            max_length=200
        )
        
        self.assertEqual(field._get_path(), '/test/path')
        self.assertEqual(field.match, r'.*\.txt$')
        self.assertTrue(field.recursive)
        self.assertTrue(field.allow_files)
        self.assertFalse(field.allow_folders)
        self.assertEqual(field.max_length, 200)

    def test_callable_path_exception_handling(self):
        """Test that exceptions in callable paths are not silently caught."""
        def failing_path():
            raise ValueError("Path calculation failed")
        
        field = models.FilePathField(path=failing_path)
        
        # Exception should propagate
        with self.assertRaises(ValueError):
            field._get_path()

    def test_clone_preserves_callable_path(self):
        """Test that field.clone() preserves callable paths."""
        def get_path():
            return '/test/path'
        
        field = models.FilePathField(path=get_path)
        cloned_field = field.clone()
        
        # Cloned field should have the same callable
        self.assertIs(cloned_field.path, get_path)
        self.assertEqual(cloned_field._get_path(), '/test/path')
