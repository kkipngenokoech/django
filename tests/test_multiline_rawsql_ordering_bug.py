import pytest
from django.db import models
from django.db.models.expressions import RawSQL
from django.db.models.sql.compiler import SQLCompiler
from django.db.models.sql.query import Query
from django.db import connection
from django.test import TestCase


class TestModel(models.Model):
    status = models.CharField(max_length=20)
    accepted_datetime = models.DateTimeField(null=True)
    preferred_datetime = models.DateTimeField(null=True)
    
    class Meta:
        app_label = 'test'


def test_issue_reproduction():
    """Test that multiline RawSQL order_by clauses with identical last lines are not incorrectly deduplicated."""
    # Create a query with two different multiline RawSQL order clauses
    # that have identical last lines (both end with "else 1 end")
    query = Query(TestModel)
    
    # First multiline RawSQL - different logic but same ending
    raw_sql_1 = RawSQL('''
        case when status = 'accepted'
             then 2
             else 1 end''', [])
    
    # Second multiline RawSQL - different logic but same ending  
    raw_sql_2 = RawSQL('''
        case when status = 'verification'
             then 3
             else 1 end''', [])
    
    # Add both as order_by clauses
    query.add_ordering(raw_sql_1.asc())
    query.add_ordering(raw_sql_2.desc())
    
    # Create compiler and get order_by results
    compiler = SQLCompiler(query, connection, 'default')
    order_by_result = compiler.get_order_by()
    
    # Both order clauses should be present, but due to the bug,
    # only one will be returned because they have identical last lines
    assert len(order_by_result) == 2, f"Expected 2 order clauses, got {len(order_by_result)}"
    
    # Verify the SQL contains both different case expressions
    sql_parts = [result[1][0] for result in order_by_result]
    
    # Should contain both "status = 'accepted'" and "status = 'verification'"
    combined_sql = ' '.join(sql_parts)
    assert "status = 'accepted'" in combined_sql, "First RawSQL clause missing"
    assert "status = 'verification'" in combined_sql, "Second RawSQL clause missing"