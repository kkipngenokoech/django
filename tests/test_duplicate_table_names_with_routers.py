import pytest
from django.core.checks import Error, Warning
from django.core.checks.model_checks import check_all_models
from django.db import models
from django.test import TestCase, override_settings
from django.apps import AppConfig
from django.apps.registry import Apps


class TestApp1Config(AppConfig):
    name = 'test_app1'
    label = 'test_app1'


class TestApp2Config(AppConfig):
    name = 'test_app2'
    label = 'test_app2'


class TestModel1(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app1'
        db_table = 'shared_table'


class TestModel2(models.Model):
    title = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app2'
        db_table = 'shared_table'


def test_issue_reproduction():
    """Test that duplicate table names produce E028 error even with DATABASE_ROUTERS configured."""
    # Create a minimal apps registry with our test models
    test_apps = Apps()
    
    # Register our test app configs
    app1_config = TestApp1Config('test_app1', None)
    app2_config = TestApp2Config('test_app2', None)
    
    test_apps.populate([
        app1_config,
        app2_config,
    ])
    
    # Add our models to the apps
    TestModel1._meta.apps = test_apps
    TestModel2._meta.apps = test_apps
    app1_config.models = {'testmodel1': TestModel1}
    app2_config.models = {'testmodel2': TestModel2}
    
    # Mock the apps.get_models() to return our test models
    original_get_models = test_apps.get_models
    test_apps.get_models = lambda: [TestModel1, TestModel2]
    
    try:
        # Test with DATABASE_ROUTERS configured (should be warning, not error)
        with override_settings(DATABASE_ROUTERS=['myapp.routers.DatabaseRouter']):
            errors = check_all_models()
            
            # Find the E028 error about duplicate table names
            e028_errors = [e for e in errors if getattr(e, 'id', None) == 'models.E028']
            
            # The bug: this should be a Warning when DATABASE_ROUTERS is configured,
            # but currently it's still an Error
            assert len(e028_errors) == 1, f"Expected 1 E028 error, got {len(e028_errors)}"
            error = e028_errors[0]
            
            # This assertion will FAIL on the current buggy code because it returns Error instead of Warning
            assert isinstance(error, Warning), f"Expected Warning with DATABASE_ROUTERS configured, got {type(error).__name__}"
            assert "shared_table" in error.msg
            assert "test_app1.TestModel1" in error.msg
            assert "test_app2.TestModel2" in error.msg
            
        # Test without DATABASE_ROUTERS (should remain an error)
        with override_settings(DATABASE_ROUTERS=[]):
            errors = check_all_models()
            
            e028_errors = [e for e in errors if getattr(e, 'id', None) == 'models.E028']
            assert len(e028_errors) == 1
            error = e028_errors[0]
            
            # Without routers, it should still be an Error
            assert isinstance(error, Error)
            assert "shared_table" in error.msg
            
    finally:
        # Restore original method
        test_apps.get_models = original_get_models