import pytest
from django.db import models
from django.test import TestCase
from django.apps import apps
from django.conf import settings

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        USE_TZ=True,
    )
    apps.populate(settings.INSTALLED_APPS)

def test_issue_reproduction():
    """Test that ManyToManyRel.identity handles through_fields list properly."""
    
    class Parent(models.Model):
        name = models.CharField(max_length=256)
        
        class Meta:
            app_label = 'test_app'
    
    class ProxyParent(Parent):
        class Meta:
            proxy = True
            app_label = 'test_app'
    
    class Child(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
        
        class Meta:
            app_label = 'test_app'
    
    class ManyToManyModel(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='+')
        child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='+')
        second_child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, default=None)
        
        class Meta:
            app_label = 'test_app'
    
    # Create the ManyToManyField with through_fields as a list
    many_to_many_field = models.ManyToManyField(
        to=Parent,
        through=ManyToManyModel,
        through_fields=['child', 'parent'],
        related_name="something"
    )
    
    # Add the field to Child model
    Child.add_to_class('many_to_many_field', many_to_many_field)
    
    # Get the reverse relation (ManyToManyRel)
    reverse_rel = many_to_many_field.remote_field
    
    # This should not raise a TypeError when trying to hash the identity tuple
    # The bug occurs because through_fields is a list and lists are not hashable
    try:
        hash(reverse_rel.identity)
        # If we get here without exception, the bug is fixed
        assert False, "Expected TypeError due to unhashable list in through_fields"
    except TypeError as e:
        # This is the expected behavior on buggy code
        assert "unhashable type: 'list'" in str(e)
        # The test passes when it fails as expected