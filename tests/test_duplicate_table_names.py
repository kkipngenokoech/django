import pytest
from django.apps import apps
from django.core.checks import run_checks
from django.core.checks.model_checks import check_all_models
from django.db import models
from django.test import TestCase, override_settings
from django.apps import AppConfig
from django.apps.registry import Apps


def test_issue_reproduction():
    """Test that models with same table name in different apps cause E028 error."""
    
    # Create a minimal apps registry for testing
    test_apps = Apps()
    
    # Create two app configs
    class BaseAppConfig(AppConfig):
        name = 'base'
        label = 'base'
        
    class App2Config(AppConfig):
        name = 'app2'
        label = 'app2'
    
    base_app = BaseAppConfig('base', test_apps)
    app2_app = App2Config('app2', test_apps)
    
    test_apps.app_configs = {
        'base': base_app,
        'app2': app2_app
    }
    
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
    
    # Register models with the test apps
    test_apps.register_model('base', BaseModel)
    test_apps.register_model('app2', App2Model)
    
    # Mock the apps.get_models() to return our test models
    original_get_models = apps.get_models
    apps.get_models = lambda: [BaseModel, App2Model]
    
    try:
        # Run the check that should fail
        errors = check_all_models()
        
        # The bug: this should find an E028 error about duplicate table names
        e028_errors = [error for error in errors if error.id == 'models.E028']
        
        # This assertion will PASS on buggy code (demonstrating the bug exists)
        assert len(e028_errors) == 1
        assert 'shared_table' in e028_errors[0].msg
        assert 'base.BaseModel' in e028_errors[0].msg
        assert 'app2.App2Model' in e028_errors[0].msg
        
    finally:
        # Restore original function
        apps.get_models = original_get_models