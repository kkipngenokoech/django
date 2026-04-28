import pytest
from django.conf import settings
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.urls import path, register_converter
from django.urls.converters import StringConverter
from django.urls.resolvers import get_resolver
from django.core.exceptions import ImproperlyConfigured


class Http404Converter(StringConverter):
    """A converter that raises Http404 in to_python method."""
    
    def to_python(self, value):
        if value == 'trigger404':
            raise Http404("Object not found")
        return value


def dummy_view(request, param):
    return None


@override_settings(DEBUG=True)
def test_issue_reproduction():
    """Test that Http404 raised in path converter's to_python method shows technical response when DEBUG=True."""
    # Register our custom converter
    register_converter(Http404Converter, 'http404conv')
    
    # Create URL pattern using the converter
    urlpatterns = [
        path('test/<http404conv:param>/', dummy_view, name='test_view'),
    ]
    
    # Create a resolver with our URL patterns
    from django.urls.resolvers import URLResolver, RegexPattern
    resolver = URLResolver(RegexPattern(r'^/'), urlpatterns)
    
    # Try to resolve a path that will trigger Http404 in the converter
    try:
        match = resolver.resolve('/test/trigger404/')
        # If we get here, the bug is fixed - Http404 was properly handled
        assert False, "Expected Http404 to be raised but got a match instead"
    except Http404:
        # This is what should happen - Http404 should bubble up for proper handling
        # But currently this fails because Http404 gets converted to a generic server error
        pass
    except Exception as e:
        # This is what currently happens - some other exception type
        # The test should fail here to demonstrate the bug
        pytest.fail(f"Expected Http404 but got {type(e).__name__}: {e}")