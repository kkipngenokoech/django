import pytest
from django.db import models
from django.db.models import RawSQL
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
    # that have identical last lines (both end with 'else 1 end')
    queryset = TestModel.objects.all().order_by(
        RawSQL('''
            case when status in ('accepted', 'verification')
                 then 2 else 1 end''', []).desc(),
        RawSQL('''
            case when status in ('pending', 'review')
                 then 3 else 1 end''', []).asc()
    )
    
    # Get the compiler and compile the ORDER BY clause
    compiler = queryset.query.get_compiler(connection=connection)
    order_by_result = compiler.get_order_by()
    
    # Both ORDER BY expressions should be present, not deduplicated
    # The bug causes the second expression to be removed because both
    # multiline expressions end with the same line 'else 1 end'
    assert len(order_by_result) == 2, f"Expected 2 ORDER BY clauses, got {len(order_by_result)}"
    
    # Verify the SQL contains both CASE expressions
    sql_parts = [item[1][0] for item in order_by_result]
    
    # First expression should contain 'accepted', 'verification'
    first_sql = sql_parts[0]
    assert 'accepted' in first_sql and 'verification' in first_sql
    
    # Second expression should contain 'pending', 'review'
    second_sql = sql_parts[1]
    assert 'pending' in second_sql and 'review' in second_sql