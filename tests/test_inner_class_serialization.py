import types
from django.db.migrations.serializer import DeconstructableSerializer

def test_issue_reproduction():
    # Create a mock inner class that mimics the structure described in the issue
    # This simulates Outer.Inner where Inner is a subclass of models.CharField
    
    # Create a mock deconstruct method that returns the problematic path
    class MockInnerField:
        def deconstruct(self):
            # This simulates what would happen with test1.models.Outer.Inner
            return ('field', 'test1.models.Outer.Inner', [], {'max_length': 20})
    
    mock_field = MockInnerField()
    serializer = DeconstructableSerializer(mock_field)
    
    # Serialize the field
    result, imports = serializer.serialize()
    
    # The bug: current code produces 'test1.models.Inner(max_length=20)'
    # Expected: should produce 'test1.models.Outer.Inner(max_length=20)'
    
    # This assertion will FAIL on the current buggy code because it loses 'Outer'
    assert 'test1.models.Outer.Inner(max_length=20)' in result, f"Expected 'test1.models.Outer.Inner' but got: {result}"
    
    # Also check that the import is correct
    assert 'import test1.models' in imports, f"Expected 'import test1.models' but got: {imports}"
    
    # Test the _serialize_path method directly to show the core issue
    name, path_imports = DeconstructableSerializer._serialize_path('test1.models.Outer.Inner')
    
    # This will FAIL because current code returns 'test1.models.Inner' instead of 'test1.models.Outer.Inner'
    assert name == 'test1.models.Outer.Inner', f"Expected 'test1.models.Outer.Inner' but got: {name}"