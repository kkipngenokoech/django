import enum
from django.db.migrations.serializer import serializer_factory
from django.utils.translation import gettext_lazy as _

def test_issue_reproduction():
    """Test that enum serialization uses name instead of value to avoid translation issues."""
    
    class Status(enum.Enum):
        GOOD = _('Good')  # This will be a translatable string
        BAD = _('Bad')
        
        def __str__(self):
            return self.name
    
    # Serialize the enum value
    serializer = serializer_factory(Status.GOOD)
    serialized_string, imports = serializer.serialize()
    
    # The current implementation generates Status('Good') which is problematic
    # because 'Good' might be translated and no longer match the enum value
    # It should generate Status.GOOD instead to reference by name
    assert 'Status.GOOD' in serialized_string, f"Expected 'Status.GOOD' in serialized output, got: {serialized_string}"
    assert 'Status(' not in serialized_string, f"Should not use Status() constructor, got: {serialized_string}"