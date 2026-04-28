import pytest
from django.contrib.auth.models import User
from django.db.models import Max
from django.test import TestCase
from django.db import connection


def test_issue_reproduction():
    """
    Test that filtering on query result preserves GROUP BY of internal query.
    
    This test reproduces the bug where Exact.process_rhs overrides the GROUP BY
    clause when using a subquery with values() and annotate().
    """
    # Create the subquery that should group by 'email'
    subquery = User.objects.filter(email__isnull=True).values('email').annotate(m=Max('id')).values('m')[:1]
    
    # Use the subquery in an exact lookup
    main_query = User.objects.filter(id=subquery)
    
    # Get the SQL to inspect the GROUP BY clause
    sql = str(main_query.query)
    
    # The subquery should GROUP BY email, not id
    # The bug causes it to GROUP BY U0."id" instead of U0."email"
    assert 'GROUP BY U0."email"' in sql, f"Expected GROUP BY U0.\"email\" but got: {sql}"
    assert 'GROUP BY U0."id"' not in sql, f"Found incorrect GROUP BY U0.\"id\" in: {sql}"
    
    # Additional verification: the subquery alone should have correct GROUP BY
    subquery_sql = str(subquery.query)
    assert 'GROUP BY "auth_user"."email"' in subquery_sql, f"Subquery should group by email: {subquery_sql}"