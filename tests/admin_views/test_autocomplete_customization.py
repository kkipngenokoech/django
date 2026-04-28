import pytest
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.admin import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.db import models
from django.http import JsonResponse
from django.test import RequestFactory
from unittest.mock import Mock


class TestModel(models.Model):
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=200, default="test notes")
    
    def __str__(self):
        return self.name
    
    class Meta:
        app_label = 'test'


class CustomAutocompleteJsonView(AutocompleteJsonView):
    """Custom view that should be able to add extra fields easily."""
    
    def get_result_data(self, obj, to_field_name):
        """This method should exist to allow easy customization."""
        return {
            'id': str(getattr(obj, to_field_name)),
            'text': str(obj),
            'notes': obj.notes  # Extra field we want to add
        }


def test_issue_reproduction():
    """Test that AutocompleteJsonView lacks get_result_data method for easy customization."""
    # Create a mock request and setup
    factory = RequestFactory()
    request = factory.get('/autocomplete/', {
        'term': 'test',
        'app_label': 'test',
        'model_name': 'testmodel',
        'field_name': 'test_field'
    })
    request.user = Mock()
    
    # Create mock objects
    mock_obj = Mock()
    mock_obj.pk = 1
    mock_obj.notes = "test notes"
    mock_obj.__str__ = Mock(return_value="Test Object")
    
    # Setup the view
    view = CustomAutocompleteJsonView()
    view.admin_site = Mock()
    
    # The test should fail because get_result_data method doesn't exist
    # in the base AutocompleteJsonView class
    with pytest.raises(AttributeError, match="get_result_data"):
        # Try to call the method that should exist for easy customization
        result = view.get_result_data(mock_obj, 'pk')
        # This should return a dict with id, text, and notes
        assert 'notes' in result