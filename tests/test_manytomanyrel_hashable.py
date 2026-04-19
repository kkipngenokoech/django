import pytest
from django.db import models
from django.test import TestCase
from django.apps import apps
from django.conf import settings


def test_issue_reproduction():
    """Test that ManyToManyRel with through_fields can be hashed without TypeError."""
    
    # Configure Django settings if not already configured
    if not settings.configured:
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
            INSTALLED_APPS=['__main__'],
            USE_TZ=True,
        )
        apps.populate(settings.INSTALLED_APPS)
    
    class Parent(models.Model):
        name = models.CharField(max_length=256)
        
        class Meta:
            app_label = '__main__'
    
    class ProxyParent(Parent):
        class Meta:
            proxy = True
            app_label = '__main__'
    
    class Child(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE)
        many_to_many_field = models.ManyToManyField(
            to=Parent,
            through="ManyToManyModel",
            through_fields=['child', 'parent'],
            related_name="something"
        )
        
        class Meta:
            app_label = '__main__'
    
    class ManyToManyModel(models.Model):
        parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='+')
        child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='+')
        second_child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, default=None)
        
        class Meta:
            app_label = '__main__'
    
    # Get the ManyToManyRel object from the field
    m2m_field = Child._meta.get_field('many_to_many_field')
    m2m_rel = m2m_field.remote_field
    
    # This should not raise a TypeError about unhashable list
    # The bug is that through_fields is a list but not made hashable in identity property
    hash(m2m_rel)