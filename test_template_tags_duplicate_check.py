import pytest
from django.conf import settings
from django.core.checks.templates import check_for_template_tags_with_the_same_name
from django.test import override_settings


def test_issue_reproduction():
    """Test that template tag libraries configured in TEMPLATES don't cause false duplicates."""
    # Mock a scenario where a library is both in TEMPLATES config and discovered by get_template_tag_modules
    templates_config = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {
                'libraries': {
                    'my_tags': 'someapp.templatetags.my_tags',
                }
            }
        }
    ]
    
    with override_settings(TEMPLATES=templates_config):
        # Mock get_template_tag_modules to return the same library that's in TEMPLATES config
        import django.core.checks.templates
        original_get_template_tag_modules = django.core.checks.templates.get_template_tag_modules
        
        def mock_get_template_tag_modules():
            return [('my_tags', 'someapp.templatetags.my_tags')]
        
        django.core.checks.templates.get_template_tag_modules = mock_get_template_tag_modules
        
        try:
            errors = check_for_template_tags_with_the_same_name(None)
            # This should not produce any errors since it's the same library, not duplicates
            # But the current buggy code will report it as a duplicate
            assert len(errors) == 0, f"Expected no errors but got: {errors}"
        finally:
            django.core.checks.templates.get_template_tag_modules = original_get_template_tag_modules