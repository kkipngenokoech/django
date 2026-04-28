import pytest
from django.views.debug import SafeExceptionReporterFilter


def test_issue_reproduction():
    """Test that cleanse_setting properly handles nested iterables containing sensitive data."""
    filter_instance = SafeExceptionReporterFilter()
    
    # Test case from the issue - nested structures with sensitive keys
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
    
    # Keys in list of dictionaries should be cleansed
    assert result["something"][0]["foo"] == "value"
    assert result["something"][0]["secret"] == "********************"
    assert result["something"][1]["secret"] == "********************"
    assert result["something"][1]["token"] == "********************"
    assert result["something"][2]["token"] == "********************"
    
    # Keys in nested list of lists of dictionaries should be cleansed
    assert result["else"][0][0]["foo"] == "value"
    assert result["else"][0][0]["secret"] == "********************"
    assert result["else"][0][0]["token"] == "********************"
    assert result["else"][0][1]["secret"] == "********************"
    assert result["else"][0][1]["token"] == "********************"
    assert result["else"][1][0]["secret"] == "********************"
    assert result["else"][1][0]["token"] == "********************"
    assert result["else"][1][1]["secret"] == "********************"
    assert result["else"][1][1]["token"] == "********************"
    
    # Test with tuples as well
    tuple_setting = (
        {"secret": "value", "foo": "value"},
        ({"token": "value", "bar": "value"},)
    )
    
    tuple_result = filter_instance.cleanse_setting("TUPLE_SETTING", tuple_setting)
    
    # Tuples containing sensitive dictionaries should be cleansed
    assert tuple_result[0]["secret"] == "********************"
    assert tuple_result[0]["foo"] == "value"
    assert tuple_result[1][0]["token"] == "********************"
    assert tuple_result[1][0]["bar"] == "value"