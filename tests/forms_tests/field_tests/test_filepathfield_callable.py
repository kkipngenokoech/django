import os
import tempfile
import unittest
from unittest import mock

from django.forms import FilePathField
from django.test import SimpleTestCase


class FilePathFieldCallableTests(SimpleTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: os.rmdir(self.temp_dir) if os.path.exists(self.temp_dir) else None)
        
        # Create test files
        self.test_file1 = os.path.join(self.temp_dir, 'test1.txt')
        self.test_file2 = os.path.join(self.temp_dir, 'test2.txt')
        
        with open(self.test_file1, 'w') as f:
            f.write('test')
        with open(self.test_file2, 'w') as f:
            f.write('test')
        
        self.addCleanup(lambda: os.unlink(self.test_file1) if os.path.exists(self.test_file1) else None)
        self.addCleanup(lambda: os.unlink(self.test_file2) if os.path.exists(self.test_file2) else None)

    def test_callable_path_basic(self):
        """Test that FilePathField accepts a callable path."""
        def get_path():
            return self.temp_dir
        
        field = FilePathField(path=get_path)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_none_return(self):
        """Test that callable returning None is handled gracefully."""
        def get_path():
            return None
        
        field = FilePathField(path=get_path)
        self.assertIsNone(field._get_path())
        choices = field._get_choices()
        self.assertEqual(choices, [])

    def test_callable_path_dynamic_evaluation(self):
        """Test that callable path is evaluated each time it's accessed."""
        counter = {'value': 0}
        
        def get_path():
            counter['value'] += 1
            return self.temp_dir
        
        field = FilePathField(path=get_path)
        
        # Call _get_path multiple times
        field._get_path()
        field._get_path()
        
        self.assertEqual(counter['value'], 2)

    def test_string_path_still_works(self):
        """Test backward compatibility with string paths."""
        field = FilePathField(path=self.temp_dir)
        self.assertEqual(field._get_path(), self.temp_dir)

    def test_callable_path_with_choices(self):
        """Test that callable path works with choice generation."""
        def get_path():
            return self.temp_dir
        
        field = FilePathField(path=get_path, allow_files=True)
        choices = field._get_choices()
        
        # Should find our test files
        choice_values = [choice[0] for choice in choices]
        self.assertIn(self.test_file1, choice_values)
        self.assertIn(self.test_file2, choice_values)

    def test_callable_path_with_match_pattern(self):
        """Test callable path with match pattern."""
        def get_path():
            return self.temp_dir
        
        field = FilePathField(path=get_path, match=r'.*1\.txt$', allow_files=True)
        choices = field._get_choices()
        
        # Should only find test1.txt
        choice_values = [choice[0] for choice in choices]
        self.assertIn(self.test_file1, choice_values)
        self.assertNotIn(self.test_file2, choice_values)

    def test_callable_path_recursive(self):
        """Test callable path with recursive option."""
        # Create subdirectory with file
        subdir = os.path.join(self.temp_dir, 'subdir')
        os.makedirs(subdir)
        subfile = os.path.join(subdir, 'subfile.txt')
        with open(subfile, 'w') as f:
            f.write('test')
        
        self.addCleanup(lambda: os.unlink(subfile) if os.path.exists(subfile) else None)
        self.addCleanup(lambda: os.rmdir(subdir) if os.path.exists(subdir) else None)
        
        def get_path():
            return self.temp_dir
        
        field = FilePathField(path=get_path, recursive=True, allow_files=True)
        choices = field._get_choices()
        
        # Should find files in subdirectory too
        choice_values = [choice[0] for choice in choices]
        self.assertIn(subfile, choice_values)

    def test_callable_path_allow_folders(self):
        """Test callable path with allow_folders option."""
        # Create subdirectory
        subdir = os.path.join(self.temp_dir, 'subdir')
        os.makedirs(subdir)
        self.addCleanup(lambda: os.rmdir(subdir) if os.path.exists(subdir) else None)
        
        def get_path():
            return self.temp_dir
        
        field = FilePathField(path=get_path, allow_folders=True, allow_files=False)
        choices = field._get_choices()
        
        # Should find the subdirectory
        choice_values = [choice[0] for choice in choices]
        self.assertIn(subdir, choice_values)
        # Should not find files
        self.assertNotIn(self.test_file1, choice_values)

    @mock.patch('os.listdir')
    def test_callable_path_os_error_handling(self, mock_listdir):
        """Test that OSError is handled gracefully when path is callable."""
        mock_listdir.side_effect = OSError("Permission denied")
        
        def get_path():
            return '/nonexistent/path'
        
        field = FilePathField(path=get_path)
        choices = field._get_choices()
        
        # Should return empty list on OSError
        self.assertEqual(choices, [])

    def test_callable_path_validation(self):
        """Test that field validation works with callable paths."""
        def get_path():
            return self.temp_dir
        
        field = FilePathField(path=get_path, allow_files=True)
        
        # Valid file path should validate
        field.clean(self.test_file1)
        
        # Invalid path should raise ValidationError
        with self.assertRaises(Exception):  # ValidationError
            field.clean('/nonexistent/file.txt')
