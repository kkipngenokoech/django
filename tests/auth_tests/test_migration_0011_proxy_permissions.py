import pytest
from django.apps import apps
from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase


class TestModel:
    """Mock model for testing"""
    class _meta:
        proxy = False
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'
        
        
class TestProxyModel:
    """Mock proxy model for testing"""
    class _meta:
        proxy = True
        model_name = 'testproxymodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'


def test_issue_reproduction():
    """Test that migration fails when permissions exist for both concrete and proxy models"""
    # Create content types for concrete and proxy models
    concrete_ct = ContentType.objects.create(
        app_label='testapp',
        model='testmodel'
    )
    proxy_ct = ContentType.objects.create(
        app_label='testapp', 
        model='testproxymodel'
    )
    
    # Create permission for concrete model
    concrete_perm = Permission.objects.create(
        name='Can add test model',
        content_type=concrete_ct,
        codename='add_testproxymodel'  # Same codename as proxy would have
    )
    
    # Create permission for proxy model (this creates the duplicate scenario)
    proxy_perm = Permission.objects.create(
        name='Can add test proxy model',
        content_type=proxy_ct,
        codename='add_testproxymodel'
    )
    
    # Mock apps.get_models to return our test proxy model
    class MockApps:
        def get_model(self, app_label, model_name):
            if app_label == 'auth' and model_name == 'Permission':
                return Permission
            elif app_label == 'contenttypes' and model_name == 'ContentType':
                return ContentType
            return None
            
        def get_models(self):
            # Return a proxy model that will trigger the migration logic
            proxy_model = type('TestProxyModel', (), {
                '_meta': type('Meta', (), {
                    'proxy': True,
                    'model_name': 'testproxymodel',
                    'default_permissions': ('add', 'change', 'delete', 'view'),
                    'permissions': ()
                })()
            })
            return [proxy_model]
    
    # Mock ContentType.objects.get_for_model
    original_get_for_model = ContentType.objects.get_for_model
    def mock_get_for_model(model, for_concrete_model=True):
        if for_concrete_model:
            return concrete_ct
        else:
            return proxy_ct
    
    ContentType.objects.get_for_model = mock_get_for_model
    
    try:
        # This should raise IntegrityError due to duplicate key constraint
        with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint"):
            update_proxy_model_permissions(MockApps(), None)
    finally:
        # Restore original method
        ContentType.objects.get_for_model = original_get_for_model
        # Clean up
        Permission.objects.filter(id__in=[concrete_perm.id, proxy_perm.id]).delete()
        ContentType.objects.filter(id__in=[concrete_ct.id, proxy_ct.id]).delete()