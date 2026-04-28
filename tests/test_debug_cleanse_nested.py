import pytest
from django.views.debug import SafeExceptionReporterFilter


def test_issue_reproduction():
    """Test that sensitive keys in nested iterables are properly cleansed."""
    filter_instance = SafeExceptionReporterFilter()
    
    # Test data with nested sensitive information in lists and tuples
    test_setting = {
        "foo": "value",
        "secret": "value",  # This should be cleansed
        "token": "value",   # This should be cleansed
        "something": [
            {"foo": "value"},
            {"secret": "value"},  # This should be cleansed but currently isn't
            {"token": "value"},   # This should be cleansed but currently isn't
        ],
        "else": [
            [
                {"foo": "value"},
                {"secret": "value"},  # This should be cleansed but currently isn't
                {"token": "value"},   # This should be cleansed but currently isn't
            ],
            (
                {"foo": "value"},
                {"secret": "value"},  # This should be cleansed but currently isn't
                {"token": "value"},   # This should be cleansed but currently isn't
            ),
        ]
    }
    
    result = filter_instance.cleanse_setting("MY_SETTING", test_setting)
    
    # Top-level sensitive keys should be cleansed
    assert result["secret"] == "********************"
    assert result["token"] == "********************"
    
    # Nested sensitive keys in lists should also be cleansed (this will fail)
    assert result["something"][1]["secret"] == "********************"
    assert result["something"][2]["token"] == "********************"
    
    # Deeply nested sensitive keys should also be cleansed (this will fail)
    assert result["else"][0][1]["secret"] == "********************"
    assert result["else"][0][2]["token"] == "********************"
    assert result["else"][1][1]["secret"] == "********************"
    assert result["else"][1][2]["token"] == "********************"