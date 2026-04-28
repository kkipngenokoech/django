import pytest
from django.urls import re_path
from django.urls.resolvers import URLResolver, RegexPattern
from django.http import HttpRequest
from django.test import RequestFactory


def test_issue_reproduction():
    """Test that optional URL params with nested groups don't crash view functions."""
    
    # Define a simple view function that expects only request and format parameters
    def modules_view(request, format='html'):
        return f"format: {format}"
    
    # Create the problematic URL pattern with nested groups
    # This pattern has (?P<format>(html|json|xml))? which creates:
    # - One named group 'format' 
    # - One unnamed nested group (html|json|xml)
    url_pattern = re_path(r'^module/(?P<format>(html|json|xml))?/?$', modules_view, name='modules')
    
    # Create a URLResolver to test the pattern matching
    resolver = URLResolver(RegexPattern(r'^'), [url_pattern])
    
    # Test the URL resolution
    request_factory = RequestFactory()
    request = request_factory.get('/module/')
    
    # This should resolve the URL and extract parameters
    match = resolver.resolve('/module/')
    
    # The bug: Django extracts both the named group and the nested unnamed group
    # This results in extra arguments being passed to the view function
    # Expected: args=(), kwargs={'format': None} (or empty if no match)
    # Actual (buggy): args=('',), kwargs={'format': None} - extra empty string from nested group
    
    # Try to call the view function with the resolved arguments
    # This should work but will fail due to the bug
    try:
        result = match.func(request, *match.args, **match.kwargs)
        # If we get here without exception, the bug is fixed
        assert result == "format: None" or result == "format: html"
    except TypeError as e:
        # This is the expected failure - too many arguments passed
        assert "takes from 1 to 2 positional arguments but 3 were given" in str(e)
        # Re-raise to make the test fail, demonstrating the bug
        raise
    
    # Also test with a specific format to ensure the pattern works correctly
    match_html = resolver.resolve('/module/html/')
    try:
        result_html = match_html.func(request, *match_html.args, **match_html.kwargs)
        assert "format: html" in result_html
    except TypeError as e:
        assert "takes from 1 to 2 positional arguments but 3 were given" in str(e)
        raise