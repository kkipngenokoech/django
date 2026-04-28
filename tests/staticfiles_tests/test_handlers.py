import pytest
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.test import RequestFactory
from django.conf import settings
from django.core.asgi import get_asgi_application


def test_issue_reproduction():
    """Test that ASGIStaticFilesHandler has get_response_async method."""
    # Configure minimal Django settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            STATIC_URL='/static/',
            STATICFILES_DIRS=[],
            USE_TZ=True,
            SECRET_KEY='test-key'
        )
    
    # Create an ASGI application to wrap
    asgi_app = get_asgi_application()
    
    # Create the ASGIStaticFilesHandler
    handler = ASGIStaticFilesHandler(asgi_app)
    
    # Create a mock request for a static file
    factory = RequestFactory()
    request = factory.get('/static/test.css')
    
    # The bug: get_response_async should exist but doesn't
    # This will fail because get_response_async returns None
    response_async_method = getattr(handler, 'get_response_async', None)
    
    # This assertion will fail on the buggy code because get_response_async doesn't exist
    assert response_async_method is not None, "ASGIStaticFilesHandler should have get_response_async method"
    assert callable(response_async_method), "get_response_async should be callable"