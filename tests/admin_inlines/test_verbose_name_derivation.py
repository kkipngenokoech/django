import pytest
from django.contrib import admin
from django.db import models
from django.test import TestCase


class ParentModel(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'


class ChildModel(models.Model):
    parent = models.ForeignKey(ParentModel, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'test_app'
        verbose_name = 'Child Item'
        verbose_name_plural = 'Child Items'


class ChildInline(admin.TabularInline):
    model = ChildModel
    verbose_name = 'Custom Child'
    # verbose_name_plural is intentionally not set - should be auto-derived


class ParentAdmin(admin.ModelAdmin):
    inlines = [ChildInline]


def test_issue_reproduction():
    """Test that inline verbose_name_plural is derived from verbose_name when not explicitly set."""
    inline = ChildInline(ParentModel, admin.site)
    
    # The inline has verbose_name set
    assert inline.verbose_name == 'Custom Child'
    
    # verbose_name_plural should be auto-derived from verbose_name (adding 's')
    # This should be 'Custom Childs' but currently falls back to model's verbose_name_plural
    expected_plural = 'Custom Childs'  # Simple pluralization of verbose_name
    actual_plural = getattr(inline, 'verbose_name_plural', None)
    
    # This assertion will fail because Django doesn't auto-derive verbose_name_plural
    # from inline's verbose_name - it uses the model's verbose_name_plural instead
    assert actual_plural == expected_plural, f"Expected '{expected_plural}' but got '{actual_plural}'"