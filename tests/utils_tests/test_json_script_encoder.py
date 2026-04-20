import json
from django.utils.html import json_script
from django.test import SimpleTestCase


class CustomJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        if isinstance(obj, str) and obj == "custom":
            return '"CUSTOM_ENCODED"'
        return super().encode(obj)


class TestJsonScriptCustomEncoder(SimpleTestCase):
    def test_issue_reproduction(self):
        # This should fail because json_script doesn't accept cls parameter yet
        result = json_script({"key": "custom"}, element_id="test", cls=CustomJSONEncoder)
        # If the custom encoder was used, "custom" would be encoded as "CUSTOM_ENCODED"
        self.assertIn('"CUSTOM_ENCODED"', result)