import pytest
from django.apps import apps
from django.db import connection
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import override_settings


class ProxyPermissionMigrationTest(TransactionTestCase):
    """
    Test that reproduces and verifies the fix for the IntegrityError when migration 
    0011_update_proxy_permissions tries to update permissions for a model that was 
    recreated as a proxy.
    """
    
    def test_proxy_permission_migration_with_duplicates(self):
        """
        Test that the migration handles the case where permissions already exist
        for both concrete and proxy content types without causing IntegrityError.
        """
        # Import the migration function
        from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
        
        # Create content types for concrete and proxy models
        concrete_ct, _ = ContentType.objects.get_or_create(
            app_label='testapp',
            model='agency_concrete'
        )
        proxy_ct, _ = ContentType.objects.get_or_create(
            app_label='testapp', 
            model='agency'
        )
        
        # Create permissions for the concrete model (simulating existing permissions)
        concrete_perm, _ = Permission.objects.get_or_create(
            codename='add_agency',
            name='Can add agency',
            content_type=concrete_ct
        )
        
        # Create the same permission for the proxy model (simulating the problematic scenario)
        proxy_perm, _ = Permission.objects.get_or_create(
            codename='add_agency',
            name='Can add agency', 
            content_type=proxy_ct
        )
        
        # Verify both permissions exist before migration
        self.assertTrue(Permission.objects.filter(codename='add_agency', content_type=concrete_ct).exists())
        self.assertTrue(Permission.objects.filter(codename='add_agency', content_type=proxy_ct).exists())
        
        # Create a mock apps registry that simulates a proxy model
        class MockModel:
            class _meta:
                proxy = True
                model_name = 'agency'
                default_permissions = ('add', 'change', 'delete', 'view')
                permissions = []
                app_label = 'testapp'
        
        class MockApps:
            def get_model(self, app_label, model_name):
                if app_label == 'auth' and model_name == 'Permission':
                    return Permission
                elif app_label == 'contenttypes' and model_name == 'ContentType':
                    return ContentType
                return None
                
            def get_models(self):
                return [MockModel]
        
        # Mock ContentType.objects.get_for_model to return our test content types
        original_get_for_model = ContentType.objects.get_for_model
        
        def mock_get_for_model(model, for_concrete_model=True):
            if model == MockModel:
                if for_concrete_model:
                    return concrete_ct
                else:
                    return proxy_ct
            return original_get_for_model(model, for_concrete_model)
        
        ContentType.objects.get_for_model = mock_get_for_model
        
        try:
            # Run the migration - this should not raise IntegrityError
            mock_apps = MockApps()
            update_proxy_model_permissions(mock_apps, None)
            
            # Verify that we still have permissions and no duplicates were created
            concrete_perms = Permission.objects.filter(codename='add_agency', content_type=concrete_ct)
            proxy_perms = Permission.objects.filter(codename='add_agency', content_type=proxy_ct)
            
            # The migration should have moved permissions from concrete to proxy content type
            # but avoided creating duplicates
            total_perms = Permission.objects.filter(codename='add_agency').count()
            self.assertLessEqual(total_perms, 2)  # Should not have created duplicates
            
        finally:
            # Restore original method
            ContentType.objects.get_for_model = original_get_for_model
    
    def test_migration_handles_missing_content_types(self):
        """
        Test that the migration gracefully handles cases where content types
        cannot be resolved for models.
        """
        from django.contrib.auth.migrations.0011_update_proxy_permissions import update_proxy_model_permissions
        
        class MockModel:
            class _meta:
                proxy = True
                model_name = 'nonexistent'
                default_permissions = ('add',)
                permissions = []
                app_label = 'testapp'
        
        class MockApps:
            def get_model(self, app_label, model_name):
                if app_label == 'auth' and model_name == 'Permission':
                    return Permission
                elif app_label == 'contenttypes' and model_name == 'ContentType':
                    return ContentType
                return None
                
            def get_models(self):
                return [MockModel]
        
        # Mock get_for_model to raise an exception
        original_get_for_model = ContentType.objects.get_for_model
        
        def mock_get_for_model(model, for_concrete_model=True):
            if model == MockModel:
                raise ContentType.DoesNotExist("Content type not found")
            return original_get_for_model(model, for_concrete_model)
        
        ContentType.objects.get_for_model = mock_get_for_model
        
        try:
            # This should not raise an exception
            mock_apps = MockApps()
            update_proxy_model_permissions(mock_apps, None)
            
        finally:
            # Restore original method
            ContentType.objects.get_for_model = original_get_for_model