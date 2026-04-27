import pytest
from django.test import TestCase
from django.db import models, IntegrityError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.db import migrations
from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'
        permissions = [('custom_perm', 'Custom Permission')]


class TestProxyModel(TestModel):
    class Meta:
        proxy = True
        app_label = 'test_app'


def test_issue_reproduction():
    """
    Test that migration 0011_update_proxy_permissions fails when permissions
    already exist for the target content_type, causing IntegrityError.
    """
    # Create content types for both concrete and proxy models
    concrete_ct = ContentType.objects.get_or_create(
        app_label='test_app',
        model='testmodel'
    )[0]
    
    proxy_ct = ContentType.objects.get_or_create(
        app_label='test_app', 
        model='testproxymodel'
    )[0]
    
    # Create permissions for the concrete model (simulating existing state)
    Permission.objects.get_or_create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=concrete_ct
    )
    Permission.objects.get_or_create(
        codename='change_testmodel', 
        name='Can change test model',
        content_type=concrete_ct
    )
    Permission.objects.get_or_create(
        codename='delete_testmodel',
        name='Can delete test model', 
        content_type=concrete_ct
    )
    Permission.objects.get_or_create(
        codename='custom_perm',
        name='Custom Permission',
        content_type=concrete_ct
    )
    
    # Create duplicate permissions for the proxy model content type
    # This simulates the scenario where permissions already exist for the target
    Permission.objects.get_or_create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=proxy_ct
    )
    Permission.objects.get_or_create(
        codename='change_testmodel',
        name='Can change test model', 
        content_type=proxy_ct
    )
    
    # Mock the apps.get_models() to return our test models
    class MockApps:
        def get_model(self, app_label, model_name):
            if app_label == 'auth' and model_name == 'Permission':
                return Permission
            elif app_label == 'contenttypes' and model_name == 'ContentType':
                return ContentType
            return None
            
        def get_models(self):
            return [TestModel, TestProxyModel]
    
    mock_apps = MockApps()
    
    # This should raise IntegrityError due to duplicate key constraint violation
    with pytest.raises(IntegrityError, match="duplicate key value violates unique constraint|UNIQUE constraint failed"):
        update_proxy_model_permissions(mock_apps, None, reverse=False)