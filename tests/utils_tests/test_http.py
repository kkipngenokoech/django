import pytest
from django.utils.http import parse_http_date

def test_issue_reproduction():
    # Empty string for If-Modified-Since header should be handled gracefully
    # but currently raises ValueError since d6aff369ad3
    with pytest.raises(ValueError):
        parse_http_date('')