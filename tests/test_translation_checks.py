import pytest
from django.conf import settings
from django.core.checks.translation import check_language_settings_consistent
from django.test import override_settings


def test_issue_reproduction():
    """Test that translation.E004 is not raised when base language is available for sublanguage."""
    # Test case: de-at should not raise E004 when 'de' is in LANGUAGES
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        # This should pass (no errors) but currently fails with E004
        assert len(errors) == 0, f"Expected no errors but got: {errors}"
    
    # Verify the current behavior still works for exact matches
    with override_settings(
        LANGUAGE_CODE='de',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert len(errors) == 0
    
    # Verify error is still raised when neither sublanguage nor base language exists
    with override_settings(
        LANGUAGE_CODE='fr-ca',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert len(errors) == 1
        assert errors[0].id == 'translation.E004'