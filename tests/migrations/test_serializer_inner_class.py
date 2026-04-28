import pytest
from django.db import models
from django.db.migrations.serializer import DeconstructableSerializer


def test_issue_reproduction():
    """Test that inner class fields are serialized with correct full path."""
    
    # Create an inner class field similar to the issue description
    class Outer(object):
        class Inner(models.CharField):
            pass
    
    # Create an instance of the inner class field
    field_instance = Outer.Inner(max_length=20)
    
    # Get the deconstruct information
    name, path, args, kwargs = field_instance.deconstruct()
    
    # Serialize the path using the current implementation
    serialized_name, imports = DeconstructableSerializer._serialize_path(path)
    
    # The bug: path should be 'test_issue_reproduction.Outer.Inner' but 
    # the current implementation only returns 'test_issue_reproduction.Inner'
    # This assertion will FAIL on the buggy code because it loses the 'Outer' part
    expected_path = f"{__name__}.Outer.Inner"
    assert expected_path in serialized_name, f"Expected '{expected_path}' in serialized name '{serialized_name}', but got incorrect path"