import pytest
from django.template import Context, Template
from django.test import RequestFactory, override_settings
from django.templatetags.static import StaticNode
from django.contrib.staticfiles.storage import staticfiles_storage


def test_issue_reproduction():
    """Test that static template tag and storage don't respect SCRIPT_NAME."""
    # Create a request with SCRIPT_NAME set
    factory = RequestFactory()
    request = factory.get('/', SCRIPT_NAME='/myapp')
    
    # Test template tag behavior
    template = Template('{% load static %}{% static "css/style.css" %}')
    context = Context({'request': request})
    
    with override_settings(STATIC_URL='/static/'):
        # Current behavior: should include SCRIPT_NAME but doesn't
        result = template.render(context)
        
        # This assertion will FAIL because current code ignores SCRIPT_NAME
        # Expected: '/myapp/static/css/style.css' 
        # Actual: '/static/css/style.css'
        assert result == '/myapp/static/css/style.css', f"Expected SCRIPT_NAME prefix, got: {result}"
        
        # Test storage URL generation
        storage_url = staticfiles_storage.url('css/style.css')
        # This will also fail for the same reason
        assert storage_url == '/myapp/static/css/style.css', f"Storage should respect SCRIPT_NAME, got: {storage_url}"