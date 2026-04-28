import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps


@isolate_apps('test_ordering')
class TestInheritedModelOrdering(TestCase):
    def test_issue_reproduction(self):
        """Test that inherited models preserve descending order for -pk in parent Meta.ordering"""
        
        class Parent(models.Model):
            class Meta:
                app_label = 'test_ordering'
                ordering = ["-pk"]
        
        class Child(Parent):
            class Meta:
                app_label = 'test_ordering'
        
        # Get the SQL query for Child.objects.all()
        query_str = str(Child.objects.all().query)
        
        # The query should order by parent.id DESC, not ASC
        # If the bug exists, it will show ASC instead of DESC
        assert 'ORDER BY' in query_str
        assert 'DESC' in query_str, f"Expected DESC ordering but got: {query_str}"
        assert 'ASC' not in query_str, f"Found ASC ordering when DESC expected: {query_str}"