import pytest
from django.db import models
from django.test import TestCase
from django.db import connection
from django.test.utils import override_settings


class Main(models.Model):
    main_field_1 = models.CharField(blank=True, max_length=45)
    main_field_2 = models.CharField(blank=True, max_length=45)
    main_field_3 = models.CharField(blank=True, max_length=45)
    
    class Meta:
        app_label = 'test_app'


class Secondary(models.Model):
    main = models.OneToOneField(Main, primary_key=True, related_name='secondary', on_delete=models.CASCADE)
    secondary_field_1 = models.CharField(blank=True, max_length=45)
    secondary_field_2 = models.CharField(blank=True, max_length=45)
    secondary_field_3 = models.CharField(blank=True, max_length=45)
    
    class Meta:
        app_label = 'test_app'


def test_issue_reproduction():
    """Test that only() works correctly with select_related() on reverse OneToOneField."""
    # Create the queryset that should only select specific fields
    queryset = Main.objects.select_related('secondary').only('main_field_1', 'secondary__secondary_field_1')
    
    # Get the SQL query
    sql, params = queryset.query.sql_with_params()
    
    # The bug is that secondary_field_2 and secondary_field_3 should NOT be in the query
    # but they are included due to the regression
    assert 'secondary_field_2' not in sql, f"secondary_field_2 should not be in query: {sql}"
    assert 'secondary_field_3' not in sql, f"secondary_field_3 should not be in query: {sql}"
    
    # These fields should be present
    assert 'main_field_1' in sql, f"main_field_1 should be in query: {sql}"
    assert 'secondary_field_1' in sql, f"secondary_field_1 should be in query: {sql}"