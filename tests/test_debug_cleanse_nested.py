import pytest
from django.views.debug import SafeExceptionReporterFilter


def test_issue_reproduction():
    """Test that cleanse_setting recursively cleanses nested iterables containing sensitive data."""
    filter_instance = SafeExceptionReporterFilter()
    
    # Test data with nested sensitive information in lists and tuples
    test_setting = {
        "foo": "value",
        "secret": "value",  # Should be cleansed at top level
        "token": "value",   # Should be cleansed at top level
        "something": [
            {"foo": "value"},
            {"secret": "value"},  # Should be cleansed but currently isn't
            {"token": "value"},   # Should be cleansed but currently isn't
        ],
        "else": [
            [
                {"foo": "value"},
                {"secret": "value"},  # Should be cleansed but currently isn't
                {"token": "value"},   # Should be cleansed but currently isn't
            ],
            [
                {"foo": "value"},
                {"secret": "value"},  # Should be cleansed but currently isn't
                {"token": "value"},   # Should be cleansed but currently isn't
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