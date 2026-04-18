import json
from django.utils.html import json_script
from django.test import SimpleTestCase


class CustomJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, str) and obj == "custom":
            return '"CUSTOM_ENCODED"'
        return super().encode(obj)


def test_issue_reproduction():
    """Test that json_script accepts a custom encoder parameter."""
    # This should work with a custom encoder but currently fails
    # because json_script doesn't accept an encoder parameter
    try:
        result = json_script({"test": "custom"}, encoder=CustomJSONEncoder)
        # If we get here, the encoder parameter was accepted
        assert "CUSTOM_ENCODED" in result
    except TypeError as e:
        # This is what currently happens - the function doesn't accept encoder parameter
        assert "unexpected keyword argument" in str(e)
        raise AssertionError("json_script should accept encoder parameter but doesn't")