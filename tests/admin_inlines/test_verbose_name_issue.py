import pytest
from django.contrib.admin import ModelAdmin, TabularInline
from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from .admin import site as admin_site
from .models import Holder, Inner


def test_issue_reproduction():
    """Test that inline verbose_name_plural defaults to verbose_name + 's' when only verbose_name is set."""
    
    class CustomInline(TabularInline):
        model = Inner
        verbose_name = "Custom Item"
        # verbose_name_plural is intentionally not set
    
    class HolderAdmin(ModelAdmin):
        inlines = [CustomInline]
    
    # Create a request and user for the admin
    factory = RequestFactory()
    request = factory.get('/admin/')
    request.user = User(username='test', is_superuser=True)
    
    # Create the admin instance
    holder_admin = HolderAdmin(Holder, admin_site)
    inline_instance = CustomInline(Holder, admin_site)
    
    # Get the formset for the inline
    formset_class = inline_instance.get_formset(request)
    
    # The issue: verbose_name_plural should default to verbose_name + 's'
    # but currently it uses the model's verbose_name_plural instead
    expected_plural = "Custom Items"  # verbose_name + 's'
    actual_plural = formset_class._meta.verbose_name_plural
    
    # This assertion should fail on current code because it doesn't derive
    # verbose_name_plural from the inline's verbose_name
    assert actual_plural == expected_plural, f"Expected '{expected_plural}' but got '{actual_plural}'"