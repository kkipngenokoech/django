import pytest
from django.db import models
from django.db.migrations.serializer import DeconstructableSerializer


def test_issue_reproduction():
    """Test that inner class fields are serialized with correct full path."""
    
    # Create an inner class field similar to the issue description
    class Outer:
        class Inner(models.CharField):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
    
    # Create an instance of the inner class field
    field_instance = Outer.Inner(max_length=20)
    
    # Get the deconstruct info
    name, path, args, kwargs = field_instance.deconstruct()
    
    # Serialize the path using the current implementation
    serialized_name, imports = DeconstructableSerializer._serialize_path(path)
    
    # The bug: current implementation will produce 'test_issue_reproduction.Inner'
    # instead of the correct 'test_issue_reproduction.Outer.Inner'
    # This assertion will FAIL on the buggy code because it doesn't handle inner classes
    assert 'Outer.Inner' in serialized_name, f"Expected 'Outer.Inner' in serialized name, got: {serialized_name}"