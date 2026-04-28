import pytest
from django.core.checks import Error
from django.db import models
from django.test import TestCase


def test_issue_reproduction():
    """Test that CharField validates max_length against choice values."""
    
    # Test case 1: Simple choices where max_length is too small
    class TestModel1(models.Model):
        field = models.CharField(
            max_length=2,
            choices=[
                ('short', 'Short'),
                ('very_long_choice', 'Very Long Choice'),  # This is 17 chars, exceeds max_length=2
            ]
        )
        
        class Meta:
            app_label = 'test'
    
    # Test case 2: Named groups with choices where max_length is too small
    class TestModel2(models.Model):
        field = models.CharField(
            max_length=5,
            choices=[
                ('Group 1', [
                    ('short', 'Short'),
                    ('medium', 'Medium'),
                ]),
                ('Group 2', [
                    ('extremely_long_choice_value', 'Extremely Long'),  # This is 29 chars, exceeds max_length=5
                    ('ok', 'OK'),
                ]),
            ]
        )
        
        class Meta:
            app_label = 'test'
    
    # Test case 3: Valid case - max_length is sufficient
    class TestModel3(models.Model):
        field = models.CharField(
            max_length=20,
            choices=[
                ('short', 'Short'),
                ('medium_length', 'Medium Length'),  # This is 13 chars, fits in max_length=20
            ]
        )
        
        class Meta:
            app_label = 'test'
    
    # Check the fields - these should fail for models 1 and 2, pass for model 3
    field1 = TestModel1._meta.get_field('field')
    field2 = TestModel2._meta.get_field('field')
    field3 = TestModel3._meta.get_field('field')
    
    errors1 = field1.check()
    errors2 = field2.check()
    errors3 = field3.check()
    
    # The current implementation should NOT catch these errors (test should fail)
    # After the fix, these assertions should pass:
    
    # Model 1 should have an error about 'very_long_choice' being too long
    choice_length_errors1 = [e for e in errors1 if 'max_length' in str(e.msg) and 'choice' in str(e.msg)]
    assert len(choice_length_errors1) > 0, "Expected validation error for choice value exceeding max_length in simple choices"
    
    # Model 2 should have an error about 'extremely_long_choice_value' being too long  
    choice_length_errors2 = [e for e in errors2 if 'max_length' in str(e.msg) and 'choice' in str(e.msg)]
    assert len(choice_length_errors2) > 0, "Expected validation error for choice value exceeding max_length in named groups"
    
    # Model 3 should have no such errors
    choice_length_errors3 = [e for e in errors3 if 'max_length' in str(e.msg) and 'choice' in str(e.msg)]
    assert len(choice_length_errors3) == 0, "Expected no validation errors when all choices fit within max_length"