import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps


@isolate_apps('test_app')
class TestInheritedOrderingPkDesc(TestCase):
    def test_issue_reproduction(self):
        """Test that inherited models correctly order by '-pk' from parent Meta.ordering"""
        
        # Define the models as described in the issue
        class Parent(models.Model):
            class Meta:
                app_label = 'test_app'
                ordering = ["-pk"]
        
        class Child(Parent):
            class Meta:
                app_label = 'test_app'
        
        # Get the query for Child.objects.all()
        queryset = Child.objects.all()
        query_str = str(queryset.query)
        
        # The issue states that the query should order by DESC but actually orders by ASC
        # We expect the query to contain "ORDER BY ... DESC" but it currently contains "ORDER BY ... ASC"
        # This test should FAIL on the current buggy code and PASS once fixed
        
        # Check that the query contains descending order for the primary key
        # The bug is that it generates ASC instead of DESC
        assert 'ORDER BY' in query_str, "Query should contain ORDER BY clause"
        
        # The specific issue is that '-pk' should result in DESC ordering
        # but the current buggy code generates ASC ordering
        # We're looking for the parent table's id field to be ordered DESC
        assert 'DESC' in query_str, f"Query should contain DESC ordering for -pk, but got: {query_str}"
        assert 'ASC' not in query_str, f"Query should not contain ASC ordering when -pk is specified, but got: {query_str}"