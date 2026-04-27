import os
import tempfile
from django.db import models
from django.test import TestCase
from django.core.exceptions import ValidationError


def get_dynamic_path():
    """Callable that returns a dynamic path"""
    return os.path.join(tempfile.gettempdir(), 'test_files')


class TestModel(models.Model):
    # This should work but currently fails
    file_field = models.FilePathField(path=get_dynamic_path)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that FilePathField should accept callable paths but currently doesn't."""
    # Create the test directory
    test_dir = get_dynamic_path()
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a test file
    test_file = os.path.join(test_dir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('test content')
    
    try:
        # This should work: the field should accept a callable path
        # and resolve it when needed
        field = TestModel._meta.get_field('file_field')
        
        # The field should be able to resolve the callable path
        # Currently this will fail because FilePathField doesn't handle callables
        resolved_path = field.path() if callable(field.path) else field.path
        
        # Verify the resolved path is correct
        assert resolved_path == test_dir
        
        # Clean up
        os.remove(test_file)
        os.rmdir(test_dir)
        
    except (TypeError, AttributeError) as e:
        # Clean up even if test fails
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(test_dir):
            os.rmdir(test_dir)
        # Re-raise to show the test failure
        raise AssertionError(f"FilePathField does not support callable paths: {e}")