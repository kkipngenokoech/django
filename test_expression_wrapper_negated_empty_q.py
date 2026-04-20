import pytest
from django.db import models
from django.db.models import Q, BooleanField
from django.db.models.expressions import ExpressionWrapper
from django.test import TestCase
from django.test.utils import isolate_apps


@isolate_apps('test_app')
def test_issue_reproduction():
    """Test that ExpressionWrapper with ~Q(pk__in=[]) generates valid SQL."""
    
    # Create a simple test model
    class TestModel(models.Model):
        name = models.CharField(max_length=100)
        
        class Meta:
            app_label = 'test_app'
    
    # Create a queryset
    queryset = TestModel.objects.all()
    
    # Test the working case: ExpressionWrapper(Q(pk__in=[]))
    working_query = queryset.annotate(
        foo=ExpressionWrapper(Q(pk__in=[]), output_field=BooleanField())
    ).values("foo")
    working_sql = str(working_query.query)
    
    # This should work and produce something like "SELECT 0 AS foo FROM ..."
    assert "0" in working_sql or "FALSE" in working_sql.upper()
    
    # Test the broken case: ExpressionWrapper(~Q(pk__in=[]))
    broken_query = queryset.annotate(
        foo=ExpressionWrapper(~Q(pk__in=[]), output_field=BooleanField())
    ).values("foo")
    broken_sql = str(broken_query.query)
    
    # This currently fails - it produces "SELECT AS foo FROM ..." (empty)
    # It should produce something like "SELECT 1 AS foo FROM ..." or "SELECT NOT (0) AS foo FROM ..."
    # The bug is that it produces an empty string for the SELECT clause
    assert "AS \"foo\"" not in broken_sql or ("1" in broken_sql or "TRUE" in broken_sql.upper() or "NOT" in broken_sql.upper())