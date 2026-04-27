#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ],
        SECRET_KEY='test-secret-key',
    )

django.setup()

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection, IntegrityError
from django.core.management import execute_from_command_line
from importlib import import_module

# Create tables
with connection.schema_editor() as schema_editor:
    schema_editor.create_model(ContentType)
    schema_editor.create_model(Permission)

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
    print("Creating content types...")
    
    # Create content types for concrete and proxy models
    concrete_ct = ContentType.objects.create(
        app_label='test_app',
        model='testmodel'
    )
    proxy_ct = ContentType.objects.create(
        app_label='test_app', 
        model='testmodel_proxy'
    )
    
    print(f"Created concrete content type: {concrete_ct}")
    print(f"Created proxy content type: {proxy_ct}")
    
    # Create permissions for concrete model (existing state)
    perm1 = Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=concrete_ct
    )
    
    # Create permissions for proxy model (target state - this causes the conflict)
    perm2 = Permission.objects.create(
        codename='add_testmodel',
        name='Can add test model',
        content_type=proxy_ct
    )
    
    print(f"Created permission for concrete model: {perm1}")
    print(f"Created permission for proxy model: {perm2}")
    
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
        print("Running migration...")
        # This should raise IntegrityError due to duplicate permissions
        update_proxy_permissions.update_proxy_model_permissions(MockApps(), None, reverse=False)
        print("Migration completed successfully - this should not happen!")
        return False
    except IntegrityError as e:
        print(f"IntegrityError raised as expected: {e}")
        return True
    finally:
        # Restore original method
        ContentType.objects.get_for_model = original_get_for_model

if __name__ == '__main__':
    result = test_issue_reproduction()
    if result:
        print("Issue reproduced successfully!")
        sys.exit(1)  # Exit with error to indicate issue exists
    else:
        print("Issue not reproduced - migration worked!")
        sys.exit(0)