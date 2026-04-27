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
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app2'
        db_table = 'shared_table'


def test_issue_reproduction():
    """Test that models from different apps can have the same db_table when using different databases."""
    # Register our test models temporarily
    apps.register_model('test_app1', TestModel1)
    apps.register_model('test_app2', TestModel2)
    
    try:
        # Run the model checks
        errors = check_all_models()
        
        # Filter for the specific error we're testing
        table_name_errors = [e for e in errors if e.id == 'models.E028']
        
        # The bug is that this check fails even when models use different databases
        # In a properly fixed version, this should not produce an error when models
        # are routed to different databases, but currently it does
        assert len(table_name_errors) == 1
        assert 'shared_table' in table_name_errors[0].msg
        assert 'test_app1.TestModel1' in table_name_errors[0].msg
        assert 'test_app2.TestModel2' in table_name_errors[0].msg
        
    finally:
        # Clean up - unregister the test models
        if 'test_app1' in apps.all_models:
            del apps.all_models['test_app1']['testmodel1']
        if 'test_app2' in apps.all_models:
            del apps.all_models['test_app2']['testmodel2']