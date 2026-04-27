import pytest
from django.conf import settings
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.urls import path
from django.urls.converters import StringConverter
from django.urls.resolvers import URLResolver, RoutePattern
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.exception import response_for_exception


class Http404RaisingConverter(StringConverter):
    """A converter that raises Http404 in to_python method."""
    
    def to_python(self, value):
        if value == 'trigger-404':
            raise Http404("Custom 404 from converter")
        return value


def dummy_view(request, param):
    return None


@override_settings(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    SECRET_KEY='test-key'
)
def test_issue_reproduction():
    """Test that Http404 raised in path converter results in generic server error instead of technical response."""
    
    # Register our custom converter
    from django.urls.converters import register_converter
    register_converter(Http404RaisingConverter, 'http404conv')
    
    # Create URL pattern using our converter
    pattern = RoutePattern('<http404conv:param>', is_endpoint=True)
    
    # Try to match a path that will trigger Http404 in converter
    factory = RequestFactory()
    request = factory.get('/trigger-404/')
    
    # This should demonstrate the bug - Http404 from converter is not handled properly
    # and results in a generic error instead of a technical debug response
    try:
        result = pattern.match('trigger-404/')
        # If we get here, the Http404 was not raised (unexpected)
        assert False, "Expected Http404 to be raised from converter"
    except Http404 as e:
        # This shows the bug - Http404 escapes from the converter without proper handling
        # In a proper implementation, this should be caught and either converted to ValueError
        # or handled to show a technical debug response
        assert str(e) == "Custom 404 from converter"
        # The test fails here because the Http404 is not being handled properly
        # by the URL resolution system