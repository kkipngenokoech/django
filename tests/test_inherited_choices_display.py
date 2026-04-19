import pytest
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that get_FOO_display() works correctly with inherited choices."""
    
    class A(models.Model):
        foo_choice = [("A", "output1"), ("B", "output2")]
        field_foo = models.CharField(max_length=254, choices=foo_choice)
        
        class Meta:
            abstract = True
    
    class B(A):
        foo_choice = [("A", "output1"), ("B", "output2"), ("C", "output3")]
        field_foo = models.CharField(max_length=254, choices=foo_choice)
        
        class Meta:
            app_label = 'test_app'
    
    # Create an instance of B with value "C"
    instance = B(field_foo="C")
    
    # This should return "output3" but currently returns "C"
    result = instance.get_field_foo_display()
    
    # The test should fail because the current implementation returns "C" instead of "output3"
    assert result == "output3", f"Expected 'output3' but got '{result}'"