import pytest
from django.conf import settings
from django.core.checks.translation import check_language_settings_consistent
from django.test import override_settings


def test_issue_reproduction():
    """Test that E004 is not raised when base language is available for sublanguage."""
    # Test case: de-at sublanguage with de base language available
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        # This should NOT raise E004 since 'de' base language is available
        # but currently it does, demonstrating the bug
        assert len(errors) == 0, f"Expected no errors but got: {errors}"