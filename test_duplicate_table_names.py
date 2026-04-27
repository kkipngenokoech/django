import pytest
from django.apps import apps
from django.core.checks import run_checks
from django.core.checks.model_checks import check_all_models
from django.db import models, router
from django.test import TestCase, override_settings


def test_issue_reproduction():
    """Test that models with same db_table in different apps targeting different databases should not raise E028 error."""
    
    # Create two test models with the same db_table name
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
    original_get_models = apps.get_models
    original_db_for_read = router.db_for_read
    
    def mock_get_models():
        return [BaseModel, App2Model]
    
    def mock_db_for_read(model):
        if model._meta.label == 'base.BaseModel':
            return 'central_db'
        elif model._meta.label == 'app2.App2Model':
            return 'app2_db'
        return 'default'
    
    apps.get_models = mock_get_models
    router.db_for_read = mock_db_for_read
    
    try:
        # Run the model checks
        errors = check_all_models()
        
        # Filter for the specific error we're testing
        e028_errors = [error for error in errors if error.id == 'models.E028']
        
        # The bug is that this raises an E028 error even when models target different databases
        # This assertion will FAIL on the current buggy code because it incorrectly reports the error
        assert len(e028_errors) == 0, f"Expected no E028 errors but got: {e028_errors}"
        
    finally:
        # Restore original methods
        apps.get_models = original_get_models
        router.db_for_read = original_db_for_read