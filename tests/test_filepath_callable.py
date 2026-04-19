import os
import tempfile
from django.db import models
from django.forms import ModelForm
from django.test import TestCase


def get_dynamic_path():
    """Callable that returns a dynamic path"""
    return tempfile.gettempdir()


class TestModel(models.Model):
    """Test model with FilePathField using callable path"""
    name = models.CharField(max_length=100)
    file_path = models.FilePathField(path=get_dynamic_path)
    
    class Meta:
        app_label = 'test'


class TestForm(ModelForm):
    class Meta:
        model = TestModel
        fields = ['name', 'file_path']


def test_issue_reproduction():
    """Test that FilePathField accepts a callable for path parameter"""
    # Create a temporary directory and file for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # Override the callable to return our test directory
        original_func = get_dynamic_path
        def mock_get_dynamic_path():
            return temp_dir
        
        # Replace the function globally
        import sys
        current_module = sys.modules[__name__]
        setattr(current_module, 'get_dynamic_path', mock_get_dynamic_path)
        
        try:
            # Try to create a form instance - this should work if callable paths are supported
            form = TestForm()
            
            # The form field should have the correct path from the callable
            field = form.fields['file_path']
            
            # This will fail on current code because path is resolved at definition time
            # and stored as a string, not kept as a callable
            assert callable(TestModel._meta.get_field('file_path').path), "FilePathField path should remain callable"
            
        finally:
            # Restore original function
            setattr(current_module, 'get_dynamic_path', original_func)