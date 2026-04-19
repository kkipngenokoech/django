import pytest
from django.utils.http import parse_http_date_safe

def test_issue_reproduction():
    # Empty string should return None, not raise an exception
    result = parse_http_date_safe('')
    assert result is None
    
    # Also test whitespace-only string
    result = parse_http_date_safe('   ')
    assert result is None