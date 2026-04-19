import pytest
from django.urls import re_path
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls.resolvers import URLResolver, RegexPattern

def test_issue_reproduction():
    """Test that optional URL params with None values don't crash view functions."""
    
    # Define a view function that expects an optional format parameter
    def modules(request, format='html'):
        return HttpResponse(f'format: {format}')
    
    # Create URL pattern with optional named group (same as in the issue)
    pattern = RegexPattern(r'^module/(?P<format>(html|json|xml))?/?$', is_endpoint=True)
    
    # Test the pattern matching behavior
    match_result = pattern.match('module/')
    
    # This should return a match with None value for format
    assert match_result is not None
    new_path, args, kwargs = match_result
    
    # The issue: kwargs contains {'format': None} which gets passed to the view
    # This causes TypeError when the view function is called
    request = RequestFactory().get('/module/')
    
    # This should fail with "modules() takes from 1 to 2 positional arguments but 3 were given"
    # because None gets passed as a positional argument somehow
    with pytest.raises(TypeError, match=r"modules\(\) takes from 1 to 2 positional arguments but 3 were given"):
        modules(request, **kwargs)