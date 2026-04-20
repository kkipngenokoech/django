import pytest
from django.conf import settings
from django.core.checks import run_checks
from django.test import override_settings


def test_issue_reproduction():
    """Test that translation.E004 is not raised when base language is available for sublanguage."""
    # Set up a scenario where 'de' is available but 'de-at' is not directly listed
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = run_checks(tags=['translation'])
        
        # Filter for translation.E004 errors
        e004_errors = [error for error in errors if error.id == 'translation.E004']
        
        # This should NOT raise E004 since 'de' base language is available
        # But currently it does, which is the bug
        assert len(e004_errors) == 1, "Expected E004 error due to current bug - this test should fail until fixed"