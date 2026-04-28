import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.conf import settings
from django.template.context import RequestContext


def test_issue_reproduction():
    """Test that static template tag ignores SCRIPT_NAME from request context."""
    # Setup a request with SCRIPT_NAME set (simulating sub-path deployment)
    factory = RequestFactory()
    request = factory.get('/')
    request.META['SCRIPT_NAME'] = '/myapp'  # Sub-path where Django is deployed
    
    # Create template with static tag
    template = Template('{% load static %}{% static "css/style.css" %}')
    
    # Render with request context that includes SCRIPT_NAME
    context = RequestContext(request)
    result = template.render(context)
    
    # The bug: result should include SCRIPT_NAME prefix but it doesn't
    # Expected: '/myapp/static/css/style.css' (with SCRIPT_NAME prefix)
    # Actual: '/static/css/style.css' (without SCRIPT_NAME prefix)
    expected_with_script_name = '/myapp/static/css/style.css'
    
    # This assertion will FAIL on current code because SCRIPT_NAME is ignored
    assert result == expected_with_script_name, f"Expected {expected_with_script_name}, got {result}"