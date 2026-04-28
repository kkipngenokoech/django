import pytest
from django.db import models
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.core.management.color import no_style


class CustomModel(models.Model):
    name = models.CharField(max_length=16)
    
    class Meta:
        app_label = 'test_app'


class ProxyCustomModel(CustomModel):
    class Meta:
        proxy = True
        app_label = 'test_app'


class AnotherModel(models.Model):
    custom = models.ForeignKey(
        ProxyCustomModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that select_related() and only() work together on proxy models."""
    # Create the tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(CustomModel)
        schema_editor.create_model(AnotherModel)
    
    try:
        # Create test data
        custom_obj = CustomModel.objects.create(name="test")
        another_obj = AnotherModel.objects.create(custom_id=custom_obj.id)
        
        # This should not crash but currently does
        result = list(AnotherModel.objects.select_related("custom").only("custom__name").all())
        
        # If we get here, the bug is fixed
        assert len(result) == 1
        assert result[0].custom.name == "test"
        
    finally:
        # Clean up tables
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(AnotherModel)
            schema_editor.delete_model(CustomModel)