import os
import tempfile
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps


class FilePathFieldCallableTests(TestCase):
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

    def test_callable_path_basic(self):
        """Test that FilePathField accepts a callable for path parameter."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        self.assertTrue(callable(field.path))
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_not_called_during_init(self):
        """Test that callable path is not called during field initialization."""
        call_count = 0

        def get_path():
            nonlocal call_count
            call_count += 1
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        self.assertEqual(call_count, 0)
        # Only called when _get_path() is invoked
        field._get_path()
        self.assertEqual(call_count, 1)

    def test_callable_path_called_on_formfield(self):
        """Test that callable path is resolved when creating form field."""
        def get_path():
            return self.temp_dir

        field = models.FilePathField(path=get_path)
        form_field = field.formfield()
        self.assertEqual(form_field.path, self.temp_dir)

    def test_string_path_still_works(self):
        """Test that string paths continue to work (backwards compatibility)."""
        field = models.FilePathField(path=self.temp_dir)
        self.assertFalse(callable(field.path))
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_with_dynamic_value(self):
        """Test callable path that returns different values."""
        paths = ['/path1', '/path2']
        counter = 0

        def get_dynamic_path():
            nonlocal counter
            path = paths[counter % len(paths)]
            counter += 1
            return path

        field = models.FilePathField(path=get_dynamic_path)
        self.assertEqual(field._get_path(), '/path1')
        self.assertEqual(field._get_path(), '/path2')
        self.assertEqual(field._get_path(), '/path1')

    @isolate_apps('model_fields')
    def test_callable_path_in_model(self):
        """Test FilePathField with callable path in a model definition."""
        def get_path():
            return self.temp_dir

        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)

            class Meta:
                app_label = 'model_fields'

        field = TestModel._meta.get_field('file_path')
        self.assertTrue(callable(field.path))
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_deconstruct(self):
        """Test that callable path is preserved in deconstruct for migrations."""
        def get_path():
            return '/some/path'

        field = models.FilePathField(path=get_path)
        name, path, args, kwargs = field.deconstruct()
        self.assertIs(kwargs['path'], get_path)
        self.assertTrue(callable(kwargs['path']))

    def test_callable_path_with_settings(self):
        """Test callable path that uses Django settings (common use case)."""
        with mock.patch('django.conf.settings.MEDIA_ROOT', '/media/root'):
            def get_media_path():
                from django.conf import settings
                return os.path.join(settings.MEDIA_ROOT, 'uploads')

            field = models.FilePathField(path=get_media_path)
            self.assertEqual(field._get_path(), '/media/root/uploads')

    def test_callable_path_with_os_path_join(self):
        """Test callable path using os.path.join (the original use case)."""
        base_dir = '/base'
        
        def get_joined_path():
            return os.path.join(base_dir, 'subdir')

        field = models.FilePathField(path=get_joined_path)
        expected_path = os.path.join(base_dir, 'subdir')
        self.assertEqual(field._get_path(), expected_path)

    def test_empty_string_path_still_works(self):
        """Test that empty string path (default) still works."""
        field = models.FilePathField()
        self.assertEqual(field.path, '')
        self.assertEqual(field._get_path(), '')

    def test_none_path_handled(self):
        """Test that None path is handled gracefully."""
        field = models.FilePathField(path=None)
        self.assertIsNone(field.path)
        self.assertIsNone(field._get_path())

    def test_callable_returning_none(self):
        """Test callable that returns None."""
        def get_none_path():
            return None

        field = models.FilePathField(path=get_none_path)
        self.assertIsNone(field._get_path())
