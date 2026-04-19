import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.conf import settings
from django.template.context import make_context


def test_issue_reproduction():
    """Test that static tag doesn't respect SCRIPT_NAME from request context."""
    # Configure Django settings for the test
    if not settings.configured:
        settings.configure(
            STATIC_URL='/static/',
            INSTALLED_APPS=['django.contrib.staticfiles'],
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.request',
                    ],
                },
            }],
        )
    
    # Create a request with SCRIPT_NAME set
    factory = RequestFactory()
    request = factory.get('/test/')
    request.META['SCRIPT_NAME'] = '/myapp'  # This should be prepended to static URLs
    
    # Create template with static tag
    template = Template('{% load static %}{% static "css/style.css" %}')
    
    # Create context with the request
    context = make_context({'request': request}, request)
    
    # Render the template
    result = template.render(context)
    
    # The bug: result should be '/myapp/static/css/style.css' but it's '/static/css/style.css'
    # This assertion will FAIL on the current buggy code because SCRIPT_NAME is ignored
    assert result == '/myapp/static/css/style.css', f"Expected '/myapp/static/css/style.css', got '{result}'"