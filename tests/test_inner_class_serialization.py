import django
from django.conf import settings
from django.db import models
from django.db.migrations.serializer import DeconstructableSerializer

# Configure Django settings if not already configured
if not settings.configured:
    settings.configure(
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        USE_TZ=True,
    )
    django.setup()

def test_issue_reproduction():
    """Test that inner class fields are serialized with correct qualified paths."""
    
    # Create the exact scenario from the issue
    class Outer(object):
        class Inner(models.CharField):
            pass
    
    # Create an instance of the inner class field
    field_instance = Outer.Inner(max_length=20)
    
    # Get the deconstruct info which includes the path
    attr_name, path, args, kwargs = field_instance.deconstruct()
    
    # The path should be the full qualified name including the outer class
    # Currently this will be wrong due to the bug
    expected_path = f"{__name__}.Outer.Inner"
    
    # This assertion will FAIL on the current buggy code
    # because the path will be missing 'Outer.' part
    assert path == expected_path, f"Expected path '{expected_path}' but got '{path}'"
    
    # Also test the serialization directly
    serializer = DeconstructableSerializer(field_instance)
    serialized_string, imports = serializer.serialize()
    
    # The serialized string should contain the full qualified path
    # This will also FAIL on the current code
    assert "Outer.Inner" in serialized_string, f"Serialized string '{serialized_string}' should contain 'Outer.Inner'"
    assert "Inner(max_length=20)" in serialized_string, f"Serialized string should contain field parameters"