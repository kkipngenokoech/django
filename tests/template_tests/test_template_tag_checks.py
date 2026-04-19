import pytest
from django.conf import settings
from django.core.checks.templates import check_for_template_tags_with_the_same_name
from django.test import override_settings


def test_issue_reproduction():
    """Test that template tags configured in TEMPLATES['OPTIONS']['libraries'] don't cause false duplicate errors."""
    # Configure a template tag library both in TEMPLATES and let it be auto-discovered
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
        
        # This should not produce any errors, but currently produces E003 duplicate error
        # because 'admin_list' appears both in custom libraries and auto-discovered modules
        assert len(errors) == 0, f"Expected no errors, but got: {[error.msg for error in errors]}"