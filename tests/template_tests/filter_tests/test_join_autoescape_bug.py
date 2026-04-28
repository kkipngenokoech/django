import pytest
from django.template import Context, Template
from django.test import SimpleTestCase


def test_issue_reproduction():
    """Test that join filter respects autoescape off for the joining string."""
    # Test case where autoescape is off - joining string should not be escaped
    template_str = '{% autoescape off %}{{ some_list|join:some_var }}{% endautoescape %}'
    template = Template(template_str)
    
    some_list = ["<p>Hello World!</p>", "beta & me", "<script>Hi!</script>"]
    some_var = "<br/>"
    
    context = Context({"some_list": some_list, "some_var": some_var})
    output = template.render(context)
    
    # Expected: joining string should NOT be escaped when autoescape is off
    expected = some_var.join(some_list)  # "<p>Hello World!</p><br/>beta & me<br/><script>Hi!</script>"
    
    # This assertion will FAIL on current buggy code because some_var gets escaped to "&lt;br/&gt;"
    assert output == expected