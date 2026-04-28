import pytest
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.test import RequestFactory
from django.conf import settings
from django.test.utils import override_settings


def test_issue_reproduction():
    """Test that ASGIStaticFilesHandler has get_response_async method."""
    # Mock ASGI application
    async def mock_app(scope, receive, send):
        pass
    
    # Create handler
    handler = ASGIStaticFilesHandler(mock_app)
    
    # Create a request for a static file
    factory = RequestFactory()
    request = factory.get('/static/test.css')
    
    # The handler should have get_response_async method
    assert hasattr(handler, 'get_response_async'), "ASGIStaticFilesHandler should have get_response_async method"
    
    # The method should not be None
    assert handler.get_response_async is not None, "get_response_async should not be None"
    
    # The method should be callable
    assert callable(handler.get_response_async), "get_response_async should be callable"