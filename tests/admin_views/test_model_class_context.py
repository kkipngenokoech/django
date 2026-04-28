import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.admin import ModelAdmin
from django.db import models


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'
        verbose_name = 'Test Model'
        verbose_name_plural = 'Test Models'


def test_issue_reproduction():
    """Test that model class is available in app_list context and _build_app_dict is public."""
    # Create admin site and register a model
    admin_site = AdminSite()
    admin_site.register(TestModel)
    
    # Create a mock request with authenticated staff user
    factory = RequestFactory()
    request = factory.get('/admin/')
    request.user = User(is_staff=True, is_active=True, is_superuser=True)
    
    # Test 1: Check that _build_app_dict method is accessible (should be public)
    # This should fail on current code since _build_app_dict is private
    assert hasattr(admin_site, 'build_app_dict'), "build_app_dict method should be public"
    
    # Test 2: Get the app list and check if model class is available
    app_list = admin_site.get_app_list(request)
    
    # Find our test app in the app list
    test_app = None
    for app in app_list:
        if app['app_label'] == 'test_app':
            test_app = app
            break
    
    assert test_app is not None, "Test app should be in app list"
    assert len(test_app['models']) > 0, "Test app should have models"
    
    # Test 3: Check that model class is available in the model dict
    # This should fail on current code since model class is not included
    test_model_dict = test_app['models'][0]
    assert 'model' in test_model_dict, "Model dict should contain 'model' key with the actual model class"
    assert test_model_dict['model'] is TestModel, "Model dict should contain reference to the actual model class"
    
    # Test 4: Verify the available_apps context includes model classes
    context = admin_site.each_context(request)
    available_apps = context['available_apps']
    
    # Find our test app in available_apps
    test_app_context = None
    for app in available_apps:
        if app['app_label'] == 'test_app':
            test_app_context = app
            break
    
    assert test_app_context is not None, "Test app should be in available_apps context"
    assert len(test_app_context['models']) > 0, "Test app should have models in context"
    
    # This should fail on current code - model class should be available in context
    test_model_context = test_app_context['models'][0]
    assert 'model' in test_model_context, "Model context should contain 'model' key with the actual model class"
    assert test_model_context['model'] is TestModel, "Model context should contain reference to the actual model class"