#!/usr/bin/env python
"""
Simple test to verify the fix for the proxy permissions migration issue.
This test simulates the problematic scenario without requiring full Django setup.
"""

class MockPermission:
    """Mock Permission model"""
    def __init__(self, codename, name, content_type):
        self.codename = codename
        self.name = name
        self.content_type = content_type
        
    def __repr__(self):
        return f"Permission(codename='{self.codename}', content_type={self.content_type})"

class MockContentType:
    """Mock ContentType model"""
    def __init__(self, id, app_label, model):
        self.id = id
        self.app_label = app_label
        self.model = model
        
    def __repr__(self):
        return f"ContentType(id={self.id}, app_label='{self.app_label}', model='{self.model}')"

class MockQuerySet:
    """Mock QuerySet for testing"""
    def __init__(self, items=None, manager=None):
        self.items = items or []
        self.manager = manager
        
    def filter(self, **kwargs):
        # Simple filter implementation for testing
        filtered = []
        for item in self.items:
            match = True
            for key, value in kwargs.items():
                if key == 'content_type' and item.content_type != value:
                    match = False
                    break
                elif key == 'codename__in' and item.codename not in value:
                    match = False
                    break
            if match:
                filtered.append(item)
        return MockQuerySet(filtered, self.manager)
    
    def exclude(self, **kwargs):
        # Simple exclude implementation for testing
        excluded = []
        for item in self.items:
            match = False
            for key, value in kwargs.items():
                if key == 'codename__in' and item.codename in value:
                    match = True
                    break
            if not match:
                excluded.append(item)
        return MockQuerySet(excluded, self.manager)
    
    def update(self, **kwargs):
        # Update all items in the queryset
        for item in self.items:
            for key, value in kwargs.items():
                setattr(item, key, value)
        return len(self.items)
    
    def delete(self):
        # Remove items from the original list
        count = len(self.items)
        if self.manager:
            for item in self.items:
                if item in self.manager.permissions:
                    self.manager.permissions.remove(item)
        return count
    
    def exists(self):
        return len(self.items) > 0
    
    def values_list(self, field, flat=False):
        if flat:
            return [getattr(item, field) for item in self.items]
        return [(getattr(item, field),) for item in self.items]

class MockPermissionManager:
    """Mock Permission objects manager"""
    def __init__(self):
        self.permissions = []
    
    def filter(self, *args, **kwargs):
        # Handle Q objects and regular filters
        from django.db.models import Q
        
        filtered = []
        for perm in self.permissions:
            match = True
            
            # Handle Q objects in args
            for q in args:
                if isinstance(q, Q):
                    # Simple Q object handling for codename__in
                    if hasattr(q, 'children') and q.children:
                        for child in q.children:
                            if isinstance(child, tuple) and len(child) == 2:
                                field, value = child
                                if field == 'codename__in' and perm.codename not in value:
                                    match = False
                                    break
            
            # Handle regular kwargs
            for key, value in kwargs.items():
                if key == 'content_type' and perm.content_type != value:
                    match = False
                    break
                elif key == 'codename__in' and perm.codename not in value:
                    match = False
                    break
            
            if match:
                filtered.append(perm)
        
        return MockQuerySet(filtered, self)

def test_migration_fix():
    """Test that the migration handles duplicate permissions correctly"""
    print("Testing migration fix...")
    
    # Create mock content types
    concrete_ct = MockContentType(1, 'test_app', 'testmodel')
    proxy_ct = MockContentType(2, 'test_app', 'testmodel_proxy')
    
    # Create mock permissions
    perm1 = MockPermission('add_testmodel', 'Can add test model', concrete_ct)
    perm2 = MockPermission('add_testmodel', 'Can add test model', proxy_ct)  # This causes the conflict
    
    # Mock Permission manager
    permission_manager = MockPermissionManager()
    permission_manager.permissions = [perm1, perm2]
    
    # Mock the Permission model
    class MockPermissionModel:
        objects = permission_manager
    
    # Mock the ContentType model
    class MockContentTypeModel:
        @staticmethod
        def get_for_model(model, for_concrete_model=True):
            if for_concrete_model:
                return concrete_ct
            else:
                return proxy_ct
    
    MockContentTypeModel.objects = MockContentTypeModel()
    
    # Mock the proxy model
    class MockProxyModel:
        class _meta:
            proxy = True
            model_name = 'testmodel'
            default_permissions = ('add', 'change', 'delete', 'view')
            permissions = ()
            app_label = 'test_app'
        _meta = _meta()
    
    # Mock apps
    class MockApps:
        def get_model(self, app_label, model_name):
            if model_name == 'Permission':
                return MockPermissionModel
            elif model_name == 'ContentType':
                return MockContentTypeModel
        
        def get_models(self):
            return [MockProxyModel]
    
    # Import and test the migration function
    from django.db.models import Q
    
    # Simulate the migration logic with our fix
    apps = MockApps()
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    print(f"Before migration:")
    print(f"  Permission 1: {perm1}")
    print(f"  Permission 2: {perm2}")
    
    for Model in apps.get_models():
        opts = Model._meta
        if not opts.proxy:
            continue
            
        proxy_default_permissions_codenames = [
            '%s_%s' % (action, opts.model_name)
            for action in opts.default_permissions
        ]
        permissions_query = Q(codename__in=proxy_default_permissions_codenames)
        
        concrete_content_type = ContentType.get_for_model(Model, for_concrete_model=True)
        proxy_content_type = ContentType.get_for_model(Model, for_concrete_model=False)
        old_content_type = concrete_content_type  # reverse=False
        new_content_type = proxy_content_type     # reverse=False
        
        # Get permissions that need to be updated
        permissions_to_update = Permission.objects.filter(
            permissions_query,
            content_type=old_content_type,
        )
        
        print(f"Permissions to update: {permissions_to_update.items}")
        
        # Check for existing permissions with the target content type that would cause conflicts
        existing_permissions = Permission.objects.filter(
            permissions_query,
            content_type=new_content_type,
        )
        
        print(f"Existing permissions: {existing_permissions.items}")
        
        if existing_permissions.exists():
            # Get the codenames of existing permissions to avoid conflicts
            existing_codenames = set(existing_permissions.values_list('codename', flat=True))
            print(f"Existing codenames: {existing_codenames}")
            
            # Filter out permissions that would cause conflicts
            permissions_to_update = permissions_to_update.exclude(
                codename__in=existing_codenames
            )
            
            print(f"Permissions to update after filtering: {permissions_to_update.items}")
            
            # Delete the conflicting permissions from the old content type
            conflicting_permissions = Permission.objects.filter(
                permissions_query,
                content_type=old_content_type,
                codename__in=existing_codenames,
            )
            
            print(f"Deleting conflicting permissions: {conflicting_permissions.items}")
            delete_count = conflicting_permissions.delete()
            print(f"Deleted {delete_count} conflicting permissions")
        
        # Update the remaining permissions
        update_count = permissions_to_update.update(content_type=new_content_type)
        print(f"Updated {update_count} permissions")
    
    print(f"After migration:")
    for perm in permission_manager.permissions:
        print(f"  {perm}")
    
    # Verify the result
    remaining_permissions = [p for p in permission_manager.permissions if p.codename == 'add_testmodel']
    if len(remaining_permissions) == 1 and remaining_permissions[0].content_type == proxy_ct:
        print("✅ Migration fix works correctly!")
        return True
    else:
        print("❌ Migration fix failed!")
        print(f"Expected 1 permission with proxy content type, got {len(remaining_permissions)} permissions")
        return False

if __name__ == '__main__':
    success = test_migration_fix()
    exit(0 if success else 1)