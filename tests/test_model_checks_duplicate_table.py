import pytest
from django.apps import apps
from django.core.checks import Error
from django.core.checks.model_checks import check_all_models
from django.db import models
from django.test import TestCase, override_settings
from django.apps import AppConfig


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
    """Test that models from different apps with same table name trigger E028 error."""
    # Register the test models temporarily
    test_app1_config = TestApp1Config('test_app1', None)
    test_app2_config = TestApp2Config('test_app2', None)
    
    # Add models to the app configs
    test_app1_config.models = {'testmodel1': TestModel1}
    test_app2_config.models = {'testmodel2': TestModel2}
    
    # Mock the apps registry to include our test models
    original_get_models = apps.get_models
    
    def mock_get_models():
        return [TestModel1, TestModel2]
    
    apps.get_models = mock_get_models
    
    try:
        # Run the check that should detect the duplicate table names
        errors = check_all_models()
        
        # The bug is that this check fails even when models use different databases
        # We expect to find the E028 error about duplicate db_table usage
        e028_errors = [error for error in errors if error.id == 'models.E028']
        
        assert len(e028_errors) == 1, f"Expected 1 E028 error, got {len(e028_errors)}"
        
        error = e028_errors[0]
        assert 'shared_table' in error.msg
        assert 'test_app1.TestModel1' in error.msg
        assert 'test_app2.TestModel2' in error.msg
        
    finally:
        # Restore original method
        apps.get_models = original_get_models