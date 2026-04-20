import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.conf import settings
from django.test.utils import override_settings


def test_issue_reproduction():
    """Test that static template tag doesn't respect SCRIPT_NAME from request context."""
    factory = RequestFactory()
    
    # Create a request with SCRIPT_NAME set (simulating sub-path deployment)
    request = factory.get('/', HTTP_HOST='example.com')
    request.META['SCRIPT_NAME'] = '/myapp'
    
    # Create template context with the request
    context = Context({'request': request})
    
    # Test the static template tag
    template = Template("{% load static %}{% static 'css/style.css' %}")
    result = template.render(context)
    
    # The bug: static tag ignores SCRIPT_NAME and returns just STATIC_URL + path
    # Expected: /myapp/static/css/style.css (with SCRIPT_NAME prefix)
    # Actual: /static/css/style.css (without SCRIPT_NAME prefix)
    
    # This assertion will FAIL on current code because SCRIPT_NAME is ignored
    assert result == '/myapp/static/css/style.css', f"Expected SCRIPT_NAME prefix, got: {result}"