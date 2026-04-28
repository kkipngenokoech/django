import pytest
from django.conf import settings
from django.core.checks import Error
from django.core.checks.translation import check_language_settings_consistent, E004
from django.test import override_settings


def test_issue_reproduction():
    """Test that translation.E004 is not raised when base language is available for sublanguage."""
    
    # Test case 1: sublanguage 'de-at' with base language 'de' available
    # This should NOT raise E004 error according to Django docs
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        # This assertion will FAIL on current buggy code because it raises E004
        # but should PASS after fix since 'de' base language is available
        assert errors == [], f"Expected no errors for sublanguage with available base language, got: {errors}"
    
    # Test case 2: sublanguage 'es-mx' with base language 'es' available
    with override_settings(
        LANGUAGE_CODE='es-mx', 
        LANGUAGES=[('es', 'Spanish'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert errors == [], f"Expected no errors for sublanguage with available base language, got: {errors}"
    
    # Test case 3: sublanguage without base language should still raise E004
    with override_settings(
        LANGUAGE_CODE='fr-ca',
        LANGUAGES=[('de', 'German'), ('en', 'English')]  # no 'fr' base language
    ):
        errors = check_language_settings_consistent(None)
        assert errors == [E004], f"Expected E004 error for sublanguage without base language, got: {errors}"
    
    # Test case 4: exact match should work (no error)
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de-at', 'Austrian German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert errors == [], f"Expected no errors for exact language match, got: {errors}"
    
    # Test case 5: base language exact match should work
    with override_settings(
        LANGUAGE_CODE='de',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert errors == [], f"Expected no errors for base language match, got: {errors}"