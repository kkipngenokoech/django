import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps


def test_issue_reproduction():
    """Test that inherited model correctly orders by "-pk" when specified on Parent.Meta.ordering"""
    
    @isolate_apps('test_app')
    def create_models():
        class Parent(models.Model):
            class Meta:
                app_label = 'test_app'
                ordering = ["-pk"]
        
        class Child(Parent):
            class Meta:
                app_label = 'test_app'
        
        return Parent, Child
    
    Parent, Child = create_models()
    
    # Get the SQL query for Child.objects.all()
    query_str = str(Child.objects.all().query)
    
    # The bug: query should contain DESC ordering but shows ASC instead
    # Expected: ORDER BY "test_app_parent"."id" DESC
    # Actual: ORDER BY "test_app_parent"."id" ASC
    assert "DESC" in query_str, f"Expected DESC ordering in query, but got: {query_str}"
    assert "ASC" not in query_str, f"Found unexpected ASC ordering in query: {query_str}"