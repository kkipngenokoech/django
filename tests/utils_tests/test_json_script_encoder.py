import json
from django.utils.html import json_script
from django.test import SimpleTestCase


class CustomJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, str) and obj == "custom":
            return '"CUSTOM_ENCODED"'
        return super().encode(obj)


def test_issue_reproduction():
    # Test that json_script accepts a custom encoder parameter
    # This should fail because the current implementation doesn't support the encoder parameter
    result = json_script({"key": "custom"}, encoder=CustomJSONEncoder)
    
    # The custom encoder should transform "custom" to "CUSTOM_ENCODED"
    expected = '<script type="application/json">{"key": "CUSTOM_ENCODED"}</script>'
    assert expected in result