import pytest
from django.db import models
from django.db.models.expressions import RawSQL
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.query import Query
from django.test import TestCase
from django.db import connection


class TestModel(models.Model):
    status = models.CharField(max_length=20)
    accepted_datetime = models.DateTimeField(null=True)
    preferred_datetime = models.DateTimeField(null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that multiline RawSQL order_by clauses are not incorrectly deduplicated."""
    # Create a query with multiple multiline RawSQL order_by clauses
    # that have identical last lines but different logic
    query = Query(TestModel)
    
    # Add two different multiline RawSQL expressions that both end with "else 1 end"
    # but have different CASE logic - these should NOT be treated as duplicates
    raw_sql_1 = RawSQL('''
        case when status in ('accepted', 'verification')
             then 2 else 1 end''', [])
    
    raw_sql_2 = RawSQL('''
        case when status in ('pending', 'review')
             then 3 else 1 end''', [])
    
    # Set up the query with order_by using these RawSQL expressions
    query.add_ordering(raw_sql_1.desc())
    query.add_ordering(raw_sql_2.asc())
    
    # Create compiler and get the order_by result
    compiler = SQLCompiler(query, connection, 'default')
    order_by_result = compiler.get_order_by()
    
    # The bug causes the second RawSQL to be dropped because the regex
    # incorrectly identifies them as the same due to matching last lines
    # We should have 2 order_by clauses, not 1
    assert len(order_by_result) == 2, f"Expected 2 order_by clauses, got {len(order_by_result)}"
    
    # Verify that both expressions are actually different
    first_sql = order_by_result[0][1][0]  # (expr, (sql, params, is_ref))
    second_sql = order_by_result[1][1][0]
    
    # The SQLs should be different - one should contain 'accepted', 'verification'
    # and the other should contain 'pending', 'review'
    assert 'accepted' in first_sql and 'verification' in first_sql
    assert 'pending' in second_sql and 'review' in second_sql
    
    # Ensure they are actually different SQL strings
    assert first_sql != second_sql, "The two RawSQL expressions should produce different SQL"