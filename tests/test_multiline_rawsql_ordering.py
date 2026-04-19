import pytest
from django.db import models
from django.db.models.expressions import RawSQL
from django.test import TestCase
from django.db import connection


class TestModel(models.Model):
    status = models.CharField(max_length=20)
    accepted_datetime = models.DateTimeField(null=True)
    preferred_datetime = models.DateTimeField(null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that multiline RawSQL ORDER BY clauses are not incorrectly deduplicated."""
    # Create a queryset with two different multiline RawSQL ORDER BY expressions
    # that have the same last line (containing DESC/ASC)
    queryset = TestModel.objects.all().order_by(
        RawSQL('''
            case when status in ('accepted', 'verification')
                 then 2 else 1 end''', []).desc(),
        RawSQL('''
            case when status in ('accepted', 'verification')
                 then (accepted_datetime, preferred_datetime)
                 else null end''', []).asc(),
    )
    
    # Get the compiler and extract the ORDER BY clause
    compiler = queryset.query.get_compiler(connection=connection)
    order_by_result = compiler.get_order_by()
    
    # Both ORDER BY expressions should be present, not deduplicated
    # The bug causes only one to be returned because the regex incorrectly
    # identifies them as the same due to matching only the last line
    assert len(order_by_result) == 2, f"Expected 2 ORDER BY clauses, got {len(order_by_result)}"