import pytest
from django.urls import re_path
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls.resolvers import URLResolver, RegexPattern


def test_issue_reproduction():
    """Test that optional URL params with nested groups don't crash view functions."""
    
    # Define a view function that matches the issue description
    def modules(request, format='html'):
        return HttpResponse(f'format: {format}')
    
    # Create the problematic URL pattern from the issue
    pattern = re_path(r'^module/(?P<format>(html|json|xml))?/?$', modules, name='modules')
    
    # Create a request factory to simulate requests
    factory = RequestFactory()
    
    # Test the case that should work: /module/ (no format specified)
    request = factory.get('/module/')
    
    # Try to resolve and call the view - this should work but currently fails
    # because Django passes too many positional arguments
    match = pattern.resolve('/module/')
    
    # The issue is that match.args contains extra arguments from nested groups
    # It should be empty when using named groups, but contains the nested group match
    assert match is not None, "Pattern should match /module/"
    
    # This is the core issue: when there are named groups, args should be empty
    # but the nested group is causing extra positional arguments
    assert len(match.args) == 0, f"Expected no positional args, got {match.args}"
    
    # The kwargs should contain the format parameter (None in this case)
    assert 'format' in match.kwargs, "Expected 'format' in kwargs"
    assert match.kwargs['format'] is None, f"Expected format=None, got {match.kwargs['format']}"
    
    # This call should work but currently fails with "takes from 1 to 2 positional arguments but 3 were given"
    try:
        response = match.func(request, *match.args, **match.kwargs)
        assert response.status_code == 200
        assert b'format: None' in response.content
    except TypeError as e:
        if "positional arguments but 3 were given" in str(e):
            pytest.fail(f"View function received too many arguments: {e}")
        else:
            raise
    
    # Also test with a format specified
    match_json = pattern.resolve('/module/json/')
    assert match_json is not None, "Pattern should match /module/json/"
    assert len(match_json.args) == 0, f"Expected no positional args for /module/json/, got {match_json.args}"
    assert match_json.kwargs['format'] == 'json', f"Expected format='json', got {match_json.kwargs['format']}"
    
    try:
        response_json = match_json.func(request, *match_json.args, **match_json.kwargs)
        assert response_json.status_code == 200
        assert b'format: json' in response_json.content
    except TypeError as e:
        if "positional arguments but 3 were given" in str(e):
            pytest.fail(f"View function received too many arguments for /module/json/: {e}")
        else:
            raise