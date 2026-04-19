import pytest
from django.conf import settings
from django.core.checks import run_checks
from django.test import override_settings


def test_issue_reproduction():
    """Test that translation.E004 is not raised when base language is available for sublanguage."""
    # Set up a scenario where we have a base language 'de' but not the sublanguage 'de-at'
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de', 'German'), ('en', 'English')],
        USE_I18N=True
    ):
        errors = run_checks(tags=['translation'])
        
        # Filter for translation.E004 errors
        e004_errors = [error for error in errors if error.id == 'translation.E004']
        
        # This should NOT raise E004 since 'de' base language is available for 'de-at'
        # But currently it does raise E004, which is the bug
        assert len(e004_errors) == 0, f"Expected no E004 errors, but got: {e004_errors}"