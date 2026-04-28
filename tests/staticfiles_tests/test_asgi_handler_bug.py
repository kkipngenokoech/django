import asyncio
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.http import HttpRequest
from django.test import TestCase, override_settings
from django.conf import settings


def test_issue_reproduction():
    """Test that ASGIStaticFilesHandler has get_response_async method."""
    
    # Create a simple ASGI application
    async def simple_app(scope, receive, send):
        response = {
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'text/plain']],
        }
        await send(response)
        await send({'type': 'http.response.body', 'body': b'Hello World'})
    
    # Create ASGIStaticFilesHandler
    handler = ASGIStaticFilesHandler(simple_app)
    
    # Create a mock request for a static file
    request = HttpRequest()
    request.path = '/static/test.css'
    request.method = 'GET'
    
    # The issue: get_response_async should exist and be callable
    # Currently it doesn't exist, so this will fail
    assert hasattr(handler, 'get_response_async'), "ASGIStaticFilesHandler should have get_response_async method"
    assert callable(getattr(handler, 'get_response_async', None)), "get_response_async should be callable"
    
    # Test that get_response_async can be called (this will fail with current code)
    async def test_async_call():
        try:
            response = await handler.get_response_async(request)
            # If we get here, the method exists and is callable
            return True
        except Exception as e:
            # This should not happen once the bug is fixed
            raise AssertionError(f"get_response_async failed: {e}")
    
    # Run the async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(test_async_call())
        assert result is True
    finally:
        loop.close()