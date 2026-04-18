import pytest
from django.conf import settings
from django.core.checks.templates import check_for_template_tags_with_the_same_name
from django.test import override_settings


def test_issue_reproduction():
    """Test that template tags specified in TEMPLATES libraries don't cause false duplicate errors."""
    # Configure TEMPLATES with a library that would also be auto-discovered
    templates_config = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {
                'libraries': {
                    'admin_list': 'django.contrib.admin.templatetags.admin_list',
                }
            }
        }
    ]
    
    with override_settings(TEMPLATES=templates_config):
        errors = check_for_template_tags_with_the_same_name(None)
        
        # This should not produce any errors, but currently does due to the bug
        # The bug causes 'admin_list' to be detected as duplicate because it's both
        # in the custom libraries and discovered by get_template_tag_modules()
        assert len(errors) == 0, f"Expected no errors but got: {[e.msg for e in errors]}"