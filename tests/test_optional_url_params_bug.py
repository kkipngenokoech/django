import pytest
from django.urls import re_path
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls.resolvers import URLResolver, RegexPattern

def test_issue_reproduction():
    """Test that optional URL params with None values don't crash view functions."""
    
    # Define a view function that expects at most 2 positional arguments
    def modules(request, format='html'):
        return HttpResponse(f'format: {format}')
    
    # Create URL pattern with optional named group that can be None
    pattern = RegexPattern(r'^module/(?P<format>(html|json|xml))?/?$', is_endpoint=True)
    
    # Test the problematic case: when optional parameter is not provided
    # This should match '/module/' and the format group should be None
    match_result = pattern.match('/module/')
    
    assert match_result is not None
    remaining_path, args, kwargs = match_result
    
    # The issue: kwargs contains {'format': None} which gets passed to the view
    # This causes TypeError when the view function is called
    assert 'format' in kwargs
    assert kwargs['format'] is None
    
    # Simulate what Django does - call the view with the matched parameters
    # This should fail with "modules() takes from 1 to 2 positional arguments but 3 were given"
    request = RequestFactory().get('/module/')
    
    # The bug: None values in kwargs cause the view to receive unexpected arguments
    with pytest.raises(TypeError, match="takes from 1 to 2 positional arguments but 3 were given"):
        modules(request, **kwargs)