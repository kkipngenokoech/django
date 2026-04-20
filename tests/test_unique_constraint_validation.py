import pytest
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase
from django.core.management.validation import get_validation_errors
from django.apps import apps
from django.conf import settings
from django.test.utils import override_settings
from io import StringIO


def test_issue_reproduction():
    """Test that UniqueConstraint should validate field existence like unique_together does."""
    
    # Configure minimal Django settings if not already configured
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
            unique_together = [('nonexistent_field',)]
    
    # Test that unique_together validation catches the error
    unique_together_errors = []
    try:
        TestModelWithUniqueTogether._meta._expire_cache()
        TestModelWithUniqueTogether.check()
    except Exception as e:
        unique_together_errors = [str(e)]
    
    # Test that UniqueConstraint validation should also catch the error but doesn't
    unique_constraint_errors = []
    try:
        TestModelWithUniqueConstraint._meta._expire_cache()
        TestModelWithUniqueConstraint.check()
    except Exception as e:
        unique_constraint_errors = [str(e)]
    
    # The bug: unique_together catches field validation errors but UniqueConstraint doesn't
    # This assertion will fail because UniqueConstraint doesn't validate fields
    assert len(unique_constraint_errors) > 0, "UniqueConstraint should validate field existence but doesn't"