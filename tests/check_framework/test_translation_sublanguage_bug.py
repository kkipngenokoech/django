import pytest
from django.conf import settings
from django.core.checks.translation import check_language_settings_consistent, E004
from django.test import override_settings


def test_issue_reproduction():
    """Test that translation.E004 is not raised when base language is available for sublanguage."""
    
    # Test case 1: de-at sublanguage with de base language available
    # This should NOT raise E004 according to Django docs
    with override_settings(
        LANGUAGE_CODE='de-at',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        # This assertion will FAIL on buggy code because it incorrectly raises E004
        assert errors == [], f"Expected no errors for de-at with de available, but got: {errors}"
    
    # Test case 2: es-ar sublanguage that exists in LANGUAGES (should work)
    with override_settings(
        LANGUAGE_CODE='es-ar', 
        LANGUAGES=[('es-ar', 'Argentinian Spanish'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert errors == [], f"Expected no errors for exact match es-ar, but got: {errors}"
    
    # Test case 3: fr-ca sublanguage with fr base language available
    with override_settings(
        LANGUAGE_CODE='fr-ca',
        LANGUAGES=[('fr', 'French'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        # This assertion will FAIL on buggy code
        assert errors == [], f"Expected no errors for fr-ca with fr available, but got: {errors}"
    
    # Test case 4: Invalid sublanguage with no base language (should raise E004)
    with override_settings(
        LANGUAGE_CODE='xx-yy',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert len(errors) == 1
        assert errors[0] == E004
    
    # Test case 5: Exact language match (should work)
    with override_settings(
        LANGUAGE_CODE='de',
        LANGUAGES=[('de', 'German'), ('en', 'English')]
    ):
        errors = check_language_settings_consistent(None)
        assert errors == []