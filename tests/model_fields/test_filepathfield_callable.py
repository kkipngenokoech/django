import os
import tempfile
from unittest import mock

from django.core.exceptions import ValidationError
from django.db import models
from django.forms import FilePathField as FilePathFormField
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
    
    def test_callable_path_basic(self):
        """Test that FilePathField accepts a callable for path parameter."""
        def get_path():
            return self.temp_dir
        
        field = models.FilePathField(path=get_path)
        self.assertTrue(callable(field.path))
        self.assertEqual(field._get_path(), self.temp_dir)
    
    def test_callable_path_in_formfield(self):
        """Test that callable path is resolved when creating form field."""
        def get_path():
            return self.temp_dir
        
        field = models.FilePathField(path=get_path)
        form_field = field.formfield()
        
        self.assertIsInstance(form_field, FilePathFormField)
        self.assertEqual(form_field._get_path(), self.temp_dir)
    
    def test_callable_path_choices(self):
        """Test that callable path is resolved when getting choices."""
        def get_path():
            return self.temp_dir
        
        field = models.FilePathField(path=get_path)
        form_field = field.formfield()
        
        # Check that choices include our test file
        choices = [choice[1] for choice in form_field.choices if choice[0]]
        self.assertIn('test.txt', choices)
    
    def test_callable_path_deconstruct(self):
        """Test that callable path is preserved in deconstruct for migrations."""
        def get_path():
            return '/some/path'
        
        field = models.FilePathField(path=get_path)
        name, path, args, kwargs = field.deconstruct()
        
        self.assertEqual(kwargs['path'], get_path)
        self.assertTrue(callable(kwargs['path']))
    
    def test_non_callable_path_still_works(self):
        """Test that non-callable paths still work as before."""
        field = models.FilePathField(path=self.temp_dir)
        self.assertFalse(callable(field.path))
        self.assertEqual(field._get_path(), self.temp_dir)
    
    def test_callable_path_with_model(self):
        """Test callable path works in actual model definition."""
        def get_path():
            return self.temp_dir
        
        @isolate_apps('test_app')
        class TestModel(models.Model):
            file_path = models.FilePathField(path=get_path)
            
            class Meta:
                app_label = 'test_app'
        
        field = TestModel._meta.get_field('file_path')
        self.assertTrue(callable(field.path))
        self.assertEqual(field._get_path(), self.temp_dir)
    
    def test_callable_path_dynamic_resolution(self):
        """Test that callable path is resolved dynamically each time."""
        counter = {'value': 0}
        
        def get_path():
            counter['value'] += 1
            return f'/path/{counter["value"]}'
        
        field = models.FilePathField(path=get_path)
        
        # Each call should increment the counter
        path1 = field._get_path()
        path2 = field._get_path()
        
        self.assertEqual(path1, '/path/1')
        self.assertEqual(path2, '/path/2')
    
    def test_callable_path_with_settings(self):
        """Test callable path using Django settings (simulating the original issue)."""
        with mock.patch('django.conf.settings.LOCAL_FILE_DIR', '/mock/local/files'):
            def get_path():
                from django.conf import settings
                return os.path.join(settings.LOCAL_FILE_DIR, 'example_dir')
            
            field = models.FilePathField(path=get_path)
            expected_path = '/mock/local/files/example_dir'
            self.assertEqual(field._get_path(), expected_path)
    
    def test_form_field_callable_path_choices_refresh(self):
        """Test that form field choices are refreshed when path changes."""
        # Create a second temp directory
        temp_dir2 = tempfile.mkdtemp()
        temp_file2 = os.path.join(temp_dir2, 'test2.txt')
        with open(temp_file2, 'w') as f:
            f.write('test content 2')
        
        try:
            switch = {'use_first': True}
            
            def get_path():
                return self.temp_dir if switch['use_first'] else temp_dir2
            
            form_field = FilePathFormField(path=get_path)
            
            # Initially should show files from first directory
            choices1 = [choice[1] for choice in form_field._get_choices()]
            self.assertIn('test.txt', choices1)
            self.assertNotIn('test2.txt', choices1)
            
            # Switch to second directory
            switch['use_first'] = False
            
            # Create new form field instance to get fresh choices
            form_field2 = FilePathFormField(path=get_path)
            choices2 = [choice[1] for choice in form_field2._get_choices()]
            self.assertNotIn('test.txt', choices2)
            self.assertIn('test2.txt', choices2)
        
        finally:
            if os.path.exists(temp_file2):
                os.remove(temp_file2)
            if os.path.exists(temp_dir2):
                os.rmdir(temp_dir2)
    
    def test_callable_path_with_match_and_recursive(self):
        """Test callable path works with match and recursive options."""
        # Create subdirectory with matching file
        sub_dir = os.path.join(self.temp_dir, 'subdir')
        os.makedirs(sub_dir)
        sub_file = os.path.join(sub_dir, 'match.txt')
        with open(sub_file, 'w') as f:
            f.write('sub content')
        
        try:
            def get_path():
                return self.temp_dir
            
            field = models.FilePathField(
                path=get_path,
                match=r'.*\.txt$',
                recursive=True
            )
            form_field = field.formfield()
            
            choices = [choice[1] for choice in form_field._get_choices()]
            self.assertIn('test.txt', choices)
            self.assertIn(os.path.join('subdir', 'match.txt'), choices)
        
        finally:
            if os.path.exists(sub_file):
                os.remove(sub_file)
            if os.path.exists(sub_dir):
                os.rmdir(sub_dir)
