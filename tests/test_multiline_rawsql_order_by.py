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
    
    # Get the compiler and extract ORDER BY clauses
    compiler = queryset.query.get_compiler(connection=connection)
    order_by_clauses = compiler.get_order_by()
    
    # Both ORDER BY clauses should be present, not deduplicated
    # The bug causes the second clause to be removed because the regex
    # only sees 'else null end' for both, thinking they're identical
    assert len(order_by_clauses) == 2, f"Expected 2 ORDER BY clauses, got {len(order_by_clauses)}"
    
    # Verify the SQL contains both different CASE expressions
    sql_parts = [clause[1][0] for clause in order_by_clauses]
    
    # First clause should contain the priority logic
    assert any('then 2 else 1 end' in sql for sql in sql_parts), "Missing first CASE expression"
    
    # Second clause should contain the datetime logic  
    assert any('accepted_datetime, preferred_datetime' in sql for sql in sql_parts), "Missing second CASE expression"