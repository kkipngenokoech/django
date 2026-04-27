import pytest
from django.apps import apps
from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from django.db import transaction


class TestModel:
    """Mock model for testing"""
    class _meta:
        proxy = True
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'
        
    _meta = _meta()


class ConcreteTestModel:
    """Mock concrete model for testing"""
    class _meta:
        proxy = False
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'
        
    _meta = _meta()


def test_issue_reproduction():
    """Test that migration fails when permissions already exist for both concrete and proxy models"""
    # Create content types for both concrete and proxy models
    concrete_ct = ContentType.objects.create(
        app_label='testapp',
        model='testmodel'
    )
    proxy_ct = ContentType.objects.create(
        app_label='testapp', 
        model='testmodel_proxy'
    )
    
    # Create permission that exists for concrete model (simulating existing state)
    concrete_perm = Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=concrete_ct
    )
    
    # Create permission that already exists for proxy model (simulating the duplicate)
    proxy_perm = Permission.objects.create(
        codename='add_testmodel', 
        name='Can add test model',
        content_type=proxy_ct
    )
    
    # Mock apps.get_models to return our test model
    class MockApps:
        def get_model(self, app_label, model_name):
            if app_label == 'auth' and model_name == 'Permission':
                return Permission
            elif app_label == 'contenttypes' and model_name == 'ContentType':
                return ContentType
            return None
            
        def get_models(self):
            return [TestModel]
    
    # Mock ContentType.objects.get_for_model to return our content types
    original_get_for_model = ContentType.objects.get_for_model
    def mock_get_for_model(model, for_concrete_model=True):
        if for_concrete_model:
            return concrete_ct
        else:
            return proxy_ct
    
    ContentType.objects.get_for_model = mock_get_for_model
    
    try:
        # This should raise IntegrityError due to duplicate key constraint
        with pytest.raises(IntegrityError):
            update_proxy_model_permissions(MockApps(), None, reverse=False)
    finally:
        # Restore original method
        ContentType.objects.get_for_model = original_get_for_model
        # Clean up
        Permission.objects.filter(id__in=[concrete_perm.id, proxy_perm.id]).delete()
        ContentType.objects.filter(id__in=[concrete_ct.id, proxy_ct.id]).delete()