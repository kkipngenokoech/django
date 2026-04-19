#!/usr/bin/env python
"""
Simple test to verify the SCRIPT_NAME fix works without full Django setup.
"""

# Mock the necessary Django components for testing
class MockRequest:
    def __init__(self, script_name=''):
        self.META = {'SCRIPT_NAME': script_name} if script_name else {}

class MockContext(dict):
    def __init__(self, data=None, request=None):
        super().__init__(data or {})
        if request:
            self['request'] = request
        self.autoescape = False

class MockFilter:
    def __init__(self, value):
        self.value = value
    
    def resolve(self, context):
        return self.value

# Mock settings
class MockSettings:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'

# Mock the django.conf.settings
import sys
from unittest.mock import MagicMock

# Create a mock django module structure
django_mock = MagicMock()
django_mock.conf.settings = MockSettings()
django_mock.apps.is_installed.return_value = False
django_mock.utils.encoding.iri_to_uri = lambda x: x
django_mock.utils.html.conditional_escape = lambda x: x
django_mock.template.TemplateSyntaxError = Exception

sys.modules['django'] = django_mock
sys.modules['django.conf'] = django_mock.conf
sys.modules['django.apps'] = django_mock.apps
sys.modules['django.utils'] = django_mock.utils
sys.modules['django.utils.encoding'] = django_mock.utils.encoding
sys.modules['django.utils.html'] = django_mock.utils.html
sys.modules['django.template'] = django_mock.template

# Now import our modified static.py
from django.templatetags.static import PrefixNode, StaticNode

def test_prefix_node_with_script_name():
    """Test PrefixNode respects SCRIPT_NAME"""
    print("Testing PrefixNode with SCRIPT_NAME...")
    
    # Test without SCRIPT_NAME
    node = PrefixNode(name="STATIC_URL")
    context = MockContext()
    result = node.render(context)
    print(f"Without SCRIPT_NAME: {result}")
    assert result == '/static/', f"Expected '/static/', got '{result}'"
    
    # Test with SCRIPT_NAME
    request = MockRequest('/myapp')
    context = MockContext(request=request)
    result = node.render(context)
    print(f"With SCRIPT_NAME '/myapp': {result}")
    assert result == '/myapp/static/', f"Expected '/myapp/static/', got '{result}'"
    
    print("PrefixNode test passed!")

def test_static_node_with_script_name():
    """Test StaticNode respects SCRIPT_NAME"""
    print("Testing StaticNode with SCRIPT_NAME...")
    
    # Test without SCRIPT_NAME
    node = StaticNode(path=MockFilter('css/style.css'))
    context = MockContext()
    result = node.url(context)
    print(f"Without SCRIPT_NAME: {result}")
    assert result == '/static/css/style.css', f"Expected '/static/css/style.css', got '{result}'"
    
    # Test with SCRIPT_NAME
    request = MockRequest('/myapp')
    context = MockContext(request=request)
    result = node.url(context)
    print(f"With SCRIPT_NAME '/myapp': {result}")
    assert result == '/myapp/static/css/style.css', f"Expected '/myapp/static/css/style.css', got '{result}'"
    
    print("StaticNode test passed!")

if __name__ == '__main__':
    test_prefix_node_with_script_name()
    test_static_node_with_script_name()
    print("All tests passed!")