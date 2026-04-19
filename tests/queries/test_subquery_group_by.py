import pytest
from django.contrib.auth.models import User
from django.db.models import Max
from django.test import TestCase
from django.db import connection


def test_issue_reproduction():
    """Test that GROUP BY clause is preserved when using query as subquery filter."""
    # Create the inner query with GROUP BY email
    inner_query = User.objects.filter(email__isnull=True).values('email').annotate(m=Max('id')).values('m')
    
    # Verify the inner query has correct GROUP BY
    inner_sql = str(inner_query.query)
    assert 'GROUP BY "auth_user"."email"' in inner_sql
    
    # Use the sliced inner query as a subquery filter
    outer_query = User.objects.filter(id=inner_query[:1])
    outer_sql = str(outer_query.query)
    
    # The bug: subquery should preserve GROUP BY email, not change to GROUP BY id
    # This assertion will FAIL on buggy code because it groups by U0."id" instead of U0."email"
    assert 'GROUP BY U0."email"' in outer_sql
    assert 'GROUP BY U0."id"' not in outer_sql