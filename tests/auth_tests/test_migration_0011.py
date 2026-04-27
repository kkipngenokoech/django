import pytest
from django.apps import apps
from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
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


class TestConcreteModel:
    """Mock concrete model for testing"""
    class _meta:
        proxy = False
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'
        
    _meta = _meta()


class MockApps:
    """Mock apps registry for testing"""
    def get_model(self, app_label, model_name):
        if app_label == 'auth' and model_name == 'Permission':
            return Permission
        elif app_label == 'contenttypes' and model_name == 'ContentType':
            return ContentType
        return None
    
    def get_models(self):
        return [TestModel]


def test_issue_reproduction():
    """Test that migration fails when permissions already exist for proxy model content type"""
    # Create content types for concrete and proxy models
    concrete_ct = ContentType.objects.get_or_create(
        app_label='testapp',
        model='testmodel'
    )[0]
    
    proxy_ct = ContentType.objects.get_or_create(
        app_label='testapp', 
        model='testmodel'
    )[0]
    
    # Create permission for concrete model
    concrete_perm = Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=concrete_ct
    )
    
    # Create permission for proxy model (simulating existing proxy permission)
    proxy_perm = Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model', 
        content_type=proxy_ct
    )
    
    # Mock apps registry
    mock_apps = MockApps()
    
    # This should raise IntegrityError due to duplicate key constraint
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            update_proxy_model_permissions(mock_apps, None, reverse=False)