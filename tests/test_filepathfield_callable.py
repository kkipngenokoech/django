import os
import tempfile
from django.db import models
from django.forms import forms
from django.test import TestCase


def get_dynamic_path():
    """A callable that returns a path dynamically"""
    return os.path.join(tempfile.gettempdir(), 'test_files')


def test_issue_reproduction():
    """Test that FilePathField accepts a callable for the path parameter."""
    
    # Create a temporary directory structure for testing
    test_dir = get_dynamic_path()
    os.makedirs(test_dir, exist_ok=True)
    
    # Create some test files
    test_file1 = os.path.join(test_dir, 'file1.txt')
    test_file2 = os.path.join(test_dir, 'file2.txt')
    
    with open(test_file1, 'w') as f:
        f.write('test content 1')
    with open(test_file2, 'w') as f:
        f.write('test content 2')
    
    try:
        # Test 1: Model field should accept callable path
        class TestModel(models.Model):
            # This should work but currently fails - path should accept a callable
            file_field = models.FilePathField(path=get_dynamic_path)
            
            class Meta:
                app_label = 'test'
        
        # Test 2: Form field should also accept callable path
        class TestForm(forms.Form):
            # This should also work but currently fails
            file_field = forms.FilePathField(path=get_dynamic_path)
        
        # Test 3: The callable should be called to get the actual path
        form = TestForm()
        
        # The form field should resolve the callable and find our test files
        choices = form.fields['file_field'].choices
        choice_values = [choice[0] for choice in choices]
        
        # Should find our test files in the dynamically resolved path
        assert any('file1.txt' in choice for choice in choice_values), f"file1.txt not found in choices: {choice_values}"
        assert any('file2.txt' in choice for choice in choice_values), f"file2.txt not found in choices: {choice_values}"
        
        # Test 4: Model field deconstruction should preserve callable
        field_instance = TestModel._meta.get_field('file_field')
        name, path, args, kwargs = field_instance.deconstruct()
        
        # The deconstructed field should preserve the callable, not resolve it to a string
        assert callable(kwargs.get('path')), f"Expected callable path in deconstruction, got: {kwargs.get('path')}"
        assert kwargs['path'] == get_dynamic_path, "Callable should be preserved exactly in deconstruction"
        
    finally:
        # Clean up test files
        try:
            os.unlink(test_file1)
            os.unlink(test_file2)
            os.rmdir(test_dir)
        except OSError:
            pass