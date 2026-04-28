import pytest
from django.db import models
from django.db import NotSupportedError
from django.test import TestCase
from django.apps import apps
from django.conf import settings

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        USE_TZ=True,
    )
    import django
    django.setup()

from django.db import connection

class ProductMetaDataType(models.Model):
    label = models.CharField(max_length=255, unique=True, blank=False, null=False)
    filterable = models.BooleanField(default=False)
    
    class Meta:
        app_label = "test_app"
        
    def __str__(self):
        return self.label

class ProductMetaData(models.Model):
    value = models.TextField(null=False, blank=False)
    metadata_type = models.ForeignKey(
        ProductMetaDataType, null=False, blank=False, on_delete=models.CASCADE
    )
    
    class Meta:
        app_label = "test_app"

def test_issue_reproduction():
    """Test that filtering with a model instance that has a 'filterable' field works correctly."""
    # Create tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(ProductMetaDataType)
        schema_editor.create_model(ProductMetaData)
    
    try:
        # Create test data
        metadata_type = ProductMetaDataType.objects.create(
            label="test_type",
            filterable=True
        )
        
        ProductMetaData.objects.create(
            value="Dark Vador",
            metadata_type=metadata_type
        )
        
        # This should work but currently raises NotSupportedError
        # because Django confuses the model's 'filterable' field with its internal filterable attribute
        result = ProductMetaData.objects.filter(
            value="Dark Vador", 
            metadata_type=metadata_type
        )
        
        # This should return the created object
        assert result.count() == 1
        assert result.first().value == "Dark Vador"
        assert result.first().metadata_type == metadata_type
        
    finally:
        # Clean up tables
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(ProductMetaData)
            schema_editor.delete_model(ProductMetaDataType)