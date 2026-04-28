import types
from django.db.migrations.serializer import FunctionTypeSerializer

def test_issue_reproduction():
    # Create a nested class structure similar to the issue
    class Profile:
        class Capability:
            @classmethod
            def default(cls):
                return ['BASIC']
    
    # Get the class method from the nested class
    method = Profile.Capability.default
    
    # Serialize it using FunctionTypeSerializer
    serializer = FunctionTypeSerializer(method)
    serialized_value, imports = serializer.serialize()
    
    # The bug: it should include the full path with parent class
    # Current buggy behavior generates: __main__.Capability.default
    # Expected correct behavior: __main__.Profile.Capability.default
    assert 'Profile.Capability.default' in serialized_value, f"Expected 'Profile.Capability.default' in serialized value, got: {serialized_value}"