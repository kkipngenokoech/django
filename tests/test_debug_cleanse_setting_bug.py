import pytest
from django.views.debug import SafeExceptionReporterFilter


def test_issue_reproduction():
    """Test that cleanse_setting fails to cleanse sensitive values in nested iterables."""
    filter_instance = SafeExceptionReporterFilter()
    
    # Test data with sensitive keys in nested lists and tuples
    test_setting = {
        "foo": "value",
        "secret": "value",  # This should be cleansed
        "token": "value",   # This should be cleansed
        "something": [
            {"foo": "value"},
            {"secret": "value"},  # This should be cleansed but isn't
            {"token": "value"},   # This should be cleansed but isn't
        ],
        "else": [
            [
                {"foo": "value"},
                {"secret": "value"},  # This should be cleansed but isn't
                {"token": "value"},   # This should be cleansed but isn't
            ],
            (
                {"foo": "value"},
                {"secret": "value"},  # This should be cleansed but isn't
                {"token": "value"},   # This should be cleansed but isn't
            ),
        ]
    }
    
    result = filter_instance.cleanse_setting("MY_SETTING", test_setting)
    
    # Top-level sensitive keys should be cleansed
    assert result["secret"] == filter_instance.cleansed_substitute
    assert result["token"] == filter_instance.cleansed_substitute
    
    # But nested sensitive keys in lists should also be cleansed (this will fail)
    # The bug is that these are NOT cleansed in the current implementation
    nested_list_item = result["something"][1]  # {"secret": "value"}
    assert nested_list_item["secret"] == filter_instance.cleansed_substitute, "Sensitive key in list not cleansed"
    
    nested_nested_list_item = result["else"][0][1]  # {"secret": "value"}
    assert nested_nested_list_item["secret"] == filter_instance.cleansed_substitute, "Sensitive key in nested list not cleansed"