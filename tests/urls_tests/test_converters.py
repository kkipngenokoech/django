import pytest
from django.http import Http404
from django.urls import path
from django.urls.converters import StringConverter
from django.urls.resolvers import RoutePattern
from django.test import override_settings


class Http404Converter(StringConverter):
    """A converter that raises Http404 in to_python method."""
    def to_python(self, value):
        if value == 'trigger-404':
            raise Http404("Object not found")
        return value


def test_issue_reproduction():
    """Test that Http404 raised in path converter's to_python method is not handled properly."""
    # Create a RoutePattern with our custom converter
    pattern = RoutePattern('test/<str:param>/', name='test')
    # Replace the str converter with our Http404 converter
    pattern.converters['param'] = Http404Converter()
    
    # This should raise Http404 instead of returning None like ValueError would
    with pytest.raises(Http404):
        pattern.match('test/trigger-404/')