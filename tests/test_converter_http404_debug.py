import pytest
from django.conf import settings
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.urls import path, include
from django.urls.converters import StringConverter
from django.urls.resolvers import get_resolver
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.exception import response_for_exception
from django.views.debug import technical_404_response


class Http404Converter(StringConverter):
    """A converter that raises Http404 in to_python method."""
    
    def to_python(self, value):
        # This should trigger a technical 404 response when DEBUG=True
        # but currently shows generic error message
        raise Http404("Custom converter Http404 for value: {}".format(value))


def dummy_view(request, param):
    return None


@override_settings(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    SECRET_KEY='test-key'
)
def test_issue_reproduction():
    """Test that Http404 in path converter shows technical response when DEBUG=True."""
    
    # Register the custom converter
    from django.urls.converters import register_converter
    register_converter(Http404Converter, 'http404')
    
    # Create URL patterns that use the converter
    urlpatterns = [
        path('test/<http404:param>/', dummy_view, name='test_view'),
    ]
    
    # Set up the module-level urlpatterns for ROOT_URLCONF
    import sys
    current_module = sys.modules[__name__]
    current_module.urlpatterns = urlpatterns
    
    # Create a request
    factory = RequestFactory()
    request = factory.get('/test/some_value/')
    
    # Try to resolve the URL - this should raise Http404 from the converter
    resolver = get_resolver()
    
    # The issue: Http404 from converter doesn't get proper technical response
    with pytest.raises(Http404) as exc_info:
        resolver.resolve('/test/some_value/')
    
    # When DEBUG=True, we should be able to get a technical response
    # but currently this fails because Http404 from converters isn't handled properly
    handler = WSGIHandler()
    response = response_for_exception(request, exc_info.value)
    
    # This assertion will fail because the current code doesn't provide
    # a technical 404 response for Http404 raised in converters
    # Instead it shows a generic error message
    assert b'Custom converter Http404 for value: some_value' in response.content, \
        "Http404 from path converter should show technical response with custom message when DEBUG=True"