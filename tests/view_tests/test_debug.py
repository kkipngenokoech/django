import pytest
from django.views.debug import SafeExceptionReporterFilter
from django.test import override_settings


def test_issue_reproduction():
    """Test that cleanse_setting recursively cleanses sensitive data in nested iterables."""
    filter_instance = SafeExceptionReporterFilter()
    
    # Test case from the issue - nested lists and dicts with sensitive keys
    test_setting = {
        "foo": "value",
        "secret": "value",
        "token": "value",
        "something": [
            {"foo": "value"},
            {"secret": "value"},
            {"token": "value"},
        ],
        "else": [
            [
                {"foo": "value"},
                {"secret": "value"},
                {"token": "value"},
            ],
            [
                {"foo": "value"},
                {"secret": "value"},
                {"token": "value"},
            ],
        ]
    }
    
    result = filter_instance.cleanse_setting("MY_SETTING", test_setting)
    
    # Top-level sensitive keys should be cleansed
    assert result["secret"] == "********************"
    assert result["token"] == "********************"
    assert result["foo"] == "value"  # non-sensitive should remain
    
    # Sensitive keys in list of dicts should be cleansed
    assert result["something"][0]["foo"] == "value"
    assert result["something"][0]["secret"] == "********************"
    assert result["something"][1]["secret"] == "********************"
    assert result["something"][2]["token"] == "********************"
    
    # Sensitive keys in nested lists of lists of dicts should be cleansed
    assert result["else"][0][0]["foo"] == "value"
    assert result["else"][0][0]["secret"] == "********************"
    assert result["else"][0][1]["secret"] == "********************"
    assert result["else"][0][2]["token"] == "********************"
    assert result["else"][1][0]["foo"] == "value"
    assert result["else"][1][0]["secret"] == "********************"
    assert result["else"][1][1]["secret"] == "********************"
    assert result["else"][1][2]["token"] == "********************"
    
    # Test with tuples as well
    tuple_setting = (
        {"api_key": "secret_value", "name": "test"},
        [{"password": "secret", "user": "admin"}]
    )
    
    tuple_result = filter_instance.cleanse_setting("TUPLE_SETTING", tuple_setting)
    
    # Should preserve tuple type and cleanse nested sensitive data
    assert isinstance(tuple_result, tuple)
    assert tuple_result[0]["api_key"] == "********************"
    assert tuple_result[0]["name"] == "test"
    assert tuple_result[1][0]["password"] == "********************"
    assert tuple_result[1][0]["user"] == "admin"