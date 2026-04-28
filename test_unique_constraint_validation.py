import pytest
from django.core.checks import run_checks
from django.db import models
from django.test import TestCase
from django.apps import apps
from django.conf import settings


def test_issue_reproduction():
    """Test that UniqueConstraint doesn't validate field existence like unique_together does."""
    
    # Configure Django if not already configured
    if not settings.configured:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            USE_TZ=True,
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
    
    # Run checks on the UniqueConstraint model
    unique_constraint_errors = run_checks(app_configs=None, tags=None, include_deployment_checks=False)
    unique_constraint_errors = [e for e in unique_constraint_errors if e.obj == TestModelWithUniqueConstraint]
    
    # Run checks on the unique_together model
    unique_together_errors = run_checks(app_configs=None, tags=None, include_deployment_checks=False)
    unique_together_errors = [e for e in unique_together_errors if e.obj == TestModelWithUniqueTogether and e.id == 'models.E012']
    
    # The bug: UniqueConstraint should raise an error for non-existent fields but doesn't
    # This assertion will FAIL on the current buggy code because no errors are raised
    assert len(unique_constraint_errors) > 0, "UniqueConstraint should validate field existence but doesn't"
    
    # Verify that unique_together does raise the expected error (this should pass)
    assert len(unique_together_errors) > 0, "unique_together should validate field existence"