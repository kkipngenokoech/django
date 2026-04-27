import enum
from django.utils.translation import gettext_lazy as _
from django.db.migrations.serializer import serializer_factory

def test_issue_reproduction():
    class Status(enum.Enum):
        GOOD = _('Good')
        BAD = _('Bad')
        
        def __str__(self):
            return self.name
    
    # Test serialization of enum object
    serializer = serializer_factory(Status.GOOD)
    serialized_string, imports = serializer.serialize()
    
    # The bug: current implementation serializes the value instead of the name
    # This will fail because it generates Status('Good') instead of Status.GOOD
    # When translations change, 'Good' might not exist in the enum anymore
    assert 'Status.GOOD' in serialized_string, f"Expected 'Status.GOOD' in serialized string, got: {serialized_string}"
    assert 'Status(' not in serialized_string, f"Should not use Status() constructor, got: {serialized_string}"