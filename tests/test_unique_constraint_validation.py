import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.core.checks import run_checks
from django.test import TestCase
from django.apps import apps
from django.conf import settings


def test_issue_reproduction():
    """Test that UniqueConstraint should validate field existence like unique_together does."""
    
    # Configure Django if not already configured
    if not settings.configured:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            USE_TZ=True
        )
    
    # Create a model with UniqueConstraint referencing non-existent field
    class TestModelWithUniqueConstraint(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
            constraints = [
                models.UniqueConstraint(fields=['nonexistent_field'], name='test_unique')
            ]
    
    # Create a model with unique_together referencing non-existent field for comparison
    class TestModelWithUniqueTogether(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
            unique_together = [['nonexistent_field']]
    
    # Run checks on both models
    unique_constraint_errors = run_checks(tags=['models'], include_deployment_checks=False)
    
    # Filter errors for our test models
    constraint_errors = [error for error in unique_constraint_errors 
                        if hasattr(error.obj, '_meta') and 
                        error.obj._meta.object_name in ['TestModelWithUniqueConstraint', 'TestModelWithUniqueTogether']]
    
    # Check that unique_together raises E012 error
    unique_together_errors = [error for error in constraint_errors 
                             if error.obj._meta.object_name == 'TestModelWithUniqueTogether' and 
                             error.id == 'models.E012']
    
    # Check that UniqueConstraint should also raise similar error but currently doesn't
    unique_constraint_field_errors = [error for error in constraint_errors 
                                     if error.obj._meta.object_name == 'TestModelWithUniqueConstraint' and 
                                     'nonexistent_field' in str(error.msg)]
    
    # This assertion should fail because UniqueConstraint doesn't validate field existence
    # but unique_together does (showing the inconsistency)
    assert len(unique_together_errors) > 0, "unique_together should raise E012 for non-existent fields"
    assert len(unique_constraint_field_errors) > 0, "UniqueConstraint should also validate field existence like unique_together does"


class TestUniqueConstraintValidation(TestCase):
    """Test cases for UniqueConstraint field validation."""
    
    def test_unique_constraint_nonexistent_field(self):
        """Test that UniqueConstraint raises error for non-existent fields."""
        
        class TestModel(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'test_app'
                constraints = [
                    models.UniqueConstraint(fields=['nonexistent_field'], name='test_unique')
                ]
        
        errors = TestModel.check()
        
        # Should have at least one error for the non-existent field
        field_errors = [error for error in errors if 'nonexistent_field' in str(error.msg)]
        self.assertGreater(len(field_errors), 0)
        
        # Should be models.E012 error
        e012_errors = [error for error in errors if error.id == 'models.E012']
        self.assertGreater(len(e012_errors), 0)
    
    def test_unique_constraint_existing_field(self):
        """Test that UniqueConstraint doesn't raise error for existing fields."""
        
        class TestModel(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'test_app'
                constraints = [
                    models.UniqueConstraint(fields=['name'], name='test_unique')
                ]
        
        errors = TestModel.check()
        
        # Should have no errors for existing field
        field_errors = [error for error in errors if 'name' in str(error.msg) and 'nonexistent' in str(error.msg)]
        self.assertEqual(len(field_errors), 0)
    
    def test_unique_constraint_multiple_fields(self):
        """Test UniqueConstraint with multiple fields, some non-existent."""
        
        class TestModel(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'test_app'
                constraints = [
                    models.UniqueConstraint(fields=['name', 'nonexistent_field'], name='test_unique')
                ]
        
        errors = TestModel.check()
        
        # Should have error for non-existent field but not for existing field
        nonexistent_errors = [error for error in errors if 'nonexistent_field' in str(error.msg)]
        self.assertGreater(len(nonexistent_errors), 0)
        
        # Should not have error mentioning 'name' field as non-existent
        name_errors = [error for error in errors if 'name' in str(error.msg) and 'nonexistent' in str(error.msg)]
        self.assertEqual(len(name_errors), 0)
