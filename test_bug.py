#!/usr/bin/env python
import os
import sys
import django
from django.conf import settings

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
    )

django.setup()

from django.db import models, connection
from django.db.models.expressions import RawSQL

class TestModel(models.Model):
    status = models.CharField(max_length=20)
    accepted_datetime = models.DateTimeField(null=True)
    preferred_datetime = models.DateTimeField(null=True)
    
    class Meta:
        app_label = 'test'

def test_multiline_rawsql_bug():
    """Test that demonstrates the multiline RawSQL ORDER BY bug."""
    print("Testing multiline RawSQL ORDER BY bug...")
    
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
    
    print(f"Number of ORDER BY clauses: {len(order_by_result)}")
    
    # Print the SQL for each ORDER BY clause
    for i, (expr, (sql, params, is_ref)) in enumerate(order_by_result):
        print(f"ORDER BY clause {i+1}: {sql}")
    
    # Both ORDER BY expressions should be present, not deduplicated
    if len(order_by_result) != 2:
        print(f"BUG CONFIRMED: Expected 2 ORDER BY clauses, got {len(order_by_result)}")
        return False
    else:
        print("SUCCESS: Both ORDER BY clauses are present")
        return True

if __name__ == '__main__':
    test_multiline_rawsql_bug()