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
    # Create a queryset with two different multiline RawSQL ORDER BY clauses
    # that have identical last lines (both end with 'else null end')
    queryset = TestModel.objects.all().order_by(
        RawSQL('''
            case when status in ('accepted', 'verification')
                 then 2 else 1 end''', []).desc(),
        RawSQL('''
            case when status in ('accepted', 'verification')
                 then (accepted_datetime, preferred_datetime)
                 else null end''', []).asc(),
    )
    
    # Get the compiler and compile the ORDER BY clause
    compiler = queryset.query.get_compiler(connection=connection)
    order_by_result = compiler.get_order_by()
    
    # Both ORDER BY expressions should be present, not deduplicated
    # The bug causes only one to be returned because the regex matches
    # identical last lines and treats them as the same expression
    assert len(order_by_result) == 2, f"Expected 2 ORDER BY clauses, got {len(order_by_result)}"
    
    # Verify the SQL contains both expressions
    sql_parts = [result[1][0] for result in order_by_result]
    assert any('then 2 else 1 end' in sql for sql in sql_parts), "First RawSQL expression missing"
    assert any('then (accepted_datetime, preferred_datetime)' in sql for sql in sql_parts), "Second RawSQL expression missing"