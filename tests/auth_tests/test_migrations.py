import pytest
from django.apps import apps
from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase


class TestModel:
    """Mock model for testing proxy permissions migration."""
    class _meta:
        proxy = True
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'
        
    _meta = _meta()


class ConcreteModel:
    """Mock concrete model for testing proxy permissions migration."""
    class _meta:
        proxy = False
        model_name = 'testmodel'
        default_permissions = ('add', 'change', 'delete', 'view')
        permissions = ()
        app_label = 'testapp'
        
    _meta = _meta()


class MockApps:
    """Mock apps registry for testing."""
    def __init__(self, models):
        self.models = models
        
    def get_models(self):
        return self.models
        
    def get_model(self, app_label, model_name):
        if app_label == 'auth' and model_name == 'Permission':
            return Permission
        elif app_label == 'contenttypes' and model_name == 'ContentType':
            return ContentType
        return None


class TestProxyPermissionsMigration(TransactionTestCase):
    """Test the proxy permissions migration handles duplicate permissions correctly."""
    
    def setUp(self):
        # Create content types for concrete and proxy models
        self.concrete_ct = ContentType.objects.create(
            app_label='testapp',
            model='testmodel'
        )
        self.proxy_ct = ContentType.objects.create(
            app_label='testapp', 
            model='testmodel_proxy'
        )
        
    def test_issue_reproduction(self):
        """Test that migration fails when duplicate permissions exist."""
        # Create permissions for the concrete model
        concrete_perm = Permission.objects.create(
            name='Can add test model',
            content_type=self.concrete_ct,
            codename='add_testmodel'
        )
        
        # Create the same permission for the proxy model (simulating existing duplicate)
        proxy_perm = Permission.objects.create(
            name='Can add test model',
            content_type=self.proxy_ct,
            codename='add_testmodel'
        )
        
        # Mock the apps registry
        test_model = TestModel()
        mock_apps = MockApps([test_model])
        
        # Mock ContentType.objects.get_for_model to return our test content types
        original_get_for_model = ContentType.objects.get_for_model
        
        def mock_get_for_model(model, for_concrete_model=True):
            if for_concrete_model:
                return self.concrete_ct
            else:
                return self.proxy_ct
                
        ContentType.objects.get_for_model = mock_get_for_model
        
        try:
            # This should fail with IntegrityError due to duplicate permissions
            with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint"):
                with transaction.atomic():
                    update_proxy_model_permissions(mock_apps, None, reverse=False)
        finally:
            # Restore original method
            ContentType.objects.get_for_model = original_get_for_model