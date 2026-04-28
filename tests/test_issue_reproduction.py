import pytest
from django.core.checks import Error, Warning
from django.core.checks.model_checks import check_all_models
from django.db import models
from django.apps import AppConfig
from django.test import override_settings
from django.apps.registry import Apps


def test_issue_reproduction():
    """Test that models with same db_table raise E028 error even with DATABASE_ROUTERS configured."""
    
    # Create a temporary apps registry
    apps = Apps()
    
    # Create two app configs
    class BaseAppConfig(AppConfig):
        name = 'base'
        label = 'base'
        
    class App2Config(AppConfig):
        name = 'app2'
        label = 'app2'
    
    base_app = BaseAppConfig('base', apps)
    app2_app = App2Config('app2', apps)
    
    apps.app_configs = {
        'base': base_app,
        'app2': app2_app,
    }
    
    # Create two models with the same db_table
    class BaseModel(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'base'
            db_table = 'shared_table'
            managed = True
    
    class App2Model(models.Model):
        title = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'app2'
            db_table = 'shared_table'
            managed = True
    
    # Register models with apps
    base_app.models = {'basemodel': BaseModel}
    app2_app.models = {'app2model': App2Model}
    apps.all_models = {
        'base': {'basemodel': BaseModel},
        'app2': {'app2model': App2Model},
    }
    
    # Mock the apps.get_models() to return our test models
    original_get_models = apps.get_models
    apps.get_models = lambda: [BaseModel, App2Model]
    
    try:
        # Test with DATABASE_ROUTERS configured - should be warning but currently is error
        with override_settings(DATABASE_ROUTERS=['myapp.routers.DatabaseRouter']):
            errors = check_all_models()
            
            # Find the E028 error
            e028_errors = [e for e in errors if getattr(e, 'id', None) == 'models.E028']
            
            # This assertion will FAIL on current code because it returns Error instead of Warning
            # The bug is that even with DATABASE_ROUTERS configured, it still raises E028 error
            # instead of converting it to a warning
            assert len(e028_errors) == 1, "Expected exactly one E028 error"
            error = e028_errors[0]
            
            # Current code incorrectly returns Error - this should be Warning when DATABASE_ROUTERS is set
            assert isinstance(error, Warning), f"Expected Warning but got {type(error).__name__} when DATABASE_ROUTERS is configured"
            assert "db_table 'shared_table' is used by multiple models: base.BaseModel, app2.App2Model" in str(error.msg)
            
    finally:
        # Restore original method
        apps.get_models = original_get_models