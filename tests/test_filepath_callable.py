import os
import tempfile
from django.db import models
from django.test import TestCase
from django.core.management import call_command
from django.db import connection
from django.apps import apps
from django.conf import settings


def get_dynamic_path():
    """A callable that returns a path - this should work but currently doesn't"""
    return os.path.join(tempfile.gettempdir(), 'test_files')


class TestModel(models.Model):
    # This should work but currently fails
    file_field = models.FilePathField(path=get_dynamic_path)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that FilePathField should accept callable path parameter"""
    # Create a temporary directory for testing
    test_dir = os.path.join(tempfile.gettempdir(), 'test_files')
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a test file
    test_file = os.path.join(test_dir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('test content')
    
    try:
        # This should work - the field should accept a callable for path
        # and evaluate it when needed, but currently it will fail
        field = TestModel._meta.get_field('file_field')
        
        # The path should be callable and when accessed, should return the actual path
        if callable(field.path):
            actual_path = field.path()
        else:
            actual_path = field.path
            
        # This should be the resolved path from our callable
        expected_path = get_dynamic_path()
        assert actual_path == expected_path, f"Expected {expected_path}, got {actual_path}"
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)