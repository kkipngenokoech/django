import pytest
from django.db import models
from django.test import TestCase
from django.core.exceptions import NotSupportedError
from django.utils import timezone


class ProductMetaDataType(models.Model):
    label = models.CharField(max_length=255, unique=True, blank=False, null=False)
    filterable = models.BooleanField(default=False, verbose_name="filterable")
    
    class Meta:
        app_label = "test_app"
        verbose_name = "product meta data type"
        verbose_name_plural = "product meta data types"
    
    def __str__(self):
        return self.label


class ProductMetaData(models.Model):
    id = models.BigAutoField(primary_key=True)
    value = models.TextField(null=False, blank=False)
    date_created = models.DateTimeField(null=True, default=timezone.now)
    metadata_type = models.ForeignKey(
        ProductMetaDataType, null=False, blank=False, on_delete=models.CASCADE
    )
    
    class Meta:
        app_label = "test_app"
        verbose_name = "product meta data"
        verbose_name_plural = "product meta datas"


def test_issue_reproduction():
    """Test that filtering with a model instance having a 'filterable' field works correctly."""
    # Create a ProductMetaDataType instance with filterable=False
    metadata_type = ProductMetaDataType(label="test_type", filterable=False)
    metadata_type.save()
    
    # Create a ProductMetaData instance
    metadata = ProductMetaData(value="Dark Vador", metadata_type=metadata_type)
    metadata.save()
    
    # This should work without raising NotSupportedError
    # The issue is that Django's query building logic checks for 'filterable' attribute
    # on the RHS (metadata_type) and gets confused by the user-defined 'filterable' field
    try:
        result = ProductMetaData.objects.filter(value="Dark Vador", metadata_type=metadata_type)
        # Force evaluation of the queryset
        list(result)
        # If we get here without exception, the bug is fixed
        assert True
    except NotSupportedError as e:
        # This is the bug - it should not raise NotSupportedError
        pytest.fail(f"NotSupportedError raised when filtering with model instance having 'filterable' field: {e}")
    
    # Also test the queryset evaluation returns the correct result
    result = ProductMetaData.objects.filter(value="Dark Vador", metadata_type=metadata_type)
    result_list = list(result)
    assert len(result_list) == 1
    assert result_list[0].value == "Dark Vador"
    assert result_list[0].metadata_type == metadata_type
