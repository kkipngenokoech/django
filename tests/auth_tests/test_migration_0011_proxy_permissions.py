import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase
from django.apps import apps
from importlib import import_module

update_proxy_permissions = import_module('django.contrib.auth.migrations.0011_update_proxy_permissions')


class TestModel:
    """Mock model for testing"""
    class _meta:
        proxy = False
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'test_app'
        
    _meta = _meta()


class TestProxyModel:
    """Mock proxy model for testing"""
    class _meta:
        proxy = True
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'test_app'
        
    _meta = _meta()


def test_issue_reproduction():
    """Test that migration fails when permissions already exist for both concrete and proxy models"""
    # Create content types for concrete and proxy models
    concrete_ct = ContentType.objects.create(
        app_label='test_app',
        model='testmodel'
    )
    proxy_ct = ContentType.objects.create(
        app_label='test_app', 
        model='testmodel_proxy'
    )
    
    # Create permissions for concrete model (existing state)
    Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=concrete_ct
    )
    
    # Create permissions for proxy model (target state - this causes the conflict)
    Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=proxy_ct
    )
    
    # Mock apps.get_models() to return our test models
    class MockApps:
        def get_model(self, app_label, model_name):
            if model_name == 'Permission':
                return Permission
            elif model_name == 'ContentType':
                return ContentType
            
        def get_models(self):
            return [TestProxyModel]
    
    # Mock ContentType.objects.get_for_model to return our content types
    original_get_for_model = ContentType.objects.get_for_model
    def mock_get_for_model(model, for_concrete_model=True):
        if for_concrete_model:
            return concrete_ct
        else:
            return proxy_ct
    
    ContentType.objects.get_for_model = mock_get_for_model
    
    try:
        # This should raise IntegrityError due to duplicate permissions
        with pytest.raises(IntegrityError):
            update_proxy_permissions.update_proxy_model_permissions(MockApps(), None, reverse=False)
    finally:
        # Restore original method
        ContentType.objects.get_for_model = original_get_for_model