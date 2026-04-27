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


class ProxyPermissionMigrationTest(TransactionTestCase):
    """Test the proxy permission migration handles duplicates correctly"""
    
    def setUp(self):
        # Clean up any existing test data
        Permission.objects.filter(codename__contains='testmodel').delete()
        ContentType.objects.filter(app_label='testapp').delete()
    
    def test_migration_handles_duplicate_permissions(self):
        """Test that the migration doesn't create IntegrityError when duplicates exist"""
        # Create content types for concrete and proxy models
        concrete_ct, _ = ContentType.objects.get_or_create(
            app_label='testapp',
            model='testmodel'
        )
        proxy_ct, _ = ContentType.objects.get_or_create(
            app_label='testapp', 
            model='testmodel_proxy'
        )
        
        # Create permission that exists for concrete model
        concrete_perm, _ = Permission.objects.get_or_create(
            codename='add_testmodel',
            name='Can add test model',
            content_type=concrete_ct
        )
        
        # Create the same permission for proxy model (simulating the duplicate scenario)
        proxy_perm, _ = Permission.objects.get_or_create(
            codename='add_testmodel',
            name='Can add test model',
            content_type=proxy_ct
        )
        
        # Verify both permissions exist
        self.assertEqual(Permission.objects.filter(codename='add_testmodel').count(), 2)
        
        # Mock the apps registry
        mock_apps = MockApps()
        
        # This should not raise an IntegrityError
        try:
            update_proxy_model_permissions(mock_apps, None)
        except IntegrityError:
            self.fail("Migration raised IntegrityError when it should handle duplicates gracefully")
        
        # Verify permissions still exist and weren't corrupted
        permissions = Permission.objects.filter(codename='add_testmodel')
        self.assertEqual(permissions.count(), 2)
        
        # Verify one permission is still for concrete model and one for proxy
        concrete_perms = permissions.filter(content_type=concrete_ct)
        proxy_perms = permissions.filter(content_type=proxy_ct)
        self.assertEqual(concrete_perms.count(), 1)
        self.assertEqual(proxy_perms.count(), 1)
    
    def test_migration_updates_permissions_without_duplicates(self):
        """Test that migration correctly updates permissions when no duplicates exist"""
        # Create content types
        concrete_ct, _ = ContentType.objects.get_or_create(
            app_label='testapp',
            model='testmodel'
        )
        proxy_ct, _ = ContentType.objects.get_or_create(
            app_label='testapp',
            model='testmodel_proxy'
        )
        
        # Create permission only for concrete model
        concrete_perm, _ = Permission.objects.get_or_create(
            codename='add_testmodel',
            name='Can add test model',
            content_type=concrete_ct
        )
        
        # Verify only one permission exists
        self.assertEqual(Permission.objects.filter(codename='add_testmodel').count(), 1)
        
        # Mock the apps registry with a model that would trigger the migration
        class MockModel:
            class _meta:
                proxy = True
                model_name = 'testmodel'
                default_permissions = ('add', 'change', 'delete', 'view')
                permissions = ()
                app_label = 'testapp'
            _meta = _meta()
        
        class MockAppsWithModel:
            def get_model(self, app_label, model_name):
                if app_label == 'auth' and model_name == 'Permission':
                    return Permission
                elif app_label == 'contenttypes' and model_name == 'ContentType':
                    return ContentType
                return None
            
            def get_models(self):
                return [MockModel]
        
        mock_apps = MockAppsWithModel()
        
        # Run the migration
        update_proxy_model_permissions(mock_apps, None)
        
        # Verify the permission was updated to use proxy content type
        updated_perm = Permission.objects.get(codename='add_testmodel')
        self.assertEqual(updated_perm.content_type, proxy_ct)
