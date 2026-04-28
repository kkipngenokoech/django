import pytest
from django.conf import settings
from django.http import Http404, HttpRequest
from django.test import RequestFactory, override_settings
from django.urls import path, register_converter
from django.urls.converters import StringConverter
from django.views.debug import technical_404_response
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings


class Http404RaisingConverter(StringConverter):
    """A path converter that raises Http404 in to_python method."""
    
    def to_python(self, value):
        # This simulates a converter that uses get_object_or_404 internally
        # and raises Http404 when the object is not found
        if value == 'nonexistent':
            raise Http404("Object not found")
        return value


def test_issue_reproduction():
    """Test that Http404 raised in path converter results in technical response when DEBUG=True."""
    
    # Register our custom converter
    register_converter(Http404RaisingConverter, 'http404_converter')
    
    with override_settings(DEBUG=True, ROOT_URLCONF='test_urls'):
        # Create a mock request that would trigger the converter
        request = RequestFactory().get('/test/nonexistent/')
        request.path = '/test/nonexistent/'
        request.path_info = '/test/nonexistent/'
        
        # Create an Http404 exception that would be raised by the converter
        # This simulates what happens when the URL resolver catches the Http404
        # from the converter and wraps it in a Resolver404
        from django.urls.exceptions import Resolver404
        
        # The original Http404 from the converter gets wrapped
        original_http404 = Http404("Object not found")
        resolver404 = Resolver404({'path': '/test/nonexistent/', 'tried': []})
        
        # When technical_404_response tries to resolve the URL again,
        # it should handle the Http404 gracefully, but currently it doesn't
        try:
            response = technical_404_response(request, resolver404)
            
            # The response should be a proper technical 404 response
            # with status 404 and HTML content showing debug information
            assert response.status_code == 404
            assert 'text/html' in response['Content-Type']
            
            # The response should contain debug information, not a generic error
            content = response.content.decode('utf-8')
            assert 'URLconf' in content or 'tried' in content
            
            # It should NOT be the generic "A server error occurred" message
            assert 'A server error occurred. Please contact the administrator.' not in content
            
        except Exception as e:
            # This is what currently happens - an unhandled exception
            # The test should fail here because the technical_404_response
            # doesn't properly handle Http404 exceptions during URL resolution
            pytest.fail(f"technical_404_response raised unhandled exception: {e}")