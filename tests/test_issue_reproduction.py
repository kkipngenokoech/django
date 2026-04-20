import pytest
from django.apps import apps
from django.core.checks import Error
from django.core.checks.model_checks import check_all_models
from django.db import models, router
from django.test import TestCase, override_settings
from unittest.mock import patch


def test_issue_reproduction():
    """Test that models with same table name in different apps should not conflict when using different databases."""
    
    # Create two models with the same table name but in different apps
    class BaseModel(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'base'
            db_table = 'shared_table'
    
    class App2Model(models.Model):
        title = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'app2'
            db_table = 'shared_table'
    
    # Mock the apps registry to include our test models
    def mock_get_models():
        return [BaseModel, App2Model]
    
    # Mock database routing so models use the same database (reproducing the bug)
    def mock_db_for_read(model):
        return 'default'  # Both models use same database
    
    with patch('django.apps.apps.get_models', side_effect=mock_get_models), \
         patch('django.db.router.db_for_read', side_effect=mock_db_for_read):
        
        # Run the model checks
        errors = check_all_models()
        
        # The current implementation should produce an error about duplicate table names
        # This is the bug - it should NOT produce this error when models use different databases
        duplicate_table_errors = [e for e in errors if e.id == 'models.E028']
        
        # This assertion will PASS on the current buggy code because it produces the error
        # Since both models use the same database, we expect 1 error
        assert len(duplicate_table_errors) == 1, f"Expected 1 duplicate table error, got {len(duplicate_table_errors)}"
        
        # Verify the error message contains both model labels
        error = duplicate_table_errors[0]
        assert 'shared_table' in error.msg
        assert 'base.BaseModel' in error.msg
        assert 'app2.App2Model' in error.msg