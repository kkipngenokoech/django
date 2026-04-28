import pytest
from django.views.debug import SafeExceptionReporterFilter
from django.conf import settings

def test_issue_reproduction():
    """Test that cleanse_setting recursively cleanses nested iterables containing sensitive data."""
    filter_instance = SafeExceptionReporterFilter()
    
    # Test data with nested sensitive information in lists and tuples
    test_setting = {
        "foo": "value",
        "secret": "sensitive_value",  # This should be cleansed
        "token": "sensitive_token",   # This should be cleansed
        "something": [
            {"foo": "value"},
            {"secret": "nested_secret"},  # This should be cleansed but currently isn't
            {"token": "nested_token"},    # This should be cleansed but currently isn't
        ],
        "else": [
            [
                {"foo": "value"},
                {"secret": "deep_secret"},  # This should be cleansed but currently isn't
                {"token": "deep_token"},    # This should be cleansed but currently isn't
            ],
            [
                {"foo": "value"},
                {"secret": "another_secret"},  # This should be cleansed but currently isn't
                {"token": "another_token"},    # This should be cleansed but currently isn't
            ],
        ]
    }
    
    result = filter_instance.cleanse_setting("MY_SETTING", test_setting)
    
    # Top-level sensitive keys should be cleansed
    assert result["secret"] == filter_instance.cleansed_substitute
    assert result["token"] == filter_instance.cleansed_substitute
    
    # Nested sensitive keys in lists should also be cleansed (this will fail on current code)
    assert result["something"][1]["secret"] == filter_instance.cleansed_substitute
    assert result["something"][2]["token"] == filter_instance.cleansed_substitute
    
    # Deeply nested sensitive keys should also be cleansed (this will fail on current code)
    assert result["else"][0][1]["secret"] == filter_instance.cleansed_substitute
    assert result["else"][0][2]["token"] == filter_instance.cleansed_substitute
    assert result["else"][1][1]["secret"] == filter_instance.cleansed_substitute
    assert result["else"][1][2]["token"] == filter_instance.cleansed_substitute