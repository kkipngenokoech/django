import pytest
from django.contrib.auth.models import User
from django.db.models import Max
from django.test import TestCase
from django.db import connection


def test_issue_reproduction():
    """
    Test that filtering on query result preserves GROUP BY of internal query.
    
    The bug: Exact.process_rhs unconditionally calls clear_select_clause() and 
    add_fields(['pk']) on subqueries, which overrides the original GROUP BY clause.
    """
    # Create the subquery with custom select fields and GROUP BY
    subquery = User.objects.filter(email__isnull=True).values('email').annotate(m=Max('id')).values('m')
    
    # Verify the subquery has the correct GROUP BY initially
    subquery_sql = str(subquery.query)
    assert 'GROUP BY "auth_user"."email"' in subquery_sql
    
    # Apply slicing to make it a single result (required for Exact lookup)
    sliced_subquery = subquery[:1]
    sliced_sql = str(sliced_subquery.query)
    assert 'GROUP BY "auth_user"."email"' in sliced_sql
    
    # Now use this subquery in an Exact lookup (filter)
    # This is where the bug occurs - the GROUP BY should be preserved
    outer_query = User.objects.filter(id=sliced_subquery)
    outer_sql = str(outer_query.query)
    
    # The bug: GROUP BY gets changed from U0."email" to U0."id"
    # We expect it to remain GROUP BY U0."email" but it becomes GROUP BY U0."id"
    assert 'GROUP BY U0."email"' in outer_sql, f"Expected GROUP BY U0.\"email\" but got: {outer_sql}"
    assert 'GROUP BY U0."id"' not in outer_sql, f"Should not have GROUP BY U0.\"id\" but got: {outer_sql}"