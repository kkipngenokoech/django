from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import re_path
from django.urls.resolvers import RegexPattern


class OptionalParamsTests(TestCase):
    """Test that optional URL parameters work correctly with view functions."""

    def test_optional_param_not_provided(self):
        """Test that when optional parameter is not provided, view function works correctly."""
        
        def modules(request, format='html'):
            return HttpResponse(f'format: {format}')
        
        # Create URL pattern with optional named group
        pattern = RegexPattern(r'^module/(?P<format>(html|json|xml))?/?$', is_endpoint=True)
        
        # Test the case where optional parameter is not provided
        match_result = pattern.match('/module/')
        
        self.assertIsNotNone(match_result)
        remaining_path, args, kwargs = match_result
        
        # The kwargs should not contain None values for optional parameters
        self.assertEqual(kwargs, {})
        
        # The view function should work correctly with default parameter
        request = RequestFactory().get('/module/')
        response = modules(request, **kwargs)
        self.assertEqual(response.content.decode(), 'format: html')
    
    def test_optional_param_provided(self):
        """Test that when optional parameter is provided, it gets passed correctly."""
        
        def modules(request, format='html'):
            return HttpResponse(f'format: {format}')
        
        # Create URL pattern with optional named group
        pattern = RegexPattern(r'^module/(?P<format>(html|json|xml))?/?$', is_endpoint=True)
        
        # Test the case where optional parameter is provided
        match_result = pattern.match('/module/json/')
        
        self.assertIsNotNone(match_result)
        remaining_path, args, kwargs = match_result
        
        # The kwargs should contain the provided value
        self.assertEqual(kwargs, {'format': 'json'})
        
        # The view function should work correctly with provided parameter
        request = RequestFactory().get('/module/json/')
        response = modules(request, **kwargs)
        self.assertEqual(response.content.decode(), 'format: json')
    
    def test_multiple_optional_params(self):
        """Test multiple optional parameters work correctly."""
        
        def view_func(request, param1='default1', param2='default2'):
            return HttpResponse(f'param1: {param1}, param2: {param2}')
        
        # Pattern with multiple optional groups
        pattern = RegexPattern(r'^test/(?P<param1>\w+)?/?(?P<param2>\w+)?/?$', is_endpoint=True)
        
        # Test no parameters provided
        match_result = pattern.match('/test/')
        self.assertIsNotNone(match_result)
        _, _, kwargs = match_result
        self.assertEqual(kwargs, {})
        
        request = RequestFactory().get('/test/')
        response = view_func(request, **kwargs)
        self.assertEqual(response.content.decode(), 'param1: default1, param2: default2')
        
        # Test one parameter provided
        match_result = pattern.match('/test/value1/')
        self.assertIsNotNone(match_result)
        _, _, kwargs = match_result
        self.assertEqual(kwargs, {'param1': 'value1'})
        
        request = RequestFactory().get('/test/value1/')
        response = view_func(request, **kwargs)
        self.assertEqual(response.content.decode(), 'param1: value1, param2: default2')
        
        # Test both parameters provided
        match_result = pattern.match('/test/value1/value2/')
        self.assertIsNotNone(match_result)
        _, _, kwargs = match_result
        self.assertEqual(kwargs, {'param1': 'value1', 'param2': 'value2'})
        
        request = RequestFactory().get('/test/value1/value2/')
        response = view_func(request, **kwargs)
        self.assertEqual(response.content.decode(), 'param1: value1, param2: value2')
