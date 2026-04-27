import pytest
from django.conf import settings
from django.http import Http404, HttpRequest
from django.test import RequestFactory, override_settings
from django.urls import path, register_converter
from django.urls.converters import StringConverter
from django.views.debug import technical_404_response
from django.core.handlers.wsgi import WSGIHandler
from django.core.handlers.exception import convert_exception_to_response
from io import StringIO
import sys


class Http404RaisingConverter(StringConverter):
    """A converter that raises Http404 in to_python method."""
    
    def to_python(self, value):
        if value == 'trigger404':
            raise Http404("Custom 404 from converter")
        return value


def dummy_view(request, param):
    return HttpResponse("Success")


def test_issue_reproduction():
    """Test that Http404 raised in path converter results in technical response when DEBUG=True."""
    
    # Register the custom converter
    register_converter(Http404RaisingConverter, 'http404conv')
    
    # Create URL patterns that use the converter
    urlpatterns = [
        path('test/<http404conv:param>/', dummy_view, name='test_view'),
    ]
    
    with override_settings(
        DEBUG=True,
        ROOT_URLCONF=__name__,
        SECRET_KEY='test-key',
        USE_I18N=False,
    ):
        # Patch the module's urlpatterns
        import sys
        current_module = sys.modules[__name__]
        current_module.urlpatterns = urlpatterns
        
        # Create a request that will trigger Http404 in converter
        factory = RequestFactory()
        request = factory.get('/test/trigger404/')
        
        # Simulate what happens in the WSGI handler
        handler = WSGIHandler()
        
        # Capture the response
        response = handler.get_response(request)
        
        # The bug: when Http404 is raised in converter, we should get a technical 404 response
        # with HTML content showing debug information, but instead we get a generic error
        
        # Check that we get a proper technical 404 response (should be HTML with debug info)
        assert response.status_code == 404
        
        # The key assertion: when DEBUG=True and Http404 is raised in a converter,
        # we should get an HTML response with technical debug information,
        # not a plain text "A server error occurred" message
        content = response.content.decode('utf-8')
        
        # This should contain technical 404 debug information
        assert 'text/html' in response.get('Content-Type', '')
        assert 'URLconf' in content or 'technical' in content.lower()
        
        # Should NOT be the generic server error message
        assert 'A server error occurred. Please contact the administrator.' not in content