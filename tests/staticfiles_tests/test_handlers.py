import asyncio
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.test import RequestFactory
from django.http import HttpResponse


async def dummy_asgi_app(scope, receive, send):
    """Dummy ASGI app that returns a simple response."""
    response = HttpResponse("Hello from main app")
    await response(scope, receive, send)


def test_issue_reproduction():
    """Test that ASGIStaticFilesHandler has get_response_async method."""
    handler = ASGIStaticFilesHandler(dummy_asgi_app)
    factory = RequestFactory()
    
    # Create a request for a static file
    request = factory.get('/static/test.css')
    
    # This should fail because get_response_async is None
    async def test_async():
        response = await handler.get_response_async(request)
        return response
    
    # Run the async test - this will fail with "'NoneType' object is not callable"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_async())
    finally:
        loop.close()