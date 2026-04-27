import pytest
from django.apps import apps
from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from django.db import transaction


class ProxyModel(TestCase.Meta if hasattr(TestCase, 'Meta') else object):
    """A simple proxy model for testing"""
    class Meta:
        proxy = True
        app_label = 'auth'


class TestProxyModel(TestCase):
    """Concrete model that will have a proxy"""
    class Meta:
        app_label = 'auth'


def test_issue_reproduction():
    """Test that reproduces the IntegrityError when updating proxy permissions with duplicates."""
    # Create a mock apps registry that includes our test models
    from django.apps.registry import Apps
    from django.db import models
    
    # Create test models
    class ConcreteTestModel(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'auth'
    
    class ProxyTestModel(ConcreteTestModel):
        class Meta:
            proxy = True
            app_label = 'auth'
    
    # Mock the apps.get_models() to return our test models
    original_get_models = apps.get_models
    
    def mock_get_models():
        return [ProxyTestModel]
    
    apps.get_models = mock_get_models
    
    try:
        # Get content types for both concrete and proxy models
        concrete_ct = ContentType.objects.get_or_create(
            app_label='auth',
            model='concretetestmodel'
        )[0]
        
        proxy_ct = ContentType.objects.get_or_create(
            app_label='auth', 
            model='proxytestmodel'
        )[0]
        
        # Create permissions for both content types with same codename
        # This simulates the scenario where permissions exist for both
        Permission.objects.get_or_create(
            codename='add_proxytestmodel',
            name='Can add proxy test model',
            content_type=concrete_ct
        )
        
        Permission.objects.get_or_create(
            codename='add_proxytestmodel', 
            name='Can add proxy test model',
            content_type=proxy_ct
        )
        
        # Now run the migration function - this should fail with IntegrityError
        with pytest.raises(IntegrityError):
            update_proxy_model_permissions(apps, None)
            
    finally:
        # Restore original get_models
        apps.get_models = original_get_models
        
        # Clean up created objects
        Permission.objects.filter(codename='add_proxytestmodel').delete()
        ContentType.objects.filter(model__in=['concretetestmodel', 'proxytestmodel']).delete()